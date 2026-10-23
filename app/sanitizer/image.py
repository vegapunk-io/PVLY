"""Metadata & C2PA sanitizer: lossless strip for JPEG/PNG/WebP, with PDF/DOCX dispatch.

Design goals
------------
* **Lossless by default** — strip container metadata without touching compressed pixel data,
  so the output is pixel-identical to the input whenever ``reencode=False``.
* **Detect → Strip → Verify** — every result carries the fields found *before*, the fields
  *removed*, and a re-scan proving what is left.
* **Honest** — embedded statistical watermarks (AudioSeal, VideoSeal, SynthID, DWT-DCT) are
  NOT removed by metadata stripping; the report always says so.

The format walkers are deliberately explicit (segment/chunk level), mirroring
``app/analyzers/jumbf.py`` so it is obvious where C2PA bytes live in each container.
"""
from __future__ import annotations

import hashlib
import io
import struct
from collections import Counter
from dataclasses import asdict, dataclass

from PIL import Image, ImageOps

from ..analyzers import jumbf

JPEG_SIG = b"\xff\xd8\xff"
PNG_SIG = b"\x89PNG\r\n\x1a\n"

SUPPORTED_MIME = {
    "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
SUPPORTED_EXT = {".jpg": "jpeg", ".jpeg": "jpeg", ".jpe": "jpeg", ".png": "png", ".webp": "webp",
                 ".pdf": "pdf", ".docx": "docx"}


class UnsupportedFormat(ValueError):
    """Raised when the input is not a supported sanitizer format."""


@dataclass
class SanitizePolicy:
    keep_icc: bool = True
    reencode: bool = False
    keep_orientation: bool = True


def _coerce_policy(policy) -> SanitizePolicy:
    if policy is None:
        return SanitizePolicy()
    if isinstance(policy, SanitizePolicy):
        return policy
    return SanitizePolicy(
        keep_icc=bool(policy.get("keep_icc", True)),
        reencode=bool(policy.get("reencode", False)),
        keep_orientation=bool(policy.get("keep_orientation", True)),
    )


# --------------------------------------------------------------------------- format detection
def detect_format(data: bytes, filename: str = "", mime: str = "") -> str | None:
    if data[:3] == JPEG_SIG:
        return "jpeg"
    if data[:8] == PNG_SIG:
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:4] == b"%PDF":
        return "pdf"
    if data[:2] == b"PK":
        try:
            import io as _io
            import zipfile
            with zipfile.ZipFile(_io.BytesIO(data)) as z:
                names = set(z.namelist())
            if "word/document.xml" in names:
                return "docx"
        except Exception:
            pass
    low_mime = (mime or "").lower()
    for fmt, m in SUPPORTED_MIME.items():
        if low_mime == m:
            return fmt
    ext = next((e for e in SUPPORTED_EXT if (filename or "").lower().endswith(e)), None)
    return SUPPORTED_EXT[ext] if ext else None


# --------------------------------------------------------------------------- JPEG walkers
def _iter_jpeg_segments(data: bytes):
    """Yield (marker, payload) for header segments, stopping at SOS/EOI."""
    i, n = 2, len(data)
    while i < n:
        if data[i] != 0xFF:
            i += 1
            continue
        j = i
        while j < n and data[j] == 0xFF:
            j += 1
        if j >= n:
            return
        marker = data[j]
        i = j + 1
        if marker == 0xD9 or marker == 0xDA:
            return
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        if i + 2 > n:
            return
        seglen = struct.unpack(">H", data[i:i + 2])[0]
        if seglen < 2 or i + seglen > n:
            return
        yield marker, data[i + 2:i + seglen]
        i += seglen


def _inspect_jpeg(data: bytes) -> dict:
    info = {"format": "jpeg", "exif": False, "xmp": False, "c2pa": False,
            "iptc": False, "icc": False, "comments": 0, "segments": []}
    for marker, payload in _iter_jpeg_segments(data):
        if marker == 0xE1:
            if payload.startswith(b"Exif"):
                info["exif"] = True
                info["segments"].append("APP1 EXIF")
            else:
                info["xmp"] = True
                info["segments"].append("APP1 XMP/other")
        elif marker == 0xE2:
            info["icc"] = True
            info["segments"].append("APP2 ICC")
        elif marker == 0xEB and payload[:2] == b"JP":
            info["c2pa"] = True
            info["segments"].append("APP11 JUMBF/C2PA")
        elif marker == 0xED:
            info["iptc"] = True
            info["segments"].append("APP13 IPTC/Photoshop")
        elif marker == 0xFE:
            info["comments"] += 1
            info["segments"].append("COM")
    if b"<x:xmpmeta" in data or b"http://ns.adobe.com/xap/1.0/" in data:
        info["xmp"] = True
    if jumbf.locate_jpeg(data):
        info["c2pa"] = True
    return info


def _strip_jpeg(data: bytes, policy: SanitizePolicy) -> tuple[bytes, list[str], list[str]]:
    if data[:3] != JPEG_SIG:
        raise UnsupportedFormat("not a JPEG")
    out = bytearray(b"\xff\xd8")
    removed, kept = [], []
    i, n = 2, len(data)
    while i < n:
        if data[i] != 0xFF:
            out += data[i:]
            break
        j = i
        while j < n and data[j] == 0xFF:
            j += 1
        if j >= n:
            break
        marker = data[j]
        i = j + 1
        if marker == 0xD9:
            out += b"\xff\xd9"
            break
        if marker == 0xDA:  # start of scan: copy header then entropy data verbatim
            if i + 2 > n:
                break
            seglen = struct.unpack(">H", data[i:i + 2])[0]
            out += b"\xff\xda" + data[i:i + seglen]
            i += seglen
            tail = data[i:]
            eoi = tail.find(b"\xff\xd9")
            out += tail[:eoi + 2] if eoi != -1 else tail
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            out += b"\xff" + bytes([marker])
            continue
        if i + 2 > n:
            break
        seglen = struct.unpack(">H", data[i:i + 2])[0]
        if seglen < 2 or i + seglen > n:
            break
        raw = b"\xff" + bytes([marker]) + data[i:i + seglen]
        payload = data[i + 2:i + seglen]
        i += seglen
        if marker == 0xE1:
            removed.append("APP1 (EXIF/XMP)")
            continue
        if marker == 0xEB and payload[:2] == b"JP":
            removed.append("APP11 (JUMBF/C2PA)")
            continue
        if marker == 0xED:
            removed.append("APP13 (IPTC/Photoshop)")
            continue
        if marker == 0xFE:
            removed.append("COM (comment)")
            continue
        if marker == 0xE2 and not policy.keep_icc:
            removed.append("APP2 (ICC profile)")
            continue
        if marker == 0xE2:
            kept.append("APP2 (ICC profile)")
        elif marker == 0xE0:
            kept.append("APP0 (JFIF)")
        elif marker == 0xEE:
            kept.append("APP14 (Adobe)")
        out += raw
    return bytes(out), removed, kept


# --------------------------------------------------------------------------- PNG walkers
def _png_chunks(data: bytes):
    """Yield (type, payload) for each PNG chunk."""
    if data[:8] != PNG_SIG:
        return
    pos, n = 8, len(data)
    while pos + 12 <= n:
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        if pos + 12 + length > n:
            return
        yield ctype, data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IEND":
            return


def _inspect_png(data: bytes) -> dict:
    info = {"format": "png", "exif": False, "xmp": False, "c2pa": False,
            "iptc": False, "icc": False, "text_chunks": 0, "timestamp": False, "chunks": []}
    for ctype, payload in _png_chunks(data):
        name = ctype.decode("latin1", "replace")
        info["chunks"].append(name)
        if ctype == b"eXIf":
            info["exif"] = True
        elif ctype == b"caBX":
            info["c2pa"] = True
        elif ctype == b"iCCP":
            info["icc"] = True
        elif ctype == b"tIME":
            info["timestamp"] = True
        elif ctype in (b"tEXt", b"zTXt", b"iTXt"):
            info["text_chunks"] += 1
            if b"XML:com.adobe.xmp" in payload:
                info["xmp"] = True
    if b"<x:xmpmeta" in data:
        info["xmp"] = True
    if jumbf.locate_png(data):
        info["c2pa"] = True
    return info


def _strip_png(data: bytes, policy: SanitizePolicy) -> tuple[bytes, list[str], list[str]]:
    if data[:8] != PNG_SIG:
        raise UnsupportedFormat("not a PNG")
    out = bytearray(PNG_SIG)
    removed, kept = [], []
    pos, n = 8, len(data)
    while pos + 12 <= n:
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        total = 12 + length
        if pos + total > n:
            break
        chunk = data[pos:pos + total]
        name = ctype.decode("latin1", "replace")
        drop = ctype in (b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"caBX", b"tIME")
        if ctype == b"iCCP" and not policy.keep_icc:
            drop = True
        if drop:
            removed.append(name)
        else:
            out += chunk
            kept.append(name)
        pos += total
        if ctype == b"IEND":
            break
    return bytes(out), removed, kept


# --------------------------------------------------------------------------- WebP walkers
def _webp_chunks(data: bytes):
    """Yield (fourcc, chunk_offset, total_len, payload) for a WebP RIFF container."""
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return
    pos, n = 12, len(data)
    while pos + 8 <= n:
        fourcc = data[pos:pos + 4]
        length = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        total = 8 + length + (length & 1)
        if pos + total > n:
            return
        yield fourcc, pos, total, data[pos + 8:pos + 8 + length]
        pos += total


def _inspect_webp(data: bytes) -> dict:
    info = {"format": "webp", "exif": False, "xmp": False, "c2pa": False,
            "iptc": False, "icc": False, "chunks": []}
    for fourcc, _off, _total, _payload in _webp_chunks(data):
        info["chunks"].append(fourcc.decode("latin1", "replace"))
        if fourcc == b"EXIF":
            info["exif"] = True
        elif fourcc == b"XMP ":
            info["xmp"] = True
        elif fourcc in (b"C2PA", b"c2pa", b"JUMB"):
            info["c2pa"] = True
        elif fourcc == b"ICCP":
            info["icc"] = True
    if b"<x:xmpmeta" in data:
        info["xmp"] = True
    if jumbf.locate_riff(data):
        info["c2pa"] = True
    return info


def _strip_webp(data: bytes, policy: SanitizePolicy) -> tuple[bytes, list[str], list[str]]:
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise UnsupportedFormat("not a WebP")
    chunks = bytearray()
    removed, kept = [], []
    for fourcc, _off, _total, payload in _webp_chunks(data):
        name = fourcc.decode("latin1", "replace")
        drop = fourcc in (b"EXIF", b"XMP ", b"C2PA", b"c2pa", b"JUMB")
        if fourcc == b"ICCP" and not policy.keep_icc:
            drop = True
        if drop:
            removed.append(name)
            continue
        raw = bytearray(fourcc + struct.pack("<I", len(payload)) + payload)
        if len(payload) & 1:
            raw += b"\x00"
        if fourcc == b"VP8X" and payload:
            # Clear EXIF (0x08) / XMP (0x04) / ICC (0x20) presence flags in the first data byte.
            flags = raw[8] & ~0x08 & ~0x04
            if not policy.keep_icc:
                flags &= ~0x20
            raw[8] = flags
        chunks += raw
        kept.append(name)
    body = b"WEBP" + bytes(chunks)
    return b"RIFF" + struct.pack("<I", len(body)) + body, removed, kept


# --------------------------------------------------------------------------- shared helpers
def _pil_meta(data: bytes) -> dict:
    try:
        im = Image.open(io.BytesIO(data))
        return {"width": im.width, "height": im.height, "mode": im.mode}
    except Exception:
        return {}


def _orientation(data: bytes) -> int | None:
    try:
        return Image.open(io.BytesIO(data)).getexif().get(274)
    except Exception:
        return None


def _pixels_equal(a: bytes, b: bytes) -> bool | None:
    try:
        ia, ib = Image.open(io.BytesIO(a)), Image.open(io.BytesIO(b))
        ia.load()
        ib.load()
        return ia.mode == ib.mode and ia.size == ib.size and ia.tobytes() == ib.tobytes()
    except Exception:
        return None


def _reencode(data: bytes, fmt: str, policy: SanitizePolicy) -> bytes:
    im = Image.open(io.BytesIO(data))
    im.load()
    if policy.keep_orientation:
        im = ImageOps.exif_transpose(im)
    icc = im.info.get("icc_profile") if policy.keep_icc else None
    buf = io.BytesIO()
    if fmt == "jpeg":
        im.convert("RGB").save(buf, "JPEG", quality=95, optimize=True, icc_profile=icc, exif=b"")
    elif fmt == "png":
        im.save(buf, "PNG", optimize=True, icc_profile=icc)
    else:  # webp
        im.save(buf, "WEBP", quality=95, method=6, icc_profile=icc)
    return buf.getvalue()


def _inspect_image(data: bytes, fmt: str) -> dict:
    if fmt == "jpeg":
        return _inspect_jpeg(data)
    if fmt == "png":
        return _inspect_png(data)
    if fmt == "webp":
        return _inspect_webp(data)
    raise UnsupportedFormat(f"unsupported image format: {fmt}")


def inspect_bytes(data: bytes, fmt: str | None = None) -> dict:
    """Return the metadata/provenance fields present in ``data`` (no modification)."""
    fmt = fmt or detect_format(data)
    if fmt in ("jpeg", "png", "webp"):
        return _inspect_image(data, fmt)
    if fmt == "pdf":
        from . import pdf
        return pdf.inspect_pdf_bytes(data)
    if fmt == "docx":
        from . import docx
        return docx.inspect_docx_bytes(data)
    raise UnsupportedFormat("unsupported file type; supported: JPEG, PNG, WebP, PDF, DOCX")


def _sanitize_image(data: bytes, filename: str = "file", policy: SanitizePolicy | dict | None = None) -> tuple[bytes, dict]:
    """Strip metadata/C2PA from an image ``data`` and return ``(sanitized_bytes, report)``."""
    policy = _coerce_policy(policy)
    fmt = detect_format(data, filename)
    if fmt not in ("jpeg", "png", "webp"):
        raise UnsupportedFormat("not a supported image (JPEG, PNG, WebP)")

    before = inspect_bytes(data, fmt)
    warnings: list[str] = []

    if policy.reencode:
        reencoded = _reencode(data, fmt, policy)
        # Belt-and-suspenders: rebuild the container so no writer-added metadata survives.
        if fmt == "jpeg":
            out, removed, kept = _strip_jpeg(reencoded, policy)
        elif fmt == "png":
            out, removed, kept = _strip_png(reencoded, policy)
        else:
            out, removed, kept = _strip_webp(reencoded, policy)
        removed = ["re-encoded clean (orientation baked)", *removed]
    else:
        if fmt == "jpeg":
            out, removed, kept = _strip_jpeg(data, policy)
        elif fmt == "png":
            out, removed, kept = _strip_png(data, policy)
        else:
            out, removed, kept = _strip_webp(data, policy)

    after = inspect_bytes(out, fmt)
    residual = {k: True for k in ("exif", "xmp", "c2pa", "iptc", "timestamp") if after.get(k)}
    if not policy.keep_icc and after.get("icc"):
        residual["icc"] = True
    if after.get("text_chunks"):
        residual["text_chunks"] = after["text_chunks"]
    clean = not residual

    pixels = None if policy.reencode else _pixels_equal(data, out)
    if pixels is False:
        warnings.append("pixel data changed during lossless strip — inspect the output")
    orient = _orientation(data)
    if orient not in (None, 1) and not policy.reencode:
        warnings.append("EXIF orientation was removed; pixels were not rotated (enable re-encode to bake it)")

    def _group(names: list[str]) -> list[dict]:
        return [{"field": k, "count": v} for k, v in Counter(names).items()]

    report = {
        "job_id": None,
        "file": {
            "filename": filename,
            "format": fmt,
            "mime": SUPPORTED_MIME[fmt],
            "sha256_in": hashlib.sha256(data).hexdigest(),
            "sha256_out": hashlib.sha256(out).hexdigest(),
            "bytes_in": len(data),
            "bytes_out": len(out),
            **_pil_meta(data),
        },
        "policy": asdict(policy),
        "detected": before,
        "removed": _group([r for r in removed if r]),
        "kept": _group(kept),
        "verify": {"before": before, "after": after, "residual": residual,
                   "verdict": "clean" if clean else "residual_metadata"},
        "lossless": not policy.reencode,
        "pixels_identical": pixels,
        "watermark_note": "Metadata and C2PA manifests removed. Embedded statistical watermarks "
                          "(AudioSeal, VideoSeal, SynthID, DWT-DCT) are not removed by this step.",
        "warnings": warnings,
    }
    return out, report


def sanitize_bytes(data: bytes, filename: str = "file",
                   policy: SanitizePolicy | dict | None = None) -> tuple[bytes, dict]:
    """Dispatch to the right format sanitizer and return ``(sanitized_bytes, report)``."""
    fmt = detect_format(data, filename)
    if fmt in ("jpeg", "png", "webp"):
        return _sanitize_image(data, filename, policy)
    if fmt == "pdf":
        from . import pdf
        return pdf.sanitize_pdf_bytes(data, filename, policy)
    if fmt == "docx":
        from . import docx
        return docx.sanitize_docx_bytes(data, filename, policy)
    raise UnsupportedFormat("unsupported file type; supported: JPEG, PNG, WebP, PDF, DOCX")
