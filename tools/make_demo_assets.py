"""Generate demo fixtures that exercise every live path of the pipeline.

All signatures use the TEST certificate from tools/dev_cert.py (issuer "Provenably Demo Signer");
these files are for exercising the product only and must never be presented as real provenance.

Outputs (demo_assets/):
  ai_generated_signed.jpg          valid C2PA, digitalSourceType=trainedAlgorithmicMedia
  camera_capture_signed.jpg        valid C2PA, digitalSourceType=digitalCapture, EXIF camera tags
  ai_edited_composite_signed.jpg   valid C2PA, compositeWithTrainedAlgorithmicMedia + ingredient (parent = camera file)
  ai_generated_tampered.jpg        pixels edited after signing (manifest spliced back) -> hash mismatch
  ai_generated_stripped.jpg        same pixels, all metadata removed -> "no provenance signal"
  iptc_ai_tagged_no_c2pa.jpg       only XMP IPTC DigitalSourceType (unsigned)
  a1111_parameters.png             PNG with Automatic1111-style 'parameters' text chunk
  sdxl_watermarked.png             DWT-DCT 48-bit SDXL pattern embedded (pristine)
  sdxl_watermarked_q75.jpg         same, after JPEG q75 — chroma subsampling destroys the U-channel mark (shows fragility)
  plain_photo_like.jpg             nothing at all
  text_clean.txt / text_hidden_chars.txt / text_greenlist_marked.txt
  speech_like_signed.wav           synthetic speech-like WAV + C2PA
  speech_like_plain.wav
  clip_signed.mp4                  OpenCV-written clip + C2PA (BMFF hash)
  clip_plain.mp4
"""
from __future__ import annotations

import json
import os
import pathlib
import struct
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import config  # noqa: E402
from app.analyzers import c2pa_an, dwtdct, imwm_an, text_an  # noqa: E402

OUT = config.DEMO_DIR
OUT.mkdir(exist_ok=True)
TMP = OUT / "_tmp"
TMP.mkdir(exist_ok=True)
rng = np.random.default_rng(42)

CLAIM_GEN = "Provenably Demo Generator/0.1"


def manifest(title: str, source_type: str, actions: list[dict], extra_assertions: list[dict] | None = None) -> dict:
    return {
        "claim_generator_info": [{"name": "Provenably Demo Generator", "version": "0.1"}],
        "title": title,
        "assertions": [
            {"label": "c2pa.actions", "data": {"actions": actions}},
            *(extra_assertions or []),
        ],
    }


def ai_actions(agent: str, source_type: str):
    return [{"action": "c2pa.created", "digitalSourceType": f"http://cv.iptc.org/newscodes/digitalsourcetype/{source_type}",
             "softwareAgent": {"name": agent, "version": "1.0"}}]


# ---------------------------------------------------------------- images ----------------------------------------
def render_synthetic(size=1024, seed=1) -> Image.Image:
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size].astype(np.float32) / size
    base = np.stack([
        0.45 + 0.25 * np.sin(6 * x + 2 * y) + 0.08 * r.standard_normal((size, size)),
        0.50 + 0.20 * np.cos(4 * y - 3 * x) + 0.08 * r.standard_normal((size, size)),
        0.55 + 0.22 * np.sin(5 * (x + y)) + 0.08 * r.standard_normal((size, size)),
    ], axis=-1)
    img = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(1.2))
    d = ImageDraw.Draw(img)
    for i in range(14):
        cx, cy, rad = r.integers(80, size - 80), r.integers(80, size - 80), int(r.integers(30, 140))
        col = tuple(int(c) for c in r.integers(40, 230, 3))
        d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=col, outline=(20, 20, 20))
    return img


def render_photo_like(size=1024, seed=5) -> Image.Image:
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size].astype(np.float32) / size
    sky = np.stack([0.55 - 0.3 * y, 0.70 - 0.25 * y, 0.95 - 0.15 * y], axis=-1)
    ground = np.stack([0.30 + 0.1 * r.random((size, size)), 0.45 + 0.1 * r.random((size, size)), 0.20 + 0.05 * r.random((size, size))], axis=-1)
    img = np.where((y > 0.62)[..., None], ground, sky)
    img = img + 0.03 * r.standard_normal((size, size, 3))  # sensor-like noise
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    for i in range(60):
        bx = int(r.integers(0, size)); bh = int(r.integers(40, 260)); bw = int(r.integers(20, 90))
        d.rectangle((bx, int(0.62 * size) - bh, bx + bw, int(0.62 * size)), fill=tuple(int(c) for c in r.integers(60, 120, 3)))
    return im


def render_midtone(size=1024, seed=13) -> np.ndarray:
    """Low-chroma mid-tone texture: the DWT-DCT scheme (U channel, QIM on LL coefficients) is only reliable on such
    content even for the reference library; saturated or clipped colours break it. Returns BGR uint8."""
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size].astype(np.float32) / size
    L = 0.5 + 0.12 * np.sin(5 * x + 2 * y) + 0.1 * np.cos(7 * y - 3 * x) + 0.05 * r.standard_normal((size, size))
    a = 0.03 * np.sin(3 * x)
    b = 0.03 * np.cos(4 * y)
    img = np.stack([L + a, L, L + b], axis=-1)
    im = Image.fromarray((np.clip(img, 0.15, 0.85) * 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(0.8))
    d = ImageDraw.Draw(im)
    for i in range(10):
        cx, cy, rad = r.integers(80, size - 80), r.integers(80, size - 80), int(r.integers(30, 120))
        g = int(r.integers(70, 190))
        col = (g + int(r.integers(-25, 25)), g, g + int(r.integers(-25, 25)))
        d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=col, outline=(60, 60, 60))
    return np.array(im)[:, :, ::-1].copy()


def exif_camera_bytes() -> bytes:
    from PIL import Image as _I
    ex = _I.Exif()
    ex[0x010F] = "Provenably Demo Camera Co."
    ex[0x0110] = "DC-1000"
    ex[0x0131] = "DC-1000 firmware 2.1"
    ex[0x9003] = "2026:10:12 09:14:33"
    ex[0x829A] = (1, 250)
    ex[0x829D] = (28, 10)
    ex[0x8827] = 100
    ex[0x920A] = (350, 10)
    return ex.tobytes()


def xmp_iptc_ai(source_type: str, tool: str) -> bytes:
    xmp = f"""<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about="" xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<Iptc4xmpExt:DigitalSourceType>http://cv.iptc.org/newscodes/digitalsourcetype/{source_type}</Iptc4xmpExt:DigitalSourceType>
<xmp:CreatorTool>{tool}</xmp:CreatorTool>
<dc:description><rdf:Alt><rdf:li xml:lang="x-default">Demo image tagged via IPTC only (no signature)</rdf:li></rdf:Alt></dc:description>
</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>"""
    return xmp.encode("utf-8")


def strip_to_pixels(src: pathlib.Path, dst: pathlib.Path, quality=92):
    im = Image.open(src).convert("RGB")
    clean = Image.new("RGB", im.size)
    clean.putdata(list(im.getdata()))
    clean.save(dst, "JPEG", quality=quality)


def splice_app11(signed: pathlib.Path, modified_pixels: pathlib.Path, dst: pathlib.Path):
    """Copy APP11 (C2PA) segments from a signed JPEG into a re-encoded JPEG => hard-binding mismatch."""
    def segments(data: bytes):
        out = []
        pos = 2
        while pos + 4 <= len(data):
            if data[pos] != 0xFF:
                break
            marker = data[pos + 1]
            if marker == 0xDA:
                out.append((marker, pos, len(data)))
                break
            ln = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            out.append((marker, pos, pos + 2 + ln))
            pos += 2 + ln
        return out
    s = signed.read_bytes()
    m = modified_pixels.read_bytes()
    app11 = b"".join(s[a:b] for mk, a, b in segments(s) if mk == 0xEB)
    segs = segments(m)
    insert_at = segs[0][2] if segs and segs[0][0] in (0xE0, 0xE1) else 2
    dst.write_bytes(m[:insert_at] + app11 + m[insert_at:])


def make_images():
    # 1. AI generated + signed
    ai = render_synthetic()
    src = TMP / "ai_src.jpg"
    ai.save(src, "JPEG", quality=92)
    c2pa_an.sign_file(str(src), str(OUT / "ai_generated_signed.jpg"),
                      manifest("Demo: AI-generated image", "trainedAlgorithmicMedia", ai_actions("Provenably Demo Diffusion", "trainedAlgorithmicMedia"),
                               [{"label": "org.provenably.demo", "data": {"note": "test fixture", "prompt_hash": "sha256:demo"}}]),
                      "image/jpeg")
    # 2. camera capture + EXIF + signed
    cam = render_photo_like()
    src2 = TMP / "cam_src.jpg"
    cam.save(src2, "JPEG", quality=94, exif=exif_camera_bytes())
    c2pa_an.sign_file(str(src2), str(OUT / "camera_capture_signed.jpg"),
                      manifest("Demo: camera capture", "digitalCapture",
                               [{"action": "c2pa.created", "digitalSourceType": "http://cv.iptc.org/newscodes/digitalsourcetype/digitalCapture",
                                 "softwareAgent": {"name": "Provenably Demo Camera Co. DC-1000", "version": "2.1"}}]),
                      "image/jpeg")
    # 3. composite: camera file edited with generative fill; ingredient = the signed camera file
    comp = cam.copy()
    comp.paste(ai.resize((360, 360)).filter(ImageFilter.GaussianBlur(0.6)), (600, 120))
    src3 = TMP / "comp_src.jpg"
    comp.save(src3, "JPEG", quality=92)
    ing_iid = "xmp:iid:provenably-demo-parent-0001"
    ingredient = ({"title": "camera_capture_signed.jpg", "relationship": "parentOf", "instance_id": ing_iid}, "image/jpeg", str(OUT / "camera_capture_signed.jpg"))
    c2pa_an.sign_file(str(src3), str(OUT / "ai_edited_composite_signed.jpg"),
                      manifest("Demo: AI-edited composite", "compositeWithTrainedAlgorithmicMedia",
                               [{"action": "c2pa.opened", "parameters": {"ingredientIds": [ing_iid]}},
                                {"action": "c2pa.edited", "digitalSourceType": "http://cv.iptc.org/newscodes/digitalsourcetype/compositeWithTrainedAlgorithmicMedia",
                                 "softwareAgent": {"name": "Provenably Demo Editor (generative fill)", "version": "1.0"}}]),
                      "image/jpeg", ingredient=ingredient)
    # 4. tampered: edit pixels after signing, keep manifest
    t = Image.open(OUT / "ai_generated_signed.jpg").convert("RGB")
    d = ImageDraw.Draw(t)
    d.rectangle((40, 40, 420, 140), fill=(250, 250, 250))
    d.text((56, 70), "EDITED AFTER SIGNING", fill=(180, 20, 20))
    tp = TMP / "tampered_pixels.jpg"
    t.save(tp, "JPEG", quality=92)
    splice_app11(OUT / "ai_generated_signed.jpg", tp, OUT / "ai_generated_tampered.jpg")
    # 5. stripped
    strip_to_pixels(OUT / "ai_generated_signed.jpg", OUT / "ai_generated_stripped.jpg")
    # 6. IPTC only
    ai2 = render_synthetic(seed=9)
    ai2.save(OUT / "iptc_ai_tagged_no_c2pa.jpg", "JPEG", quality=90, xmp=xmp_iptc_ai("trainedAlgorithmicMedia", "Provenably Demo Diffusion 1.0"))
    # 7. A1111 PNG text
    from PIL.PngImagePlugin import PngInfo
    info = PngInfo()
    info.add_text("parameters", "a watercolor lighthouse at dusk, dramatic sky\nNegative prompt: blurry\nSteps: 30, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 1234567, Size: 768x768, Model: sd_xl_base_1.0")
    render_synthetic(768, seed=3).save(OUT / "a1111_parameters.png", "PNG", pnginfo=info)
    # 8. SDXL watermark (pristine PNG + JPEG q75)
    import cv2
    base = render_midtone(1024, seed=13)  # BGR
    wm = dwtdct.embed_bits(base, imwm_an.SDXL_BITS)
    assert np.mean(np.array(dwtdct.decode_bits(wm, 48)[0]) == np.array(imwm_an.SDXL_BITS)) > 0.99
    cv2.imwrite(str(OUT / "sdxl_watermarked.png"), wm)
    cv2.imwrite(str(OUT / "sdxl_watermarked_q75.jpg"), wm, [cv2.IMWRITE_JPEG_QUALITY, 75])
    # 9. plain
    render_photo_like(seed=21).save(OUT / "plain_photo_like.jpg", "JPEG", quality=88)


# ---------------------------------------------------------------- text ------------------------------------------
CLEAN = ("The committee met on Tuesday to review the quarterly figures. Revenue grew by eight percent, driven mostly by the "
         "subscription business, while hardware margins stayed flat. Two members asked for a clearer breakdown of regional "
         "performance before the next board meeting, and the chair agreed to circulate a revised deck by Friday. "
         "Nobody raised the staffing question, although it is likely to come up again once the hiring freeze is reviewed in "
         "November. The minutes will be published on the intranet after legal has checked the section on the pending audit.\n")


def make_text():
    (OUT / "text_clean.txt").write_text(CLEAN * 2, encoding="utf-8")
    hidden = CLEAN.replace(" the ", " the\u200b ", 3).replace("Revenue", "Re\u200cvenue").replace("board", "bo\u00adard").replace(" - ", " \u2014 ")
    hidden = hidden.replace("Friday.", "Friday.\u202f").replace("November", "N\u043evember")  # Cyrillic o homoglyph
    (OUT / "text_hidden_chars.txt").write_text(hidden + "\u200e\n", encoding="utf-8")
    toks = text_an.greenlist_generate(key="demo-key", n=320, gamma=0.5, strength=0.92, seed=7)
    (OUT / "text_greenlist_marked.txt").write_text(" ".join(toks) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- audio -----------------------------------------
def speech_like(seconds=3.0, sr=16000, seed=3) -> np.ndarray:
    r = np.random.default_rng(seed)
    t = np.arange(int(seconds * sr)) / sr
    f0 = 120 + 25 * np.sin(2 * np.pi * 0.7 * t) + 8 * r.standard_normal(t.size).cumsum() / np.sqrt(t.size)
    phase = 2 * np.pi * np.cumsum(f0) / sr
    sig = sum((1 / k) * np.sin(k * phase) for k in range(1, 12))
    # formant-ish envelope + syllable rhythm
    env = (0.55 + 0.45 * np.sin(2 * np.pi * 3.5 * t)) ** 2 * (t > 0.1) * (t < seconds - 0.1)
    sig = sig * env
    sig += 0.01 * r.standard_normal(sig.size)
    sig /= np.abs(sig).max()
    return (sig * 0.7 * 32767).astype(np.int16)


def write_wav(path: pathlib.Path, data: np.ndarray, sr=16000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(data.tobytes())


def make_audio():
    plain = TMP / "speech_plain.wav"
    write_wav(plain, speech_like())
    write_wav(OUT / "speech_like_plain.wav", speech_like(seed=8))
    try:
        c2pa_an.sign_file(str(plain), str(OUT / "speech_like_signed.wav"),
                          manifest("Demo: synthetic speech", "trainedAlgorithmicMedia", ai_actions("Provenably Demo TTS", "trainedAlgorithmicMedia")),
                          "audio/wav")
    except Exception as e:
        print("WAV signing failed:", e)


# ---------------------------------------------------------------- video -----------------------------------------
def make_video():
    import cv2
    plain = TMP / "clip_plain.mp4"
    w, h, fps, n = 640, 360, 24, 48
    vw = cv2.VideoWriter(str(plain), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    base = np.array(render_synthetic(360, seed=17))[:, :, ::-1]
    for i in range(n):
        frame = np.zeros((h, w, 3), np.uint8)
        frame[:, :, :] = (30, 30, 30)
        off = int(i * 4)
        frame[:, off:off + 360] = base[:, : max(0, min(360, w - off))]
        cv2.putText(frame, f"demo frame {i}", (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 240, 240), 1, cv2.LINE_AA)
        vw.write(frame)
    vw.release()
    (OUT / "clip_plain.mp4").write_bytes(plain.read_bytes())
    try:
        c2pa_an.sign_file(str(plain), str(OUT / "clip_signed.mp4"),
                          manifest("Demo: AI-generated clip", "trainedAlgorithmicMedia", ai_actions("Provenably Demo Video Model", "trainedAlgorithmicMedia")),
                          "video/mp4")
    except Exception as e:
        print("MP4 signing failed:", e)


if __name__ == "__main__":
    make_images(); print("images ok")
    make_text(); print("text ok")
    make_audio(); print("audio ok")
    make_video(); print("video ok")
    import shutil
    shutil.rmtree(TMP, ignore_errors=True)
    for f in sorted(OUT.iterdir()):
        if f.is_file():
            print(f"{f.name:36s} {f.stat().st_size:>9,d} B")
