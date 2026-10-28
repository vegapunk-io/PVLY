"""Container metadata forensics: EXIF / XMP / IPTC DigitalSourceType / PNG text chunks / segment map.

Why it matters: Meta's "AI info" label is triggered by the IPTC DigitalSourceType AI values and C2PA actions;
generator-specific tags (A1111 'parameters', ComfyUI 'prompt', Firefly/DALL·E CreatorTool…) are strong
*attribution* clues; and the segment map tells you whether a file has been stripped/re-encoded.
"""
from __future__ import annotations

import io
import json
import re
import struct

from PIL import Image, ExifTags

from .base import Analyzer, Context, Signal

AI_DST_VALUES = {
    "trainedAlgorithmicMedia": ("ai_generated", "moderate"),
    "compositeWithTrainedAlgorithmicMedia": ("ai_assisted", "moderate"),
    "trainedAlgorithmicData": ("ai_generated", "moderate"),
    "algorithmicMedia": ("algorithmic", "weak"),
    "digitalCapture": ("captured", "weak"),
    "computationalCapture": ("captured", "weak"),
    "digitalCreation": ("human_created", "weak"),
}

GENERATOR_HINTS = [
    (r"dall[\s·-]?e|openai|chatgpt", "OpenAI (DALL·E / ChatGPT images)"),
    (r"firefly|adobe", "Adobe (Firefly / Photoshop)"),
    (r"midjourney", "Midjourney"),
    (r"stable[\s_-]?diffusion|sdxl|comfyui|automatic1111|a1111|invokeai|fooocus|forge", "Stable Diffusion ecosystem"),
    (r"novelai", "NovelAI"),
    (r"gemini|imagen|google", "Google (Gemini / Imagen)"),
    (r"designer|copilot|bing image|microsoft", "Microsoft (Designer / Copilot)"),
    (r"canva", "Canva"),
    (r"leonardo", "Leonardo.ai"),
    (r"ideogram", "Ideogram"),
    (r"flux|black forest", "FLUX (Black Forest Labs)"),
    (r"recraft", "Recraft"),
    (r"meta ai|imagine with meta|emu", "Meta AI"),
    (r"lavc|lavf|ffmpeg", "re-encoded with FFmpeg"),
    (r"pillow|pil\b", "re-saved with Python Pillow"),
    (r"photoshop|lightroom", "Adobe desktop apps"),
    (r"gimp", "GIMP"),
    (r"snapseed|instagram|whatsapp", "mobile/social app re-encode"),
]

JPEG_SEGMENT_NAMES = {0xE0: "APP0 (JFIF)", 0xE1: "APP1 (EXIF/XMP)", 0xE2: "APP2 (ICC/MPF)", 0xEB: "APP11 (JUMBF/C2PA)",
                      0xED: "APP13 (Photoshop IRB/IPTC-IIM)", 0xEE: "APP14 (Adobe)", 0xDB: "DQT", 0xC0: "SOF0",
                      0xC2: "SOF2 (progressive)", 0xC4: "DHT", 0xFE: "COM"}


def _jpeg_segment_map(data: bytes) -> list[str]:
    segs, pos, n = [], 2, len(data)
    while pos + 4 <= n:
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker == 0xDA:
            segs.append("SOS (image data)")
            break
        if 0xD0 <= marker <= 0xD7 or marker in (0xD8, 0x01):
            pos += 2
            continue
        seglen = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        name = JPEG_SEGMENT_NAMES.get(marker, f"0x{marker:02X}")
        if marker == 0xE1:
            payload = data[pos + 4:pos + 4 + 12]
            name = "APP1 (EXIF)" if payload.startswith(b"Exif") else ("APP1 (XMP)" if payload.startswith(b"http") else name)
        segs.append(name)
        pos += 2 + seglen
    return segs


def _extract_xmp(data: bytes) -> str | None:
    start = data.find(b"<x:xmpmeta")
    if start == -1:
        start = data.find(b"<?xpacket begin")
    if start == -1:
        return None
    end = data.find(b"</x:xmpmeta>", start)
    if end == -1:
        return None
    return data[start:end + len(b"</x:xmpmeta>")].decode("utf-8", "replace")


def _xmp_fields(xmp: str) -> dict:
    out = {}

    def grab(names):
        for n in names:
            m = re.search(rf'{n}\s*=\s*"([^"]*)"', xmp) or re.search(rf"<{n}[^>]*>\s*(?:<rdf:[^>]+>\s*)*(?:<rdf:li[^>]*>)?([^<]+)<", xmp)
            if m:
                return m.group(1).strip()
        return None

    out["digital_source_type"] = grab(["Iptc4xmpExt:DigitalSourceType"])
    out["creator_tool"] = grab(["xmp:CreatorTool"])
    out["description"] = grab(["dc:description"])
    out["creator"] = grab(["dc:creator"])
    out["credit"] = grab(["photoshop:Credit"])
    out["document_id"] = grab(["xmpMM:DocumentID"])
    agents = re.findall(r'stEvt:softwareAgent\s*=\s*"([^"]*)"', xmp) or re.findall(r"<stEvt:softwareAgent>([^<]+)<", xmp)
    if agents:
        out["history_software_agents"] = list(dict.fromkeys(agents))
    return {k: v for k, v in out.items() if v}


def _exif_summary(img: Image.Image) -> dict:
    out = {}
    try:
        exif = img.getexif()
    except Exception:
        return out
    wanted = {271: "make", 272: "model", 305: "software", 306: "datetime", 315: "artist", 33432: "copyright",
              274: "orientation"}
    for tag, key in wanted.items():
        if tag in exif:
            out[key] = str(exif.get(tag))[:200]
    try:
        ifd = exif.get_ifd(ExifTags.IFD.Exif)
        for tag, key in {36867: "datetime_original", 42036: "lens_model", 33434: "exposure_time", 34855: "iso"}.items():
            if tag in ifd:
                out[key] = str(ifd.get(tag))[:100]
        gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
        if gps:
            out["gps_present"] = True
    except Exception:
        pass
    return out


def _png_text(img: Image.Image) -> dict:
    text = {}
    for k, v in (getattr(img, "text", None) or {}).items():
        if isinstance(v, str):
            text[k] = v[:1500]
    for k in ("Software", "Comment", "Description", "Author", "parameters", "prompt", "workflow", "Title"):
        v = img.info.get(k)
        if isinstance(v, str) and k not in text:
            text[k] = v[:1500]
    return text


def _generator_hints(blob: str) -> list[str]:
    hits = []
    low = blob.lower()
    for pat, label in GENERATOR_HINTS:
        if re.search(pat, low):
            hits.append(label)
    return list(dict.fromkeys(hits))


class MetadataAnalyzer(Analyzer):
    name = "metadata"
    modalities = ("image",)

    def run(self, ctx: Context) -> list[Signal]:
        data = open(ctx.path, "rb").read()
        info: dict = {"format": None}
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
            info.update({"format": img.format, "mode": img.mode, "size": list(img.size)})
            info["exif"] = _exif_summary(img)
            info["icc_profile"] = bool(img.info.get("icc_profile"))
            if img.format == "PNG":
                info["png_text"] = _png_text(img)
            if img.format == "JPEG":
                info["jpeg_segments"] = _jpeg_segment_map(data)
                info["progressive"] = bool(img.info.get("progressive"))
        except Exception as e:
            info["error"] = f"PIL could not open: {e}"
        xmp = _extract_xmp(data)
        info["xmp_present"] = bool(xmp)
        if xmp:
            info["xmp"] = _xmp_fields(xmp)
            info["xmp_raw_excerpt"] = xmp[:1200]

        # ---- interpretation
        dst = (info.get("xmp") or {}).get("digital_source_type")
        dst_key = dst.rsplit("/", 1)[-1] if dst else None
        cls, grade = AI_DST_VALUES.get(dst_key, (None, "none")) if dst_key else (None, "none")

        blob = json.dumps({k: info.get(k) for k in ("exif", "xmp", "png_text")}, ensure_ascii=False)
        hints = _generator_hints(blob)
        png_text = info.get("png_text") or {}
        sd_ui = None
        if "parameters" in png_text:
            sd_ui = "Automatic1111/Forge-style 'parameters' chunk (prompt + sampler settings)"
        elif "prompt" in png_text or "workflow" in png_text:
            sd_ui = "ComfyUI 'prompt'/'workflow' JSON chunk"
        elif "Comment" in png_text and "NovelAI" in png_text.get("Software", ""):
            sd_ui = "NovelAI"
        if sd_ui:
            hints.insert(0, sd_ui)

        stripped = []
        if info.get("format") == "JPEG":
            segs = info.get("jpeg_segments", [])
            if not any("EXIF" in s for s in segs) and not info["xmp_present"] and not any("JUMBF" in s for s in segs):
                stripped.append("no EXIF, no XMP, no C2PA: metadata absent (typical of screenshots, social re-encodes, or deliberate stripping)")
            if any("APP14" in s for s in segs) and not info["xmp_present"]:
                stripped.append("Adobe APP14 marker without XMP: possibly exported/flattened")
        if info.get("format") == "PNG" and not png_text and not info["xmp_present"]:
            stripped.append("PNG without text chunks or XMP")

        if cls:
            status, summary = "detected", f"IPTC DigitalSourceType = {dst_key} ({cls}). This is exactly the field Meta/Google read to label AI content."
        elif hints:
            status, grade = "detected", "weak"
            summary = "Generator/tool clues in metadata: " + ", ".join(hints) + ". Attribution hint only: easily forged or removed."
        elif stripped:
            status, grade, summary = "info", "none", stripped[0][:1].upper() + stripped[0][1:] + "."
        else:
            status, grade, summary = "info", "none", "Ordinary metadata; no AI source-type fields or generator tags."

        return [Signal(kind="metadata", name="Metadata forensics (EXIF / XMP / IPTC / PNG text)", status=status,
                       evidence_grade=grade, summary=summary,
                       data={"iptc_digital_source_type": dst, "class": cls, "generator_hints": hints,
                             "stripped_indicators": stripped, **info},
                       method="Pillow + XMP/segment parsing (exiftool recommended in production)")]
