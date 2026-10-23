"""Provenably Sanitizer — remove container metadata / C2PA and verify the result.

Phase 1–2 scope: JPEG, PNG, WebP, PDF, DOCX. See ``docs/PRD.md`` for the full roadmap.

This deliberately does NOT remove embedded statistical watermarks. It strips metadata and
provenance manifests only, then re-scans to prove what is gone.
"""
from .image import (  # noqa: F401
    SUPPORTED_MIME,
    SanitizePolicy,
    UnsupportedFormat,
    detect_format,
    inspect_bytes,
    sanitize_bytes,
)

__all__ = [
    "SUPPORTED_MIME",
    "SanitizePolicy",
    "UnsupportedFormat",
    "detect_format",
    "inspect_bytes",
    "sanitize_bytes",
]
