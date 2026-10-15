"""C2PA / Content Credentials analyzer.

Validation is delegated to the official SDK (c2pa-python -> c2pa-rs). We add:
  * trust configuration (official anchors if fetched + a clearly-labelled demo anchor),
  * extraction of the human-meaningful facts (AI actions, digitalSourceType, signer, ingredients, soft bindings),
  * an evidence grade,
  * a "how it works" structure dump via the pure-Python JUMBF walker.
"""
from __future__ import annotations

import json
import logging
import pathlib
import threading

from .. import config
from .base import Analyzer, Context, Signal
from . import jumbf

log = logging.getLogger(__name__)

try:
    import c2pa  # type: ignore
    HAVE_SDK = True
except Exception:  # pragma: no cover
    c2pa = None
    HAVE_SDK = False

AI_DST = {
    "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia": ("ai_generated", "fully AI-generated (trainedAlgorithmicMedia)"),
    "http://cv.iptc.org/newscodes/digitalsourcetype/compositeWithTrainedAlgorithmicMedia": ("ai_assisted", "AI-edited composite (compositeWithTrainedAlgorithmicMedia)"),
    "http://cv.iptc.org/newscodes/digitalsourcetype/algorithmicMedia": ("algorithmic", "algorithmic media (non-trained)"),
    "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicData": ("ai_generated", "AI-generated data"),
    "http://cv.iptc.org/newscodes/digitalsourcetype/digitalCapture": ("captured", "digital capture (camera)"),
    "http://cv.iptc.org/newscodes/digitalsourcetype/computationalCapture": ("captured", "computational capture"),
    "http://cv.iptc.org/newscodes/digitalsourcetype/digitalCreation": ("human_created", "digital creation (human, e.g. illustration)"),
    "http://cv.iptc.org/newscodes/digitalsourcetype/humanEdits": ("human_edited", "human edits"),
}

_trust_loaded = {"sources": []}
_thread_state = threading.local()   # c2pa-rs keeps Settings in thread-local storage -> (re)apply per thread


def _load_trust():
    """Configure trust anchors in the *current thread* (idempotent per thread).

    c2pa-rs stores settings thread-locally, so a settings load on the main thread is invisible to worker
    threads (uvicorn threadpool, BackgroundTasks, queue workers). We therefore apply once per thread.
    Uses the deprecated-but-stable load_settings API."""
    if getattr(_thread_state, "done", False) or not HAVE_SDK:
        return
    pems, sources = [], []
    if config.TRUST_ANCHORS_PEM.exists():
        pems.append(config.TRUST_ANCHORS_PEM.read_text())
        sources.append(f"official anchors ({config.TRUST_ANCHORS_PEM.name})")
    if config.INCLUDE_DEMO_TRUST_ANCHOR and config.DEMO_ROOT_CA_PEM.exists():
        pems.append(config.DEMO_ROOT_CA_PEM.read_text())
        sources.append("DEMO root CA (test only)")
    settings = {"verify": {"verify_trust": True}, "trust": {"trust_anchors": "\n".join(pems)}}
    if config.TRUST_ALLOWED_PEM.exists():
        settings["trust"]["allowed_list"] = config.TRUST_ALLOWED_PEM.read_text()
        sources.append("allowed list")
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            c2pa.load_settings(json.dumps(settings))
        _trust_loaded["sources"] = sources
    except Exception as e:  # pragma: no cover
        log.warning("could not load trust settings: %s", e)
        _trust_loaded["sources"] = [f"error: {e}"]
    _thread_state.done = True


def trust_sources() -> list[str]:
    _load_trust()
    return _trust_loaded["sources"]


def _summarise_manifest(label: str, m: dict) -> dict:
    actions, dst_classes = [], []
    soft_bindings, training, assertion_labels = [], None, []
    ai_disclosure = None
    for a in m.get("assertions", []):
        lab = a.get("label", "")
        assertion_labels.append(lab)
        data = a.get("data", {}) or {}
        if lab.startswith("c2pa.actions"):
            for act in data.get("actions", []):
                dst = act.get("digitalSourceType")
                cls = AI_DST.get(dst, (None, None))[0] if dst else None
                if cls:
                    dst_classes.append(cls)
                agent = act.get("softwareAgent")
                if isinstance(agent, dict):
                    agent = " ".join(str(agent.get(k)) for k in ("name", "version") if agent.get(k))
                actions.append({"action": act.get("action"), "digitalSourceType": dst, "class": cls,
                                "softwareAgent": agent, "when": act.get("when"),
                                "description": AI_DST.get(dst, (None, None))[1] if dst else None})
        elif lab.startswith("c2pa.soft-binding"):
            soft_bindings.append({"alg": data.get("alg"), "blocks": len(data.get("blocks", []) or [])})
        elif "training-mining" in lab:
            training = data
        elif "ai-disclosure" in lab or "ai_disclosure" in lab:
            ai_disclosure = data
    ingredients = []
    for ing in m.get("ingredients", []) or []:
        ingredients.append({"title": ing.get("title"), "relationship": ing.get("relationship"),
                            "format": ing.get("format"), "active_manifest": ing.get("active_manifest"),
                            "validation_status": ing.get("validation_status")})
    cg = m.get("claim_generator_info") or m.get("claim_generator")
    if isinstance(cg, list) and cg:
        cg = " ".join(str(cg[0].get(k)) for k in ("name", "version") if cg[0].get(k))
    sig = m.get("signature_info") or {}
    return {
        "label": label, "title": m.get("title"), "claim_generator": cg,
        "signer": {"issuer": sig.get("issuer"), "common_name": sig.get("common_name"),
                   "alg": sig.get("alg"), "time": sig.get("time"), "cert_serial": sig.get("cert_serial_number")},
        "actions": actions, "ingredients": ingredients, "assertion_labels": assertion_labels,
        "soft_bindings": soft_bindings, "training_mining": training, "ai_disclosure": ai_disclosure,
        "dst_classes": sorted(set(dst_classes)),
    }


class C2PAAnalyzer(Analyzer):
    name = "c2pa"
    modalities = ("image", "audio", "video", "document")

    def available(self):
        return (True, "") if HAVE_SDK else (False, "pip install c2pa-python")

    def run(self, ctx: Context) -> list[Signal]:
        data = pathlib.Path(ctx.path).read_bytes()
        structure = jumbf.describe(data)
        if not HAVE_SDK:
            return [Signal(kind="c2pa", name="Content Credentials (C2PA)", status="not_installed",
                           summary="Official SDK missing — structure scan only.",
                           data={"structure": structure}, manual_integration="pip install c2pa-python",
                           method="pure-python JUMBF scan")]
        _load_trust()
        try:
            reader = c2pa.Reader(ctx.path)
        except Exception as e:
            msg = str(e)
            absent = "ManifestNotFound" in msg or "no JUMBF" in msg or "manifest not found" in msg.lower() or "not found" in msg.lower()
            if absent or structure is None:
                return [Signal(kind="c2pa", name="Content Credentials (C2PA)", status="absent", evidence_grade="none",
                               summary="No C2PA manifest embedded. Absence is NOT evidence of human origin — "
                                       "most upload pipelines and screenshots strip metadata.",
                               data={"structure": structure, "sdk_error": None if absent else msg},
                               method=f"c2pa-python {getattr(c2pa, '__version__', '')} / c2pa-rs {c2pa.sdk_version()}")]
            return [Signal(kind="c2pa", name="Content Credentials (C2PA)", status="error", summary=f"SDK error: {msg[:200]}",
                           data={"structure": structure}, method="c2pa-python")]

        store = json.loads(reader.json())
        state = reader.get_validation_state() or "Unknown"
        results = reader.get_validation_results() or {}
        remote = None
        try:
            remote = reader.get_remote_url()
        except Exception:
            pass
        manifests = store.get("manifests", {})
        active_label = store.get("active_manifest")
        summaries = {lab: _summarise_manifest(lab, m) for lab, m in manifests.items()}
        active = summaries.get(active_label) or (next(iter(summaries.values())) if summaries else None)

        codes = {"success": [], "informational": [], "failure": []}
        am = results.get("activeManifest") or {}
        for k in codes:
            codes[k] = [{"code": x.get("code"), "explanation": x.get("explanation")} for x in am.get(k, [])]
        failure_codes = [c["code"] for c in codes["failure"]]
        modified_after_signing = any("dataHash.mismatch" in (c or "") or "hash.mismatch" in (c or "") or "bmffHash" in (c or "") for c in failure_codes)
        signer_untrusted = any("untrusted" in (c or "") for c in failure_codes)

        classes = active["dst_classes"] if active else []
        if "ai_generated" in classes:
            prov = "ai_generated_declared"
        elif "ai_assisted" in classes:
            prov = "ai_assisted_declared"
        elif "captured" in classes:
            prov = "captured_declared"
        elif classes:
            prov = classes[0] + "_declared"
        else:
            prov = "signed_no_source_type"

        if state == "Trusted":
            grade = "strong"
        elif state == "Valid":
            grade = "moderate"
        else:
            grade = "none"
        if modified_after_signing:
            grade = "none"

        if modified_after_signing:
            summary = "Manifest present but the asset bytes no longer match the signed hash — modified after signing (or spliced)."
        elif state == "Trusted":
            summary = f"Valid Content Credential signed by {active['signer']['issuer'] or 'unknown'} (certificate chains to a configured trust anchor)."
        elif state == "Valid":
            summary = f"Signature verifies ({active['signer']['issuer'] or 'unknown issuer'}) but the signer is NOT on the configured trust list — treat as 'valid, unverified identity'."
        else:
            summary = f"Manifest present but validation state is {state}."
        if active and active["actions"]:
            desc = [a["description"] for a in active["actions"] if a.get("description")]
            if desc:
                summary += " Declares: " + "; ".join(dict.fromkeys(desc)) + "."

        details = None
        try:
            details = json.loads(reader.detailed_json())
            # keep it compact: drop thumbnails
            for m in details.get("manifests", {}).values():
                for k, v in list((m.get("assertion_store") or {}).items()):
                    if isinstance(v, str) and v.startswith("<omitted>"):
                        m["assertion_store"][k] = v
        except Exception:
            pass

        return [Signal(kind="c2pa", name="Content Credentials (C2PA)", status="detected", evidence_grade=grade,
                       summary=summary,
                       data={"validation_state": state, "provenance_class": prov, "active_manifest": active_label,
                             "manifest_count": len(manifests), "active": active, "manifests": summaries,
                             "validation_codes": codes, "modified_after_signing": modified_after_signing,
                             "signer_untrusted": signer_untrusted, "remote_manifest_url": remote,
                             "trust_sources": _trust_loaded["sources"], "structure": structure,
                             "detailed": details},
                       method=f"c2pa-python / c2pa-rs {c2pa.sdk_version()} + pure-python JUMBF walker")]


def sign_file(src: str, dst: str, manifest: dict, mime: str | None = None, ingredient: tuple[dict, str, str] | None = None) -> bytes:
    """Sign an asset with the DEMO certificate (used by tools/make_demo_assets.py and the /sign demo).
    MANUAL INTEGRATION for production: real certificate + TSA + KMS-backed key."""
    if not HAVE_SDK:
        raise RuntimeError("c2pa-python not installed")
    certs = config.DEMO_CHAIN_PEM.read_bytes()
    key = config.DEMO_SIGNER_KEY_PEM.read_bytes()
    signer = c2pa.Signer.from_info(c2pa.C2paSignerInfo(alg=b"es256", sign_cert=certs, private_key=key, ta_url=None))
    builder = c2pa.Builder(manifest)
    if ingredient:
        ing_json, ing_mime, ing_path = ingredient
        with open(ing_path, "rb") as f:
            builder.add_ingredient(ing_json, ing_mime, f)
    return builder.sign_file(src, dst, signer)
