"""Vendor verification connectors.

These are **manual integrations**: each vendor exposes detection of *its own* marks through an authenticated
surface. The connector shape is implemented end-to-end (config -> request -> normalised Signal) but the request
is only sent when the operator supplies credentials. Without credentials the analyzer reports `not_configured`
and explains exactly what to fill in.

OpenAI Verify API, image (SynthID + C2PA, since 19 May 2026) and audio (since 31 Jul 2026).
Google SynthID Detector, public web tool since 7 Oct 2026; third-party API access is partner-gated  [verify].
Anthropic, text watermark on Claude models released on/after 2 Aug 2026; public detector announced, not released.
"""
from __future__ import annotations

import json
import urllib.request

from .base import Analyzer, Context, Signal
from .. import config


def _post_json(url: str, headers: dict, payload: dict, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec - operator-configured URL
        return json.loads(r.read().decode())


class VendorConnectorsAnalyzer(Analyzer):
    name = "vendor_connectors"
    modalities = ("image", "audio", "video")  # text vendors are reported by text_an.py

    def run(self, ctx: Context) -> list[Signal]:
        out = []
        # ---- OpenAI Verify ------------------------------------------------------------------
        if ctx.modality in ("image", "audio"):
            if config.OPENAI_VERIFY_ENDPOINT and config.OPENAI_VERIFY_API_KEY:
                try:
                    import base64
                    b64 = base64.b64encode(open(ctx.path, "rb").read()).decode()
                    resp = _post_json(config.OPENAI_VERIFY_ENDPOINT, {"Authorization": f"Bearer {config.OPENAI_VERIFY_API_KEY}"},
                                      {"content": b64, "mime_type": ctx.mime})
                    # Response schema is vendor-defined; normalise defensively.
                    hit = bool(resp.get("watermark_detected") or resp.get("detected") or resp.get("result") == "detected")
                    out.append(Signal(kind="vendor_watermark", name="OpenAI Verify (SynthID + C2PA)", status="detected" if hit else "absent",
                                      evidence_grade="strong" if hit else "none", summary="Vendor response normalised; raw payload attached.",
                                      data=resp, method="OpenAI Verify API"))
                except Exception as e:
                    out.append(Signal(kind="vendor_watermark", name="OpenAI Verify (SynthID + C2PA)", status="error", summary=str(e)[:200]))
            else:
                out.append(Signal(kind="vendor_watermark", name="OpenAI Verify (SynthID + C2PA)", status="not_configured", evidence_grade="none",
                                  summary="Detects OpenAI's own SynthID image/audio marks server-side. Not called: no credentials configured.",
                                  manual_integration="Set OPENAI_VERIFY_API_KEY and OPENAI_VERIFY_ENDPOINT in .env; confirm the current endpoint path and response schema in OpenAI's docs (the public Verify tool exists; API field names here are placeholders)."))
        # ---- Google SynthID -------------------------------------------------------------------
        if ctx.modality in ("image", "audio", "video"):
            if config.GOOGLE_SYNTHID_ENDPOINT and config.GOOGLE_ACCESS_TOKEN:
                try:
                    import base64
                    b64 = base64.b64encode(open(ctx.path, "rb").read()).decode()
                    resp = _post_json(config.GOOGLE_SYNTHID_ENDPOINT, {"Authorization": f"Bearer {config.GOOGLE_ACCESS_TOKEN}"}, {"content": b64, "mime_type": ctx.mime})
                    hit = bool(resp.get("watermark_detected") or resp.get("detected"))
                    out.append(Signal(kind="vendor_watermark", name="Google SynthID Detector", status="detected" if hit else "absent",
                                      evidence_grade="strong" if hit else "none", summary="Vendor response normalised; raw payload attached.",
                                      data=resp, method="Google SynthID Detector (partner API)"))
                except Exception as e:
                    out.append(Signal(kind="vendor_watermark", name="Google SynthID Detector", status="error", summary=str(e)[:200]))
            else:
                out.append(Signal(kind="vendor_watermark", name="Google SynthID Detector", status="not_configured", evidence_grade="none",
                                  summary="Covers Google, OpenAI, NVIDIA, Kakao, ElevenLabs marks (public web tool since 7 Oct 2026). Third-party API access is partner-gated.",
                                  manual_integration="Apply for SynthID Detector partner/API access; set GOOGLE_ACCESS_TOKEN and GOOGLE_SYNTHID_ENDPOINT. Until then, link the user to the public tool from the report."))
        return out
