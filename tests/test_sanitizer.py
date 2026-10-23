"""Phase 1 sanitizer tests: lossless metadata/C2PA removal + verify for JPEG, PNG, WebP."""
import io
import pathlib
import struct
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app import config, db  # noqa: E402
from app.sanitizer import image as san  # noqa: E402
from app.main import app  # noqa: E402

DEMO = config.DEMO_DIR
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _db():
    db.init_db()


def _demo(name: str) -> bytes:
    p = DEMO / name
    if not p.exists():
        pytest.skip("demo assets not generated (run tools/make_demo_assets.py)")
    return p.read_bytes()


def test_jpeg_strip_removes_c2pa_exif_xmp_losslessly():
    data = _demo("camera_capture_signed.jpg")
    before = san.inspect_bytes(data)
    assert before["c2pa"] and before["exif"]

    out, rep = san.sanitize_bytes(data, "x.jpg")
    after = san.inspect_bytes(out)

    assert not after["c2pa"] and not after["exif"] and not after["xmp"] and not after["iptc"]
    assert rep["verify"]["verdict"] == "clean"
    assert rep["verify"]["residual"] == {}
    assert rep["lossless"] is True
    assert rep["pixels_identical"] is True

    i0, i1 = Image.open(io.BytesIO(data)), Image.open(io.BytesIO(out))
    assert i0.size == i1.size and i0.mode == i1.mode


def test_jpeg_strip_removes_xmp_app1():
    base = _demo("plain_photo_like.jpg")
    xmp = b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF/></x:xmpmeta>'
    app1 = b"\xff\xe1" + struct.pack(">H", 2 + len(xmp)) + xmp
    data = base[:2] + app1 + base[2:]
    assert san.inspect_bytes(data)["xmp"] is True

    out, rep = san.sanitize_bytes(data, "x.jpg")
    assert not san.inspect_bytes(out)["xmp"]
    assert rep["verify"]["verdict"] == "clean"
    assert rep["pixels_identical"] is True


def test_png_strip_removes_text_chunks():
    data = _demo("a1111_parameters.png")
    before = san.inspect_bytes(data)
    assert before["text_chunks"] > 0

    out, rep = san.sanitize_bytes(data, "x.png")
    after = san.inspect_bytes(out)

    assert after["text_chunks"] == 0 and not after["c2pa"]
    assert rep["verify"]["verdict"] == "clean"
    assert rep["pixels_identical"] is True


def test_png_strip_removes_c2pa():
    data = _demo("sdxl_watermarked.png")
    out, rep = san.sanitize_bytes(data, "x.png")
    assert not san.inspect_bytes(out)["c2pa"]
    assert rep["verify"]["verdict"] == "clean"


def test_webp_strip_removes_exif_chunk():
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (10, 20, 30)).save(buf, "WEBP")
    base = buf.getvalue()
    exif_payload = b"Exif\x00\x00" + b"II*\x00" + b"\x00" * 4
    exif_chunk = b"EXIF" + struct.pack("<I", len(exif_payload)) + exif_payload
    if len(exif_payload) & 1:
        exif_chunk += b"\x00"
    body = base[12:] + exif_chunk
    data = b"RIFF" + struct.pack("<I", 4 + len(body)) + b"WEBP" + body
    assert san.inspect_bytes(data)["exif"] is True

    out, rep = san.sanitize_bytes(data, "x.webp")
    assert not san.inspect_bytes(out)["exif"]
    assert rep["verify"]["verdict"] == "clean"


def test_idempotent():
    data = _demo("ai_generated_signed.jpg")
    out1, _ = san.sanitize_bytes(data, "x.jpg")
    out2, _ = san.sanitize_bytes(out1, "x.jpg")
    assert out1 == out2


def test_unsupported_format():
    with pytest.raises(san.UnsupportedFormat):
        san.sanitize_bytes(b"just some text", "x.txt")


def test_api_sanitize_detect_and_download():
    data = _demo("camera_capture_signed.jpg")

    d = client.post("/v1/detect", files={"file": ("x.jpg", data, "image/jpeg")}).json()
    assert d["inspection"]["c2pa"] and d["inspection"]["exif"]

    r = client.post("/v1/sanitize", files={"file": ("x.jpg", data, "image/jpeg")},
                    data={"keep_icc": "true", "reencode": "false"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["verify"]["verdict"] == "clean" and j["download_url"].startswith("/v1/sanitize/")

    got = client.get(j["download_url"])
    assert got.status_code == 200 and got.content[:2] == b"\xff\xd8"
    assert not san.inspect_bytes(got.content)["c2pa"]

    job = client.get(f"/v1/sanitize/{j['job_id']}").json()
    assert job["status"] == "done" and job["report"]["verify"]["verdict"] == "clean"


def test_sanitize_page_and_unsupported_api():
    assert client.get("/sanitize").status_code == 200
    r = client.post("/v1/sanitize", files={"file": ("x.txt", b"hello", "text/plain")})
    assert r.status_code == 415
