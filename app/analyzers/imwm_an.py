"""Open-source image watermark decoders.

LIVE now:   DWT-DCT 'invisible-watermark' as shipped by Stable Diffusion 1.x/2.x ("StableDiffusionV1" text payload)
            and diffusers' SDXL pipeline (fixed 48-bit pattern).
MANUAL:     Stable Signature extractor, Adobe TrustMark, Meta Watermark-Anything (all need torch + weights).
"""
from __future__ import annotations

import math

import numpy as np

from .base import Analyzer, Context, Signal
from . import dwtdct

SDXL_BITS_INT = 0b101100111110110010010000011110111011000110011110  # diffusers watermark.py WATERMARK_MESSAGE
SDXL_BITS = [int(b) for b in bin(SDXL_BITS_INT)[2:].zfill(48)]
SD1_TEXT = b"StableDiffusionV1"
SD1_BITS = list(np.unpackbits(np.frombuffer(SD1_TEXT, dtype=np.uint8)))


def binom_p_at_least(k: int, n: int, p: float = 0.5) -> float:
    """One-sided P(X >= k) for X ~ Binomial(n, p). n <= ~200 so a direct sum is fine."""
    return sum(math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(k, n + 1))


def _match(bits_found, expected):
    k = int(sum(int(a) == b for a, b in zip(bits_found, expected)))
    n = len(expected)
    return k / n, binom_p_at_least(k, n)


def decode_image_bgr(bgr: np.ndarray) -> dict:
    h, w = bgr.shape[:2]
    if h * w < 256 * 256:
        return {"skipped": "image smaller than 256x256; scheme undefined"}
    bits48, avg48 = dwtdct.decode_bits(bgr, 48)
    acc_sdxl, p_sdxl = _match(bits48, SDXL_BITS)
    bits136, _ = dwtdct.decode_bits(bgr, len(SD1_BITS))
    acc_sd1, p_sd1 = _match(bits136, SD1_BITS)
    try:
        text = np.packbits(bits136.astype(np.uint8)).tobytes().decode("utf-8", "replace")
    except Exception:
        text = ""
    return {"sdxl": {"bit_accuracy": round(acc_sdxl, 4), "p_value": p_sdxl, "bits": "".join(str(int(b)) for b in bits48),
                     "mean_votes": [round(float(x), 3) for x in avg48]},
            "sd1": {"bit_accuracy": round(acc_sd1, 4), "p_value": p_sd1, "decoded_text": text}}


def interpret(res: dict) -> tuple[str, str, str]:
    """-> (status, grade, summary)"""
    if "skipped" in res:
        return "skipped", "none", res["skipped"]
    best = max(("SDXL 48-bit pattern (diffusers)", res["sdxl"]), ("SD 1.x/2.x 'StableDiffusionV1'", res["sd1"]),
               key=lambda kv: kv[1]["bit_accuracy"])
    name, r = best
    acc, p = r["bit_accuracy"], r["p_value"]
    if acc >= 0.85 and p < 1e-6:
        return "detected", "moderate", f"{name} decoded with {acc:.0%} bit accuracy (p={p:.1e}). Open scheme: strong positive evidence of an SD-family pipeline, but the mark is public and could be copied."
    if acc >= 0.72:
        return "inconclusive", "weak", f"Partial match to {name} ({acc:.0%}, p={p:.2e}) — consistent with a degraded watermark (resize/compression) or chance."
    return "absent", "none", f"No DWT-DCT watermark payload (best match {acc:.0%}). A miss proves nothing: resizing or cropping destroys this scheme."


class OpenImageWatermarkAnalyzer(Analyzer):
    name = "open_watermarks"
    modalities = ("image",)

    def available(self):
        return (True, "") if dwtdct.HAVE_DEPS else (False, "pip install opencv-python-headless PyWavelets")

    def run(self, ctx: Context) -> list[Signal]:
        out = []
        if not dwtdct.HAVE_DEPS:
            out.append(Signal(kind="open_watermark", name="DWT-DCT invisible-watermark (SD / SDXL)", status="not_installed",
                              manual_integration="pip install opencv-python-headless PyWavelets"))
        else:
            import cv2
            bgr = cv2.imread(ctx.path, cv2.IMREAD_COLOR)
            if bgr is None:
                out.append(Signal(kind="open_watermark", name="DWT-DCT invisible-watermark (SD / SDXL)", status="error",
                                  summary="OpenCV could not decode the image"))
            else:
                res = decode_image_bgr(bgr)
                status, grade, summary = interpret(res)
                out.append(Signal(kind="open_watermark", name="DWT-DCT invisible-watermark (SD / SDXL)", status=status,
                                  evidence_grade=grade, summary=summary, data=res,
                                  method="port of ShieldMnt/invisible-watermark dwtDct (U channel, scale 36, 4x4 blocks)"))
        # ---- manual-integration placeholders (kept visible so the report is honest about coverage)
        out.append(Signal(kind="open_watermark", name="Stable Signature extractor (Meta)", status="not_installed",
                          summary="48-bit latent-decoder watermark. Needs torch + the published extractor weights.",
                          manual_integration="pip install torch; download extractor from github.com/facebookresearch/stable_signature; wire analyzers/stable_signature_an.py"))
        out.append(Signal(kind="open_watermark", name="TrustMark decoder (Adobe)", status="not_installed",
                          summary="Universal watermark used as C2PA soft binding. Needs torch + `pip install trustmark`.",
                          manual_integration="pip install torch trustmark; call TrustMark(verbose=False).decode(PIL image)"))
        out.append(Signal(kind="open_watermark", name="Watermark Anything (Meta WAM)", status="not_installed",
                          summary="Localised multi-message watermark; returns a mask of watermarked pixels.",
                          manual_integration="torch + github.com/facebookresearch/watermark-anything checkpoints"))
        return out
