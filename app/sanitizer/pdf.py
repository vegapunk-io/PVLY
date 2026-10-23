"""PDF sanitizer (Phase 2) using pikepdf/qpdf.

Removes: document Info dictionary, XMP metadata streams, embedded file attachments and
associated-file arrays. C2PA in PDF lives in XMP and/or embedded files, so this clears it.

Not removed: raster images embedded in the PDF keep their own EXIF/XMP unless recompressed.
"""
from __future__ import annotations

import hashlib
import io
from dataclasses import asdict

from .image import SUPPORTED_MIME, SanitizePolicy, UnsupportedFormat, _coerce_policy


try:
    import pikepdf  # type: ignore
    HAVE_PIKEPDF = True
except Exception:  # pragma: no cover
    pikepdf = None
    HAVE_PIKEPDF = False


def _open(data: bytes):
    if not HAVE_PIKEPDF:
        raise UnsupportedFormat("pikepdf not installed (pip install pikepdf)")
    try:
        return pikepdf.open(io.BytesIO(data))
    except pikepdf.PasswordError:
        raise UnsupportedFormat("PDF is password-protected; cannot sanitize without the password")
    except Exception as e:
        raise UnsupportedFormat(f"not a readable PDF: {e}")


def _inspect(pdf, data: bytes) -> dict:
    info = {}
    try:
        info = {k.lstrip("/").lower(): str(v) for k, v in pdf.docinfo.items()}
    except Exception:
        pass
    xmp = b""
    try:
        m = pdf.Root.get("/Metadata")
        if m is not None:
            xmp = bytes(m.read_bytes())
    except Exception:
        pass
    attachments = []
    try:
        attachments = [str(n) for n in pdf.attachments.keys()]
    except Exception:
        pass
    try:
        pages = len(pdf.pages)
    except Exception:
        pages = None
    low = xmp.lower()
    c2pa = (b"jumb" in data) or (b"c2pa" in low) or any("c2pa" in a.lower() for a in attachments)
    return {"format": "pdf", "info": info, "xmp": bool(xmp.strip()), "xmp_bytes": len(xmp),
            "attachments": attachments, "pages": pages, "c2pa": c2pa}


def inspect_pdf_bytes(data: bytes) -> dict:
    pdf = _open(data)
    try:
        return _inspect(pdf, data)
    finally:
        pdf.close()


def sanitize_pdf_bytes(data: bytes, filename: str = "file",
                       policy: SanitizePolicy | dict | None = None) -> tuple[bytes, dict]:
    policy = _coerce_policy(policy)
    pdf = _open(data)
    before = _inspect(pdf, data)
    warnings: list[str] = []
    removed: list[str] = []

    if before.get("pages"):
        warnings.append("Raster images inside the PDF may still carry their own EXIF/XMP; "
                        "only document-level metadata and attachments are removed.")

    try:
        for k in list(pdf.docinfo.keys()):
            del pdf.docinfo[k]
        if "/Info" in pdf.trailer:
            del pdf.trailer["/Info"]
        removed.append("document Info dictionary (Author/Title/Creator/Producer/Dates)")
    except Exception as e:
        warnings.append(f"could not clear Info dictionary: {e}")

    try:
        n = 0
        for obj in pdf.objects:
            if isinstance(obj, pikepdf.Dictionary) and "/Metadata" in obj:
                del obj["/Metadata"]
                n += 1
        if "/Metadata" in pdf.Root:
            del pdf.Root["/Metadata"]
            n += 1
        if n:
            removed.append(f"XMP metadata stream(s) ×{n}")
    except Exception as e:
        warnings.append(f"could not clear XMP metadata: {e}")

    try:
        names = [str(n) for n in pdf.attachments.keys()]
        for name in list(pdf.attachments.keys()):
            del pdf.attachments[name]
        if names:
            removed.append("embedded attachments: " + ", ".join(names))
        if "/AF" in pdf.Root:
            del pdf.Root["/AF"]
    except Exception as e:
        warnings.append(f"could not remove attachments: {e}")

    buf = io.BytesIO()
    try:
        pdf.save(buf)
    finally:
        pdf.close()
    out = buf.getvalue()

    p2 = _open(out)
    try:
        after = _inspect(p2, out)
    finally:
        p2.close()

    residual = {}
    if after.get("info"):
        residual["info"] = True
    if after.get("xmp"):
        residual["xmp"] = True
    if after.get("attachments"):
        residual["attachments"] = True
    if after.get("c2pa"):
        residual["c2pa"] = True

    report = {
        "job_id": None,
        "file": {
            "filename": filename, "format": "pdf", "mime": SUPPORTED_MIME["pdf"],
            "sha256_in": hashlib.sha256(data).hexdigest(),
            "sha256_out": hashlib.sha256(out).hexdigest(),
            "bytes_in": len(data), "bytes_out": len(out), "pages": after.get("pages"),
        },
        "policy": asdict(policy),
        "detected": before,
        "removed": [{"field": r} for r in removed],
        "kept": [],
        "verify": {"before": before, "after": after, "residual": residual,
                   "verdict": "clean" if not residual else "residual_metadata"},
        "lossless": False,
        "pixels_identical": None,
        "watermark_note": "Document metadata, XMP and attachments removed. Embedded statistical "
                          "watermarks are not removed; embedded raster images may retain their own metadata.",
        "warnings": warnings,
    }
    return out, report
