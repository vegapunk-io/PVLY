"""Smoke tests: run with `pytest -q` from the repo root (demo assets must exist: python tools/make_demo_assets.py)."""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, db, pipeline  # noqa: E402
from app.analyzers import text_an  # noqa: E402
from app.main import app  # noqa: E402
from app.rules import engine  # noqa: E402

DEMO = config.DEMO_DIR
EXPECTED = {
    "ai_generated_signed.jpg": ("ai_generated_declared", "strong"),
    "camera_capture_signed.jpg": ("captured_declared", "strong"),
    "ai_edited_composite_signed.jpg": ("ai_assisted_declared", "strong"),
    "ai_generated_tampered.jpg": ("tampered_after_signing", "strong"),
    "ai_generated_stripped.jpg": ("no_provenance_signal", "none"),
    "iptc_ai_tagged_no_c2pa.jpg": ("ai_generated_metadata", "weak"),
    "a1111_parameters.png": ("ai_generated_metadata", "weak"),
    "sdxl_watermarked.png": ("ai_generated_watermark", "moderate"),
    "sdxl_watermarked_q75.jpg": ("no_provenance_signal", "none"),
    "text_hidden_chars.txt": ("text_hidden_characters", "weak"),
    "speech_like_signed.wav": ("ai_generated_declared", "strong"),
    "clip_signed.mp4": ("ai_generated_declared", "strong"),
}

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _db():
    db.init_db()


@pytest.mark.parametrize("name,expected", EXPECTED.items())
def test_pipeline_conclusions(name, expected):
    p = DEMO / name
    if not p.exists():
        pytest.skip("demo assets not generated")
    rep = pipeline.analyze_bytes_sync(p.read_bytes(), name)
    assert (rep["conclusion"]["provenance_class"], rep["conclusion"]["evidence_grade"]) == expected
    assert rep["coverage"]["errors"] == 0
    assert all(s["status"] in ("detected", "absent", "info", "inconclusive", "skipped", "not_installed", "not_configured") for s in rep["signals"])


def test_greenlist_roundtrip():
    toks = text_an.greenlist_generate("k", n=300)
    assert text_an.greenlist_zscore(toks, "k")["z"] > 4
    assert text_an.greenlist_zscore(toks, "wrong")["z"] < 3


def test_unicode_clean():
    dirty = "Re\u200bvenue bo\u00adard N\u043evember"
    assert text_an.scan_unicode(dirty)["count"] == 3
    assert text_an.clean_unicode(dirty) == "Revenue board November"


def test_disclosure_engine():
    r = engine.disclosure_check(content_type="image", is_ai_generated=True, depicts_real_person=True)
    assert r["open_items"] >= 4
    r2 = engine.disclosure_check(content_type="image", is_ai_generated=True, has_c2pa=True, has_visible_label=True, has_metadata_id=True)
    assert r2["open_items"] == 0
    r3 = engine.disclosure_check(content_type="image", is_ai_generated=False)
    assert r3["open_items"] == 0 and not r3["synthetic"]


def test_platform_label_research_contract():
    platforms = {p["slug"]: p for p in engine.PLATFORMS}
    expected_labels = {
        "instagram": "AI info",
        "facebook": "AI info",
        "threads": "AI info",
        "youtube": "Made with AI",
        "tiktok": "AI-generated",
        "linkedin": "cr pin (Content Credentials)",
        "pinterest": "AI modified",
        "reddit": "No site-wide AI label",
        "x": "Made with AI",
        "google_search": "About this image provenance",
        "amazon_kdp": "No public reader label specified",
    }
    assert expected_labels.items() <= {slug: p["label_text"] for slug, p in platforms.items()}.items()
    for platform in platforms.values():
        assert platform["label_subtext"]
        assert platform["detection_summary"]
        assert platform["metadata_signals"]
        assert platform["creator_duty"]
        assert platform["last_verified"] == "2026-10-24"
        assert platform["sources"] and all(source.startswith("https://") for source in platform["sources"])

    assert "c2pa_ai" not in platforms["pinterest"]["auto_label_triggers"]
    assert platforms["x"]["confidence"] == "medium"

    preview = {
        p["slug"]: p
        for p in engine.platform_preview(
            {"c2pa_ai": True, "c2pa_any": True, "iptc_ai": True, "vendor_watermark": False}
        )
    }
    assert preview["instagram"]["likely_label"] == "yes"
    assert preview["youtube"]["likely_label"] == "yes"
    assert preview["linkedin"]["likely_label"] == "yes"
    assert preview["pinterest"]["likely_label"] == "yes"
    assert preview["reddit"]["likely_label"] == "no"
    assert preview["reddit"]["sources"]
    assert preview["reddit"]["metadata_signals"]


def test_api_flow():
    assert client.get("/health").json()["ok"]
    for path in ("/", "/demo", "/registry", "/laws", "/tools", "/lab", "/docs-guide", "/registry/openai-gpt-image"):
        assert client.get(path).status_code == 200, path
    r = client.post("/v1/scans", data={"text": "hello\u200b world " * 30, "wait": "true"})
    assert r.status_code == 200 and r.json()["conclusion"]["provenance_class"] == "text_hidden_characters"
    r = client.post("/v1/scans", data={"url": "http://127.0.0.1:1/x"})
    assert r.status_code == 400
    r = client.post("/v1/disclosure/check", json={"content_type": "video", "is_ai_generated": True})
    assert r.status_code == 200 and r.json()["open_items"] > 0
    r = client.post("/v1/lab/greenlist", json={"action": "generate", "key": "x", "n": 200})
    assert r.json()["stats"]["verdict"] == "watermark"
    caps = client.get("/v1/capabilities").json()
    assert caps["live"]["c2pa_validation"] is True


def test_sniff():
    assert pipeline.sniff(b"\xff\xd8\xff\xe0" + b"\0" * 60, "x") == ("image/jpeg", "image")
    assert pipeline.sniff(b"RIFF\0\0\0\0WAVEfmt " + b"\0" * 48, "x") == ("audio/wav", "audio")
    assert pipeline.sniff(b"\0\0\0\x18ftypmp42" + b"\0" * 52, "x") == ("video/mp4", "video")
    assert pipeline.sniff(b"plain words", "notes.txt") == ("text/plain", "text")


def test_detect_only_surface():
    """Product wedge = Detect (founder decision 2026-10-24): no sanitizer anywhere."""
    assert client.get("/").status_code == 200
    assert client.get("/scan").status_code == 200
    for method, path in [("get", "/sanitize"), ("get", "/v1/sanitize"),
                         ("post", "/v1/sanitize"), ("post", "/v1/detect")]:
        assert getattr(client, method)(path).status_code == 404, (method, path)
    caps = client.get("/v1/capabilities").json()
    assert not any("sanitize" in k for k in caps["live"])
