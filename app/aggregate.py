"""Turn a list of Signals into one defensible conclusion.

Rules (in priority order):
 1. C2PA 'modified_after_signing' or hash-mismatch  -> tampered_after_signing (strong)
 2. Valid C2PA with AI digitalSourceType            -> ai_generated_declared / ai_assisted_declared (grade from trust)
 3. Valid C2PA with capture source                  -> captured_declared
 4. Vendor watermark detected (via connector)       -> ai_generated_watermark (strong)
 5. Open watermark detected                         -> ai_generated_watermark (moderate)
 6. IPTC/XMP/PNG-text AI generator metadata          -> ai_generated_metadata (weak: trivially editable)
 7. Text: hidden-character payload detected          -> text_marked (weak..moderate), greenlist detection -> text_watermark_detected
 8. Otherwise                                        -> no_provenance_signal (grade none)
Passive/forensic signals never set the class; they only appear as context.
"""
from __future__ import annotations

from .analyzers.base import Signal

CLASS_LABELS = {
    "tampered_after_signing": "Signed content was modified after signing",
    "ai_generated_declared": "AI-generated (declared in a Content Credential)",
    "ai_assisted_declared": "AI-edited / composite (declared in a Content Credential)",
    "captured_declared": "Camera capture (declared in a Content Credential)",
    "signed_no_source_type": "Signed Content Credential without a digital source type",
    "ai_generated_watermark": "AI-generated (watermark detected)",
    "ai_generated_metadata": "AI generator metadata present (unsigned, editable)",
    "text_watermark_detected": "Statistical text watermark detected (key supplied)",
    "text_hidden_characters": "Hidden/invisible characters present in text",
    "no_provenance_signal": "No provenance signal found",
}

GRADE_RANK = {"strong": 3, "moderate": 2, "weak": 1, "none": 0}


def aggregate(signals: list[Signal], modality: str) -> dict:
    sig = [s for s in signals if s.status not in ("skipped",)]
    c2pa = [s for s in sig if s.kind == "c2pa"]
    for s in c2pa:
        pc = s.data.get("provenance_class")
        if pc == "tampered_after_signing" or s.data.get("modified_after_signing"):
            return _conc("tampered_after_signing", "strong", s, [
                "The embedded Content Credential's hard binding no longer matches the pixels/bytes — the content was edited or re-encoded after signing. This is NOT by itself evidence of AI; treat the manifest as stale."])
    for s in c2pa:
        pc = s.data.get("provenance_class")
        if s.status == "detected" and pc in ("ai_generated_declared", "ai_assisted_declared", "captured_declared", "signed_no_source_type"):
            notes = []
            if s.evidence_grade == "moderate":
                notes.append("Signature verifies but the signer is not on the configured trust list — identity unverified.")
            if pc == "signed_no_source_type":
                notes.append("Manifest is valid but declares no digitalSourceType; check actions and ingredients.")
            return _conc(pc, s.evidence_grade, s, notes)
    vend = [s for s in sig if s.kind == "vendor_watermark" and s.status == "detected"]
    if vend:
        return _conc("ai_generated_watermark", "strong", vend[0], [f"Confirmed by vendor verifier: {vend[0].name}."])
    openwm = [s for s in sig if s.kind == "open_watermark" and s.status == "detected"]
    if openwm:
        best = max(openwm, key=lambda s: GRADE_RANK.get(s.evidence_grade, 0))
        return _conc("ai_generated_watermark", best.evidence_grade, best,
                     ["Open watermark pattern matched (default Stable Diffusion pipeline family). The pattern can be forged; corroborate with other signals before publishing a claim."])
    if modality == "text":
        gl = [s for s in sig if s.kind == "text_watermark" and s.status == "detected"]
        if gl:
            return _conc("text_watermark_detected", gl[0].evidence_grade, gl[0], [])
        hid = [s for s in sig if s.kind == "text_hygiene" and s.status == "detected"]
        if hid:
            return _conc("text_hidden_characters", hid[0].evidence_grade, hid[0],
                         ["Hidden characters indicate copy-paste from a tool that inserts them (or deliberate marking); they are not proof of AI authorship."])
    meta = [s for s in sig if s.kind == "metadata" and s.status == "detected"]
    if meta:
        return _conc("ai_generated_metadata", "weak", meta[0],
                     ["Unsigned metadata is trivially editable in both directions; use it as a hint, not as evidence."])
    inconclusive = [s for s in sig if s.status == "inconclusive"]
    notes = ["No Content Credential, no vendor or open watermark, no generator metadata."]
    if inconclusive:
        notes.append("Some detectors returned borderline scores (see signals).")
    notes.append("Absence of provenance is not evidence of human origin: most generators still ship nothing, and metadata is stripped by messaging apps, screenshots and most social platforms.")
    return {"provenance_class": "no_provenance_signal", "label": CLASS_LABELS["no_provenance_signal"], "evidence_grade": "none",
            "decisive_signal": None, "notes": notes}


def _conc(cls: str, grade: str, s: Signal, notes: list[str]) -> dict:
    return {"provenance_class": cls, "label": CLASS_LABELS[cls], "evidence_grade": grade,
            "decisive_signal": s.name, "notes": notes}


def coverage(signals: list[Signal]) -> dict:
    """How much of the detector surface actually ran — shown on the report so 'clean' never over-claims."""
    live = [s for s in signals if s.status in ("detected", "absent", "info", "inconclusive")]
    manual = [s for s in signals if s.status in ("not_installed", "not_configured")]
    errors = [s for s in signals if s.status == "error"]
    return {"live": len(live), "manual": len(manual), "errors": len(errors),
            "manual_modules": [{"name": s.name, "status": s.status, "how": s.manual_integration} for s in manual]}
