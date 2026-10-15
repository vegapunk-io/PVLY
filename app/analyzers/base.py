"""Shared types for analyzers.

A *Signal* is a fact with provenance of its own: who produced it (analyzer), how (method),
what it found (status/data) and how much weight it may carry (evidence_grade).
The aggregator never lets a 'weak' signal outrank a 'strong' one.
"""
from __future__ import annotations

import dataclasses
import time
from dataclasses import dataclass, field
from typing import Any

GRADES = ("strong", "moderate", "weak", "none")
STATUSES = ("detected", "absent", "info", "inconclusive", "error", "not_configured", "not_installed", "skipped")


@dataclass
class Signal:
    kind: str                      # c2pa | metadata | open_watermark | vendor_watermark | passive | forensics | text_hygiene | container | connector
    name: str                      # short human label
    status: str                    # see STATUSES
    evidence_grade: str = "none"   # see GRADES
    summary: str = ""
    data: dict = field(default_factory=dict)
    method: str = ""               # library / algorithm used
    manual_integration: str | None = None   # non-empty => this module needs a manual step to become live
    duration_ms: int = 0

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        return d


@dataclass
class Context:
    scan_id: str
    modality: str                  # image | audio | video | text | document | unknown
    path: str | None               # file path on disk (None for text)
    filename: str
    mime: str
    sha256: str
    size: int
    text: str | None = None
    options: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)   # analyzers may stash things for later analyzers (e.g. frames)


class Analyzer:
    name = "analyzer"
    modalities: tuple[str, ...] = ()

    def available(self) -> tuple[bool, str]:
        return True, ""

    def run(self, ctx: Context) -> list[Signal]:  # pragma: no cover - interface
        raise NotImplementedError


def timed(fn, *a, **kw):
    t0 = time.time()
    out = fn(*a, **kw)
    return out, int((time.time() - t0) * 1000)
