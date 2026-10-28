"""Security-focused smoke tests."""
import pathlib

import pytest

from fastapi.testclient import TestClient

from app import config, db, pipeline
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _db():
    db.init_db()


def test_ssrf_loopback_blocked():
    r = client.post("/v1/scans", data={"url": "http://127.0.0.1:1/x"})
    assert r.status_code == 400


def test_ssrf_private_ip_blocked():
    r = client.post("/v1/scans", data={"url": "http://10.0.0.1/x"})
    assert r.status_code == 400


def test_ssrf_non_http_scheme_blocked():
    r = client.post("/v1/scans", data={"url": "file:///etc/passwd"})
    assert r.status_code == 400


def test_empty_upload_rejected():
    r = client.post("/v1/scans", files={"file": ("empty.txt", b"", "text/plain")})
    assert r.status_code == 400


def test_demo_asset_path_traversal():
    r = client.get("/demo-assets/..%2F..%2Fetc%2Fpasswd")
    assert r.status_code in (400, 404)


def test_official_trust_list_loaded():
    caps = client.get("/v1/capabilities").json()
    assert caps["manual_integration"]["official_c2pa_trust_list"] is True


def test_auth_required_when_enabled(monkeypatch):
    import app.config as cfg
    monkeypatch.setattr(cfg, "API_KEYS", [])
    monkeypatch.setattr(cfg, "REQUIRE_AUTH", True)
    r = client.get("/v1/scans")
    assert r.status_code == 401


def test_rate_limit_applies_to_api_only(monkeypatch):
    import app.main as main
    monkeypatch.setattr(config, "RATE_LIMIT_PER_MINUTE", 2)
    main._rate_buckets.clear()
    assert client.get("/v1/capabilities").status_code == 200
    assert client.get("/v1/capabilities").status_code == 200
    r = client.get("/v1/capabilities")
    assert r.status_code == 429 and r.headers["retry-after"] == "60"
    assert "too quickly" in r.json()["detail"]
    # pages and assets are never limited, even once the API bucket is full
    for _ in range(5):
        assert client.get("/").status_code == 200
    main._rate_buckets.clear()


def test_forwarded_for_ignored_unless_proxy_trusted(monkeypatch):
    import app.main as main
    monkeypatch.setattr(config, "RATE_LIMIT_PER_MINUTE", 1)
    monkeypatch.setattr(config, "TRUST_PROXY_HEADERS", False)
    main._rate_buckets.clear()
    assert client.get("/v1/capabilities", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert client.get("/v1/capabilities", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 429
    main._rate_buckets.clear()
    monkeypatch.setattr(config, "TRUST_PROXY_HEADERS", True)
    assert client.get("/v1/capabilities", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert client.get("/v1/capabilities", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 200
    main._rate_buckets.clear()


def test_health_not_rate_limited():
    for _ in range(5):
        assert client.get("/health").status_code == 200


def test_metrics_endpoint():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "provenably_requests_total" in r.text


def test_request_id_header():
    r = client.get("/health")
    assert "x-request-id" in {k.lower() for k in r.headers}


def test_removal_requires_attestation():
    r = client.post("/v1/remove", params={"scan_id": "x", "attested": "true"})
    assert r.status_code in (400, 404)


def test_removal_requires_attested_flag():
    r = client.post("/v1/remove", params={"scan_id": "x"})
    assert r.status_code == 400


def test_report_preview_requires_existing_scan():
    r = client.get("/v1/scans/doesnotexist/preview.jpg")
    assert r.status_code == 404