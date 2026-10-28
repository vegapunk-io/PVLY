"""Image forensic context (NOT an AI detector): JPEG quality estimate, noise level, dimensions typical of generators.

Everything here is 'info' or 'weak' by construction. The passive AI classifier (UnivFD / GenImage-trained CNN)
is a MANUAL integration because it needs a GPU-class model and a published false-positive rate before it may
appear in a customer-facing report.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image

from .base import Analyzer, Context, Signal

# Standard IJG luminance quantisation table (quality 50) – used to estimate the save quality.
STD_LUMA = np.array([
    16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99], dtype=float)

GENERATOR_SIZES = {
    (1024, 1024): "1024²: DALL·E 3 / SDXL / Firefly / Midjourney default", (1792, 1024): "1792×1024: DALL·E 3 wide",
    (1024, 1792): "1024×1792: DALL·E 3 tall", (512, 512): "512²: SD 1.x default", (768, 768): "768²: SD 2.x",
    (1536, 1024): "1536×1024: ChatGPT images landscape", (1024, 1536): "1024×1536: ChatGPT images portrait",
    (1456, 816): "1456×816: Midjourney 16:9 (v6)", (1344, 768): "1344×768: SDXL 16:9",
}


def estimate_jpeg_quality(img: Image.Image) -> int | None:
    q = getattr(img, "quantization", None)
    if not q:
        return None
    table = np.array(q.get(0) or next(iter(q.values())), dtype=float)
    if table.size != 64:
        return None
    scale = float(np.mean(table / STD_LUMA)) * 100.0  # IJG: table = clamp(std*scale/100)
    quality = 5000.0 / scale / 100.0 if scale > 100 else 100 - scale / 2
    return int(round(max(1, min(100, quality))))


class ImageForensicsAnalyzer(Analyzer):
    name = "forensics"
    modalities = ("image",)

    def run(self, ctx: Context) -> list[Signal]:
        out = []
        try:
            img = Image.open(ctx.path)
            img.load()
        except Exception as e:
            return [Signal(kind="forensics", name="Image forensic context", status="error", summary=str(e)[:200])]
        w, h = img.size
        info = {"width": w, "height": h, "format": img.format, "mode": img.mode}
        if img.format == "JPEG":
            info["estimated_jpeg_quality"] = estimate_jpeg_quality(img)
            info["subsampling"] = str(img.info.get("subsampling", "?"))
        info["generator_size_hint"] = GENERATOR_SIZES.get((w, h))
        try:
            g = np.asarray(img.convert("L"), dtype=float)
            if g.size > 4_000_000:
                step = int(np.sqrt(g.size / 4_000_000)) + 1
                g = g[::step, ::step]
            lap = (-4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:])
            info["noise_laplacian_std"] = round(float(lap.std()), 2)
            info["mean_luma"] = round(float(g.mean()), 1)
        except Exception:
            pass
        hints = []
        if info.get("generator_size_hint"):
            hints.append(info["generator_size_hint"])
        if info.get("estimated_jpeg_quality") is not None and info["estimated_jpeg_quality"] <= 80:
            hints.append(f"re-compressed at ~q{info['estimated_jpeg_quality']} (typical of social/messaging re-encodes)")
        summary = ("Context only: not evidence of AI. " + "; ".join(hints)) if hints else "Context only: nothing notable."
        out.append(Signal(kind="forensics", name="Image forensic context", status="info", evidence_grade="none",
                          summary=summary, data=info, method="PIL quantisation tables + Laplacian noise estimate"))
        out.append(Signal(kind="passive", name="Passive AI-image classifier", status="not_installed", evidence_grade="none",
                          summary="Disabled by design until a calibrated model with a published FPR is integrated.",
                          manual_integration="Integrate UnivFD (CLIP-ViT features + linear probe) or a GenImage-trained "
                                             "classifier on Modal/GPU; calibrate (temperature scaling) on your own real-photo "
                                             "corpus; publish FPR; then enable in analyzers/passive_image_an.py"))
        return out
