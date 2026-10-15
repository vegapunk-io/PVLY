"""Scan pipeline: sniff modality -> run applicable analyzers (isolated, timed) -> aggregate -> persist.

Synchronous and single-process on purpose for the prototype; the same `run_scan(scan_id)` entry point is what a
Celery/RQ/Arq worker would call once you move to a queue (see README "Scaling path").
"""
from __future__ import annotations

import hashlib
import logging
import os
import pathlib
import time
import traceback
import uuid

from . import config, db
from .aggregate import aggregate, coverage
from .analyzers.base import Context, Signal
from .analyzers.c2pa_an import C2PAAnalyzer, trust_sources
from .analyzers.metadata_an import MetadataAnalyzer
from .analyzers.imwm_an import OpenImageWatermarkAnalyzer
from .analyzers.forensics_an import ImageForensicsAnalyzer
from .analyzers.text_an import TextAnalyzer
from .analyzers.audio_an import AudioAnalyzer
from .analyzers.video_an import VideoAnalyzer
from .analyzers.vendor_an import VendorConnectorsAnalyzer
from .rules import engine

log = logging.getLogger("provenably.pipeline")

ANALYZERS = [
    C2PAAnalyzer(),
    MetadataAnalyzer(),
    OpenImageWatermarkAnalyzer(),
    ImageForensicsAnalyzer(),
    AudioAnalyzer(),
    VideoAnalyzer(),
    TextAnalyzer(),
    VendorConnectorsAnalyzer(),
]

MAGIC = [
    (b"\xff\xd8\xff", "image/jpeg", "image"),
    (b"\x89PNG\r\n\x1a\n", "image/png", "image"),
    (b"GIF8", "image/gif", "image"),
    (b"ID3", "audio/mpeg", "audio"),
    (b"\xff\xfb", "audio/mpeg", "audio"),
    (b"\xff\xf3", "audio/mpeg", "audio"),
    (b"fLaC", "audio/flac", "audio"),
    (b"OggS", "audio/ogg", "audio"),
    (b"%PDF", "application/pdf", "document"),
]


def sniff(head: bytes, filename: str) -> tuple[str, str]:
    """Return (mime, modality) from magic bytes, falling back to the extension."""
    for magic, mime, mod in MAGIC:
        if head.startswith(magic):
            return mime, mod
    if head[:4] == b"RIFF":
        if head[8:12] == b"WAVE":
            return "audio/wav", "audio"
        if head[8:12] == b"WEBP":
            return "image/webp", "image"
        if head[8:12] == b"AVI ":
            return "video/x-msvideo", "video"
    if head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in (b"avif", b"avis"):
            return "image/avif", "image"
        if brand in (b"heic", b"heix", b"mif1", b"heif"):
            return "image/heic", "image"
        if brand in (b"M4A ",):
            return "audio/mp4", "audio"
        return "video/mp4", "video"
    if head[:4] == b"\x1aE\xdf\xa3":
        return "video/webm", "video"
    if head[:2] in (b"II", b"MM") and head[2:4] in (b"*\x00", b"\x00*"):
        return "image/tiff", "image"
    ext = pathlib.Path(filename).suffix.lower()
    by_ext = {".txt": ("text/plain", "text"), ".md": ("text/markdown", "text"), ".html": ("text/html", "text"),
              ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "document"),
              ".mp3": ("audio/mpeg", "audio"), ".wav": ("audio/wav", "audio"), ".mp4": ("video/mp4", "video"), ".mov": ("video/quicktime", "video"),
              ".jpg": ("image/jpeg", "image"), ".jpeg": ("image/jpeg", "image"), ".png": ("image/png", "image"), ".webp": ("image/webp", "image")}
    if ext in by_ext:
        return by_ext[ext]
    try:
        head.decode("utf-8")
        return "text/plain", "text"
    except UnicodeDecodeError:
        return "application/octet-stream", "unknown"


def new_scan_from_bytes(data: bytes, filename: str, hash_only: bool = False, options: dict | None = None) -> str:
    scan_id = uuid.uuid4().hex[:12]
    mime, modality = sniff(data[:64], filename)
    sha = hashlib.sha256(data).hexdigest()
    blob_path = None
    if modality == "text" and len(data) < 2_000_000:
        # keep text inline in the blob too (analyzers read ctx.text)
        pass
    ext = pathlib.Path(filename).suffix.lower() or ""
    blob_path = str(config.BLOB_DIR / f"{scan_id}{ext}")
    with open(blob_path, "wb") as f:
        f.write(data)
    db.create_scan(scan_id, modality, filename, mime, len(data), sha, hash_only, blob_path)
    return scan_id


def new_scan_from_text(text: str, filename: str = "pasted.txt", options: dict | None = None) -> str:
    return new_scan_from_bytes(text.encode("utf-8"), filename, hash_only=False, options=options)


def run_scan(scan_id: str, options: dict | None = None) -> dict:
    """Execute all applicable analyzers for a stored scan. Safe to call from a background task or a worker."""
    row = db.get_scan(scan_id)
    if not row:
        raise KeyError(scan_id)
    db.set_status(scan_id, "running")
    t0 = time.time()
    path = row["blob_path"]
    text = None
    if row["modality"] == "text" and path:
        text = open(path, "rb").read().decode("utf-8", "replace")
    ctx = Context(scan_id=scan_id, modality=row["modality"], path=path, filename=row["filename"], mime=row["mime"],
                  sha256=row["sha256"], size=row["size"], text=text, options=options or {})
    signals: list[Signal] = []
    timings = []
    for an in ANALYZERS:
        if ctx.modality not in an.modalities:
            continue
        ok, msg = an.available()
        t = time.time()
        if not ok:
            signals.append(Signal(kind=an.name, name=an.name, status="not_installed", summary=msg, manual_integration=msg))
            continue
        try:
            out = an.run(ctx)
        except Exception as e:  # analyzer isolation: one failure never kills the report
            log.exception("analyzer %s failed", an.name)
            out = [Signal(kind=an.name, name=f"{an.name} (crashed)", status="error", summary=f"{type(e).__name__}: {e}"[:300],
                          data={"trace": traceback.format_exc()[-1500:]})]
        ms = int((time.time() - t) * 1000)
        for s in out:
            s.duration_ms = ms
        signals.extend(out)
        timings.append({"analyzer": an.name, "ms": ms, "signals": len(out)})
    conclusion = aggregate(signals, ctx.modality)
    report = {
        "scan_id": scan_id,
        "product": {"name": config.APP_NAME, "version": config.APP_VERSION},
        "created_at": row["created_at"],
        "completed_at": time.time(),
        "duration_ms": int((time.time() - t0) * 1000),
        "file": {"filename": row["filename"], "mime": row["mime"], "size": row["size"], "sha256": row["sha256"]},
        "modality": ctx.modality,
        "conclusion": conclusion,
        "signals": [s.to_dict() for s in signals],
        "coverage": coverage(signals),
        "timings": timings,
        "trust_sources": trust_sources(),
        "hash_only": bool(row["hash_only"]),
    }
    facts = engine.facts_from_report(report)
    report["platform_preview"] = engine.platform_preview(facts)
    report["facts"] = facts
    db.save_report(scan_id, report)
    if row["hash_only"] and path:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        db.clear_blob(scan_id)
    return report


def cleanup_expired_blobs() -> int:
    n = 0
    for r in db.expired_blobs():
        try:
            if r["blob_path"] and os.path.exists(r["blob_path"]):
                os.remove(r["blob_path"])
            db.clear_blob(r["id"])
            n += 1
        except Exception:
            log.exception("cleanup failed for %s", r["id"])
    return n


def analyze_bytes_sync(data: bytes, filename: str, hash_only: bool = False) -> dict:
    """Convenience for tests/CLI: create + run in one go."""
    sid = new_scan_from_bytes(data, filename, hash_only=hash_only)
    return run_scan(sid)
