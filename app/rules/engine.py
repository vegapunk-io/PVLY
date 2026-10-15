"""Rules engine: platform label preview + jurisdiction disclosure checklist.

Pure functions over the JSON rule files so they can be unit-tested and later moved to a DB-backed rules service.
Inputs are *facts* (the aggregated report conclusion or a user-supplied declaration); outputs are explanations,
never legal advice.
"""
from __future__ import annotations

import json
import pathlib

RULES_DIR = pathlib.Path(__file__).resolve().parent


def _load(name: str) -> dict:
    return json.loads((RULES_DIR / name).read_text())


PLATFORMS = _load("platforms.json")["platforms"]
JURISDICTIONS = _load("jurisdictions.json")["jurisdictions"]
REGISTRY = _load("registry.json")["entries"]
REGISTRY_META = _load("registry.json")["_meta"]


def registry_entry(slug: str) -> dict | None:
    return next((e for e in REGISTRY if e["slug"] == slug), None)


def registry_by_modality() -> dict:
    out: dict[str, list] = {}
    for e in REGISTRY:
        out.setdefault(e["modality"], []).append(e)
    return out


# ------------------------------------------------------------------------------------------------
# Facts derived from a report conclusion
# ------------------------------------------------------------------------------------------------

def facts_from_report(report: dict) -> dict:
    """Reduce a provenance report to the boolean facts platform rules care about."""
    conc = report.get("conclusion", {}) or {}
    cls = conc.get("provenance_class", "unknown")
    signals = report.get("signals", []) or []
    c2pa_valid = any(s["kind"] == "c2pa" and s["status"] == "detected" and s["evidence_grade"] in ("strong", "moderate") for s in signals)
    c2pa_ai = c2pa_valid and cls in ("ai_generated_declared", "ai_assisted_declared")
    iptc_ai = any(s["kind"] == "metadata" and s["status"] == "detected" and "DigitalSourceType" in json.dumps(s.get("data", {})) for s in signals)
    vendor_wm = any(s["kind"] == "vendor_watermark" and s["status"] == "detected" for s in signals)
    open_wm = any(s["kind"] == "open_watermark" and s["status"] == "detected" for s in signals)
    return {
        "modality": report.get("modality"),
        "provenance_class": cls,
        "c2pa_any": c2pa_valid,
        "c2pa_ai": c2pa_ai,
        "iptc_ai": iptc_ai,
        "vendor_watermark": vendor_wm,
        "synthid": vendor_wm,
        "open_watermark": open_wm,
        "tampered": cls == "tampered_after_signing",
    }


def platform_preview(facts: dict, self_disclosure: bool = False) -> list[dict]:
    """For each platform: will a label most likely appear, and why."""
    out = []
    for p in PLATFORMS:
        trig = p["auto_label_triggers"]
        reasons = []
        if "c2pa_ai" in trig and facts.get("c2pa_ai"):
            reasons.append("C2PA manifest declares AI generation/edit")
        if "c2pa_any" in trig and facts.get("c2pa_any"):
            reasons.append("valid C2PA manifest present")
        if "iptc_ai" in trig and facts.get("iptc_ai"):
            reasons.append("IPTC DigitalSourceType is an AI value")
        if ("synthid" in trig or "vendor_watermark_meta" in trig) and facts.get("vendor_watermark"):
            reasons.append("vendor watermark detected")
        if "self_disclosure" in trig and self_disclosure:
            reasons.append("you will self-disclose")
        likely = "yes" if reasons else ("unknown" if any(t in trig for t in ("internal_classifier", "internal_classifier_photoreal", "ad_auto_detect", "manual_review")) else "no")
        out.append({
            "platform": p["name"], "slug": p["slug"], "label_text": p["label_text"], "likely_label": likely,
            "reasons": reasons or (["platform may still label via its own classifier"] if likely == "unknown" else ["no trigger present in this file"]),
            "removal_policy": p["removal_policy"], "monetization_impact": p["monetization_impact"],
            "confidence": p["confidence"], "last_verified": p["last_verified"],
        })
    return out


# ------------------------------------------------------------------------------------------------
# Disclosure checklist
# ------------------------------------------------------------------------------------------------

def disclosure_check(*, content_type: str, is_ai_generated: bool, is_ai_edited: bool = False,
                     depicts_real_person: bool = False, public_interest_text: bool = False,
                     human_reviewed: bool = False, artistic: bool = False, jurisdictions: list[str] | None = None,
                     has_c2pa: bool = False, has_visible_label: bool = False, has_metadata_id: bool = False) -> dict:
    """Return a per-jurisdiction checklist for a deployer about to publish `content_type`."""
    sel = [j for j in JURISDICTIONS if not jurisdictions or j["slug"] in jurisdictions]
    synthetic = is_ai_generated or is_ai_edited
    results = []
    for j in sel:
        items = []
        req_keys = j["content_types"].get(content_type, [])
        for key in req_keys:
            text = j["obligations"][key]
            applies, why, status = True, "", "todo"
            if key == "deepfake_label":
                applies = synthetic and content_type in ("image", "video", "audio")
                if applies and not depicts_real_person and not is_ai_edited:
                    why = "Applies to content resembling real persons/objects/places/events that would falsely appear authentic; purely abstract or obviously synthetic art may fall outside the deepfake definition — document your assessment."
                if artistic:
                    why += " Artistic/satirical exception: disclose in a non-hampering way (e.g. caption/credits)."
                status = "done" if has_visible_label else "todo"
            elif key == "text_public_interest":
                applies = is_ai_generated and public_interest_text
                if applies and human_reviewed:
                    status = "exempt"
                    why = "Exempt: human review with editorial responsibility."
                else:
                    status = "done" if has_visible_label else "todo"
            elif key in ("label", "explicit_label"):
                applies = synthetic
                status = "done" if has_visible_label else "todo"
            elif key in ("metadata", "implicit_label", "latent_disclosure"):
                applies = synthetic
                status = "done" if (has_c2pa or has_metadata_id) else "todo"
                if applies and key == "latent_disclosure":
                    why = "Provider-side duty: if you generated with a covered provider (OpenAI, Google, Adobe …) the latent disclosure is already embedded — do not strip metadata when re-encoding."
            elif key == "manifest_disclosure":
                applies = synthetic
                status = "done" if has_c2pa else "optional"
            elif key == "deception":
                applies = synthetic
                status = "todo" if not (has_visible_label or has_c2pa) else "done"
                why = "No labelling mandate, but presenting synthetic media as authentic in commerce is risky under FTC §5 / state UDAP."
            if applies:
                items.append({"key": key, "requirement": text, "status": status, "note": why})
        results.append({
            "jurisdiction": j["name"], "slug": j["slug"], "effective": j["effective"], "status_note": j["status"],
            "penalty": j["penalty"], "items": items, "confidence": j["confidence"], "last_verified": j["last_verified"],
            "applies": bool(items),
        })
    todo = sum(1 for r in results for i in r["items"] if i["status"] == "todo")
    recommendations = []
    if synthetic and not has_c2pa:
        recommendations.append("Attach a C2PA manifest (c2pa-python / c2patool) with digitalSourceType=trainedAlgorithmicMedia (generated) or compositeWithTrainedAlgorithmicMedia (edited) before publishing; keep the original signed file.")
    if synthetic and not has_visible_label and content_type in ("image", "video", "audio"):
        recommendations.append("Add a visible/audible label (EU 'AI' icon or 'AI-generated' caption; India: prominent label; China: ≥5% text) — platform labels do not discharge the deployer duty.")
    if synthetic and not has_metadata_id:
        recommendations.append("Write IPTC/XMP Iptc4xmpExt:DigitalSourceType so Meta/Google/Pinterest label automatically and consistently.")
    if not synthetic:
        recommendations.append("No AI disclosure obligation identified. Consider signing with C2PA anyway to protect against later false 'AI' labelling.")
    return {"content_type": content_type, "synthetic": synthetic, "open_items": todo, "jurisdictions": results,
            "recommendations": recommendations, "disclaimer": "Rule summaries researched 2026-10-14; not legal advice. Verify entries marked confidence≠high."}
