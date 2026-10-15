"""Video analyzers.

LIVE:   ISO-BMFF box walk (brands, duration, tracks, encoder tag, C2PA uuid box presence).
LIVE:   Frame sampling with OpenCV (bundled FFmpeg) -> open image-watermark decoder on sampled frames.
LIVE:   C2PA validation of the MP4 via the shared C2PA analyzer (incl. BMFF hash).
MANUAL: audio-track extraction (ffmpeg binary), Video Seal detector (torch), visible-logo template matching,
        SynthID-Video (Google surfaces only).
"""
from __future__ import annotations

import struct

from .base import Analyzer, Context, Signal
from . import imwm_an

CONTAINER_BOXES = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"udta", b"edts", b"dinf", b"meta", b"ilst"}


def _walk(data: bytes, start: int, end: int, depth: int, acc: dict, path: str = ""):
    pos = start
    while pos + 8 <= end:
        size, btype = struct.unpack(">I4s", data[pos:pos + 8])
        hdr = 8
        if size == 1:
            size = struct.unpack(">Q", data[pos + 8:pos + 16])[0]
            hdr = 16
        elif size == 0:
            size = end - pos
        if size < hdr or pos + size > end:
            break
        name = btype.decode("latin1", "replace")
        p = f"{path}/{name}"
        acc.setdefault("boxes", []).append(p) if depth < 3 else None
        body_start = pos + hdr
        if btype == b"ftyp":
            acc["major_brand"] = data[body_start:body_start + 4].decode("latin1", "replace")
            acc["compatible_brands"] = [data[i:i + 4].decode("latin1", "replace") for i in range(body_start + 8, pos + size, 4)]
        elif btype == b"mvhd":
            v = data[body_start]
            if v == 1:
                ts, dur = struct.unpack(">IQ", data[body_start + 20:body_start + 32])
            else:
                ts, dur = struct.unpack(">II", data[body_start + 12:body_start + 20])
            acc["duration_s"] = round(dur / ts, 2) if ts else None
        elif btype == b"tkhd":
            v = data[body_start]
            off = body_start + (88 if v == 1 else 76)
            w, h = struct.unpack(">II", data[off:off + 8])
            acc.setdefault("tracks", []).append({"width": w >> 16, "height": h >> 16})
        elif btype == b"hdlr":
            acc.setdefault("handlers", []).append(data[body_start + 8:body_start + 12].decode("latin1", "replace"))
        elif btype == b"uuid":
            acc.setdefault("uuid_boxes", []).append(data[body_start:body_start + 16].hex())
        elif btype == b"\xa9too":
            acc["encoder_tag"] = data[body_start + 16:pos + size].decode("utf-8", "replace")[:100]
        if btype in CONTAINER_BOXES and depth < 6:
            inner = body_start + (4 if btype == b"meta" else 0)
            _walk(data, inner, pos + size, depth + 1, acc, p)
        pos += size


def bmff_facts(path: str) -> dict:
    data = open(path, "rb").read()
    acc: dict = {}
    _walk(data, 0, len(data), 0, acc)
    acc["c2pa_uuid_box"] = any(u.lower() == "d8fec3d61b0e483c92975828877ec481" for u in acc.get("uuid_boxes", []))
    acc["boxes"] = acc.get("boxes", [])[:40]
    return acc


class VideoAnalyzer(Analyzer):
    name = "video"
    modalities = ("video",)

    def run(self, ctx: Context) -> list[Signal]:
        out = []
        facts = {}
        try:
            facts = bmff_facts(ctx.path)
        except Exception as e:
            facts = {"error": str(e)[:200]}
        hints = []
        if facts.get("encoder_tag"):
            hints.append(f"encoder tag '{facts['encoder_tag']}'" + (" (FFmpeg/Lavf re-mux — metadata may have been dropped)" if "Lavf" in facts["encoder_tag"] else ""))
        out.append(Signal(kind="container", name="MP4 / ISO-BMFF structure", status="info", evidence_grade="none",
                          summary=("C2PA uuid box present. " if facts.get("c2pa_uuid_box") else "No C2PA uuid box. ") + "; ".join(hints),
                          data=facts, method="pure-python box walker"))

        # Frame sampling
        try:
            import cv2
            cap = cv2.VideoCapture(ctx.path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            idxs = sorted(set(int(i) for i in [0, n * 0.2, n * 0.4, n * 0.6, n * 0.8, max(0, n - 1)])) if n else [0]
            per_frame, frames_read = [], 0
            for i in idxs:
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ok, frame = cap.read()
                if not ok:
                    continue
                frames_read += 1
                res = imwm_an.decode_image_bgr(frame)
                status, grade, _ = imwm_an.interpret(res)
                per_frame.append({"frame": i, "dwtdct": status, "sdxl_bit_acc": res.get("sdxl", {}).get("bit_accuracy"),
                                  "mean_luma": round(float(frame.mean()), 1)})
            cap.release()
            detected = [f for f in per_frame if f["dwtdct"] == "detected"]
            out.append(Signal(kind="open_watermark", name="Per-frame open watermark scan (DWT-DCT)",
                              status="detected" if detected else ("absent" if frames_read else "error"),
                              evidence_grade="moderate" if len(detected) >= 2 else ("weak" if detected else "none"),
                              summary=f"{frames_read} frames sampled at {fps:.1f} fps, {w}x{h}; DWT-DCT pattern on {len(detected)} frame(s).",
                              data={"fps": fps, "frame_count": n, "width": w, "height": h, "frames": per_frame},
                              method="OpenCV frame sampling + dwtDct port"))
        except Exception as e:
            out.append(Signal(kind="open_watermark", name="Per-frame open watermark scan (DWT-DCT)", status="error", summary=str(e)[:200]))

        out.append(Signal(kind="open_watermark", name="Video Seal detector (Meta)", status="not_installed", evidence_grade="none",
                          summary="Open multi-bit video watermark with temporal propagation; extractor needs torch.",
                          manual_integration="pip install torch; git+https://github.com/facebookresearch/videoseal; run extractor on sampled clips"))
        out.append(Signal(kind="forensics", name="Visible watermark / logo template matcher", status="not_configured", evidence_grade="none",
                          summary="Template-match known marks (Sora animated logo, Veo corner mark, Kling/Pika free-tier logos) in corner regions.",
                          manual_integration="Collect 20–50 logo crops per generator into data/templates/<tool>/ and enable analyzers/logo_an.py (cv2.matchTemplate, multi-scale)"))
        out.append(Signal(kind="connector", name="Audio track analysis", status="not_configured", evidence_grade="none",
                          summary="OpenCV cannot demux audio; extract with ffmpeg and run the audio analyzers (AudioSeal / SynthID connectors).",
                          manual_integration="apt-get install ffmpeg; `ffmpeg -i in.mp4 -vn -ac 1 -ar 16000 out.wav`; call pipeline.analyze_file on the result"))
        out.append(Signal(kind="vendor_watermark", name="SynthID-Video / Sora fingerprint", status="not_configured", evidence_grade="none",
                          summary="Google SynthID Detector (public) and OpenAI's internal reverse-video index cover Veo/Sora content server-side.",
                          manual_integration="Vendor connectors in analyzers/vendor_an.py"))
        return out
