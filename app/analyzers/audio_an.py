"""Audio analyzers.

LIVE:   WAV container facts + spectral context (bandwidth, flatness, silence, clipping) — context only.
LIVE:   MP3 ID3v2 tag summary (encoder strings are attribution hints).
LIVE:   C2PA in WAV/MP3 runs through the shared C2PA analyzer.
MANUAL: AudioSeal (Meta) detector — auto-enables when `torch` + `audioseal` are importable.
MANUAL: SynthID-Audio (Google / OpenAI / ElevenLabs) — vendor surfaces only.
"""
from __future__ import annotations

import struct
import wave

import numpy as np

from .base import Analyzer, Context, Signal


def _wav_facts(path: str) -> dict:
    with wave.open(path, "rb") as w:
        n, sr, ch, sw = w.getnframes(), w.getframerate(), w.getnchannels(), w.getsampwidth()
        frames = w.readframes(min(n, sr * 60))
    dtype = {1: np.uint8, 2: np.int16, 4: np.int32}.get(sw)
    facts = {"sample_rate": sr, "channels": ch, "bit_depth": sw * 8, "duration_s": round(n / sr, 2) if sr else None}
    if dtype is None or not frames:
        return facts
    x = np.frombuffer(frames, dtype=dtype).astype(np.float64)
    if sw == 1:
        x = x - 128
    x = x.reshape(-1, ch).mean(axis=1) if ch > 1 else x
    peak = float(np.abs(x).max()) or 1.0
    x = x / (2 ** (sw * 8 - 1))
    facts["peak_dbfs"] = round(20 * np.log10(peak / 2 ** (sw * 8 - 1) + 1e-12), 1)
    facts["clipping_ratio"] = round(float(np.mean(np.abs(x) > 0.985)), 5)
    facts["silence_ratio"] = round(float(np.mean(np.abs(x) < 1e-3)), 3)
    # spectrum on up to 2^18 samples
    seg = x[: 2 ** 18]
    if seg.size > 2048:
        win = np.hanning(seg.size)
        spec = np.abs(np.fft.rfft(seg * win)) ** 2
        freqs = np.fft.rfftfreq(seg.size, 1 / sr)
        cum = np.cumsum(spec) / (spec.sum() + 1e-12)
        facts["bandwidth_99pct_hz"] = int(freqs[np.searchsorted(cum, 0.99)])
        facts["bandwidth_999pct_hz"] = int(freqs[np.searchsorted(cum, 0.999)])
        gm = np.exp(np.mean(np.log(spec + 1e-12)))
        facts["spectral_flatness"] = round(float(gm / (spec.mean() + 1e-12)), 4)
    return facts


def _id3_summary(path: str) -> dict:
    with open(path, "rb") as f:
        head = f.read(10)
        if head[:3] != b"ID3":
            return {}
        ver = f"2.{head[3]}.{head[4]}"
        size = ((head[6] & 0x7F) << 21) | ((head[7] & 0x7F) << 14) | ((head[8] & 0x7F) << 7) | (head[9] & 0x7F)
        body = f.read(size)
    frames, pos = {}, 0
    while pos + 10 <= len(body):
        fid = body[pos:pos + 4]
        if not fid.strip(b"\x00"):
            break
        if head[3] == 4:
            flen = ((body[pos + 4] & 0x7F) << 21) | ((body[pos + 5] & 0x7F) << 14) | ((body[pos + 6] & 0x7F) << 7) | (body[pos + 7] & 0x7F)
        else:
            flen = struct.unpack(">I", body[pos + 4:pos + 8])[0]
        payload = body[pos + 10:pos + 10 + flen]
        name = fid.decode("latin1")
        if name.startswith("T") and payload:
            enc = payload[0]
            try:
                txt = payload[1:].decode({0: "latin1", 1: "utf-16", 2: "utf-16-be", 3: "utf-8"}.get(enc, "latin1"), "replace").strip("\x00")
            except Exception:
                txt = ""
            frames[name] = txt[:200]
        else:
            frames[name] = f"<{flen} bytes>"
        pos += 10 + flen
    return {"id3_version": ver, "frames": frames}


def _load_audio_16k(path: str):
    """Load audio as a mono float tensor shaped (1, samples) at 16 kHz.

    Prefers soundfile (bundles libsndfile; no FFmpeg/torchcodec needed). Falls back
    to torchaudio.load for formats soundfile cannot open.
    """
    import torch
    try:
        import soundfile as sf
        data, sr = sf.read(path, always_2d=True)
        mono = torch.from_numpy(np.ascontiguousarray(data.mean(axis=1), dtype=np.float32))
        if sr != 16000:
            import torchaudio  # type: ignore
            mono = torchaudio.functional.resample(mono, sr, 16000)
        return mono.unsqueeze(0)
    except Exception:
        import torchaudio  # type: ignore
        wav, sr = torchaudio.load(path)
        return torchaudio.functional.resample(wav.mean(0, keepdim=True), sr, 16000)


class AudioAnalyzer(Analyzer):
    name = "audio"
    modalities = ("audio",)

    def run(self, ctx: Context) -> list[Signal]:
        out = []
        facts, hints = {}, []
        try:
            if ctx.mime in ("audio/wav", "audio/x-wav", "audio/wave") or ctx.filename.lower().endswith(".wav"):
                facts = _wav_facts(ctx.path)
                bw = facts.get("bandwidth_99pct_hz")
                sr = facts.get("sample_rate")
                if bw and sr and bw < 0.42 * sr:
                    hints.append(f"energy stops near {bw} Hz although the file is {sr} Hz — up-sampled from a narrower pipeline (16/22/24 kHz TTS codecs are common, but so is phone audio)")
                if facts.get("spectral_flatness", 0) > 0.5:
                    hints.append("very flat spectrum (noise-like)")
            elif ctx.filename.lower().endswith(".mp3") or ctx.mime == "audio/mpeg":
                facts = _id3_summary(ctx.path)
                enc = (facts.get("frames") or {}).get("TSSE") or (facts.get("frames") or {}).get("TENC")
                if enc:
                    hints.append(f"encoder tag: {enc}")
            summary = ("Context only — not evidence of AI. " + "; ".join(hints)) if hints else "Context only — nothing notable."
            out.append(Signal(kind="forensics", name="Audio container & spectral context", status="info", evidence_grade="none",
                              summary=summary, data=facts, method="wave/ID3 parsing + numpy FFT"))
        except Exception as e:
            out.append(Signal(kind="forensics", name="Audio container & spectral context", status="error", summary=str(e)[:200]))

        # AudioSeal: auto-enable if installed
        try:
            import torch  # noqa: F401
            from audioseal import AudioSeal  # type: ignore
            wav = _load_audio_16k(ctx.path)
            det = AudioSeal.load_detector("audioseal_detector_16bits")
            result, message = det.detect_watermark(wav.unsqueeze(0), sample_rate=16000)
            prob = float(result)
            out.append(Signal(kind="open_watermark", name="AudioSeal detector (Meta)", status="detected" if prob > 0.5 else "absent",
                              evidence_grade="moderate" if prob > 0.9 else ("weak" if prob > 0.5 else "none"),
                              summary=f"AudioSeal probability {prob:.2f}", data={"probability": prob, "message_bits": str(message)},
                              method="facebookresearch/audioseal"))
        except Exception as e:
            out.append(Signal(kind="open_watermark", name="AudioSeal detector (Meta)", status="not_installed", evidence_grade="none",
                              summary="Per-sample localisation of Meta's open audio watermark. Enables automatically once torch + audioseal are installed.",
                              manual_integration="pip install torch torchaudio audioseal  (CPU is fine; ~1x realtime)"))
        out.append(Signal(kind="vendor_watermark", name="SynthID-Audio (Google / OpenAI / ElevenLabs)", status="not_configured",
                          evidence_grade="none", summary="Server-side only: Google SynthID Detector (public since 7 Oct 2026), OpenAI Verify API (audio since 31 Jul 2026).",
                          manual_integration="Configure OPENAI_VERIFY_* / GOOGLE_SYNTHID_* env vars; see analyzers/vendor_an.py"))
        out.append(Signal(kind="passive", name="Anti-spoofing / voice-clone classifier", status="not_installed", evidence_grade="none",
                          summary="ASVspoof-style models; high false positives on codec-compressed phone audio.",
                          manual_integration="e.g. AASIST / RawNet2 checkpoints behind a GPU worker; calibrate on your channel conditions"))
        return out
