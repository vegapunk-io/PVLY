"""R0 Layer-1 removal tests."""
import hashlib
import io
import pathlib

import pytest
from PIL import Image

from app import config, db, pipeline, removal
from app.analyzers import metadata_an

DEMO = config.DEMO_DIR


@pytest.fixture(scope="session", autouse=True)
def _db():
    db.init_db()


def _hash(b):
    return hashlib.sha256(b).hexdigest()


_AI_MANIFEST = {
    "claim_generator_info": [{"name": "ChatGPT", "version": "1"}],
    "title": "x",
    "assertions": [{"label": "c2pa.actions", "data": {"actions": [{
        "action": "c2pa.created",
        "digitalSourceType": "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"}]}}],
}


def _make_source(path: pathlib.Path, ext: str) -> None:
    import shutil, subprocess
    img = Image.new("RGB", (64, 64), (200, 30, 30))
    exif = Image.Exif()
    exif[0x0131] = "Midjourney v7"
    exif[0x010F] = "AI Corp"
    if ext == "heic":
        if not shutil.which("sips"):
            pytest.skip("no HEIC encoder (macOS sips) available")
        tiff = path.with_suffix(".tiff")
        img.save(tiff, "TIFF", exif=exif)
        subprocess.run(["sips", "-s", "format", "heic", str(tiff), "--out", str(path)], check=True, capture_output=True)
        return
    fmt = {"png": "PNG", "webp": "WEBP", "jpg": "JPEG", "avif": "AVIF", "gif": "GIF", "tiff": "TIFF"}[ext]
    kwargs = {} if ext in ("png", "gif") else {"exif": exif}
    img.save(path, fmt, **kwargs)


@pytest.mark.parametrize("ext", ["png", "webp", "jpg", "heic", "avif", "gif", "tiff"])
def test_c2pa_removed_from_every_image_format(tmp_path, ext):
    """Real C2PA-signed files: the manifest and generator strings must be gone, pixels identical."""
    from app.analyzers import c2pa_an
    src, signed, clean = tmp_path / f"in.{ext}", tmp_path / f"signed.{ext}", tmp_path / f"clean.{ext}"
    _make_source(src, ext)
    c2pa_an.sign_file(str(src), str(signed), _AI_MANIFEST)
    data = signed.read_bytes()
    assert pipeline.analyze_bytes_sync(data, signed.name)["conclusion"]["provenance_class"] == "ai_generated_declared"

    cleaned, fields = removal._strip_for_modality("image", f"image/{ext}", data, signed.name)
    clean.write_bytes(cleaned)
    assert fields, "stripper reported nothing removed from a signed file"
    removal._validate_decodes("image", "", cleaned, clean.name)

    after = removal._rescan_summary(cleaned, clean.name)
    assert after["layer1_present"] == []
    assert after["provenance_class"] != "ai_generated_declared"
    for leaked in (b"Midjourney", b"AI Corp", b"ChatGPT"):
        assert leaked not in cleaned, f"{leaked!r} survived in {ext}"
    assert list(Image.open(io.BytesIO(data)).convert("RGB").getdata()) == list(Image.open(clean).convert("RGB").getdata())

    again, fields2 = removal._strip_for_modality("image", "", cleaned, clean.name)
    assert again == cleaned and fields2 == [], "removal must be idempotent"


def test_routing_uses_content_not_extension(tmp_path):
    """A HEIC renamed to .jpg must still go through the HEIF stripper."""
    from app.analyzers import c2pa_an
    src, signed = tmp_path / "in.avif", tmp_path / "signed.avif"
    _make_source(src, "avif")
    c2pa_an.sign_file(str(src), str(signed), _AI_MANIFEST)
    _, fields = removal._strip_for_modality("image", "image/jpeg", signed.read_bytes(), "photo.jpg")
    assert "heif:C2PA" in fields


@pytest.mark.parametrize("stripper,blob", [
    ("_strip_heif", b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00\x00\x00\x08meta"),
    ("_strip_heif", b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\xff\xff\xff\xffmeta"),
    ("_strip_gif", b"GIF89a" + b"\x01\x00\x01\x00\x00\x00\x00" + b"\x21\xff\x0bC2PA_GIF"),
    ("_strip_tiff", b"II*\x00" + b"\xff\xff\xff\x7f"),
])
def test_malformed_input_fails_safely(stripper, blob):
    with pytest.raises(removal.RemovalError):
        getattr(removal, stripper)(blob)


def test_jpeg_lossless_pixels():
    p = DEMO / "ai_generated_signed.jpg"
    if not p.exists():
        pytest.skip("demo assets missing")
    data = p.read_bytes()
    cleaned, fields = removal._strip_jpeg(data)
    # pixel data identical: compare decoded pixels
    a = Image.open(io.BytesIO(data))
    b = Image.open(io.BytesIO(cleaned))
    assert a.size == b.size
    assert list(a.getdata()) == list(b.getdata())
    assert any(f.startswith("jpeg:") for f in fields)


def test_jpeg_no_metadata_after():
    p = DEMO / "ai_generated_signed.jpg"
    if not p.exists():
        pytest.skip("demo assets missing")
    data = p.read_bytes()
    cleaned, _ = removal._strip_jpeg(data)
    # no APP1/APP13/APP14 markers remain
    i = 2
    n = len(cleaned)
    markers = []
    while i < n:
        if cleaned[i] != 0xFF:
            break
        while i < n and cleaned[i] == 0xFF:
            i += 1
        if i >= n:
            break
        m = cleaned[i]
        i += 1
        if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
            if m == 0xD9:
                break
            continue
        if i + 2 > n:
            break
        seg_len = int.from_bytes(cleaned[i:i+2], "big")
        if m in (0xE1, 0xED, 0xEE):
            markers.append(m)
        i += seg_len
        if m == 0xDA:
            break
    assert markers == [], "metadata APP segments remain"


def test_png_lossless():
    p = DEMO / "sdxl_watermarked.png"
    if not p.exists():
        pytest.skip("demo assets missing")
    data = p.read_bytes()
    cleaned, fields = removal._strip_png(data)
    a = Image.open(io.BytesIO(data))
    b = Image.open(io.BytesIO(cleaned))
    assert a.size == b.size
    assert list(a.getdata()) == list(b.getdata())


def test_attestation_required():
    with pytest.raises(removal.RemovalError):
        removal.remove_layer1("nonexistent", attested=False)


def test_scan_not_found():
    with pytest.raises(removal.RemovalError):
        removal.remove_layer1("doesnotexist", attested=True)


def test_full_image_removal_flow():
    p = DEMO / "ai_generated_signed.jpg"
    if not p.exists():
        pytest.skip("demo assets missing")
    # create scan
    sid = pipeline.new_scan_from_bytes(p.read_bytes(), p.name)
    pipeline.run_scan(sid)
    res = removal.remove_layer1(sid, attested=True)
    assert res.status == "done"
    assert res.input_sha256 != res.output_sha256
    assert res.output_blob_path and pathlib.Path(res.output_blob_path).exists()
    assert res.fields_removed
    # re-scan output has no C2PA manifest (or at least metadata stripped)
    out_bytes = pathlib.Path(res.output_blob_path).read_bytes()
    assert _hash(out_bytes) == res.output_sha256
    # Layer-2 disclaimer present
    assert "Layer-1" in res.layer2_disclaimer
    assert "Layer-2" in res.layer2_disclaimer


def test_docx_strip():
    import zipfile, io
    # build a minimal docx with docProps
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", "<document/>")
        z.writestr("docProps/core.xml", "<core/>")
    data = buf.getvalue()
    cleaned, fields = removal._strip_docx(data)
    assert "docx:docProps/core.xml" in fields
    z = zipfile.ZipFile(io.BytesIO(cleaned))
    assert "docProps/core.xml" not in z.namelist()


def test_text_strip():
    dirty = "Re\u200bvenue"
    data = dirty.encode()
    cleaned, fields = removal._strip_text(data)
    assert cleaned == b"Revenue"
    assert fields == ["text:unicode_hygiene"]


def test_pdf_strip_removes_metadata():
    import io
    from pypdf import PdfWriter, PdfReader
    w = PdfWriter()
    w.add_blank_page(width=100, height=100)
    w.add_metadata({"/Title": "AI generated"})
    buf = io.BytesIO()
    w.write(buf)
    data = buf.getvalue()
    cleaned, fields = removal._strip_pdf(data)
    assert "pdf:metadata" in fields
    r = PdfReader(io.BytesIO(cleaned))
    md = r.metadata or {}
    assert "/Title" not in md


def test_video_removal_flow():
    import shutil
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not installed")
    p = DEMO / "clip_signed.mp4"
    if not p.exists():
        pytest.skip("demo assets missing")
    sid = pipeline.new_scan_from_bytes(p.read_bytes(), p.name)
    pipeline.run_scan(sid)
    res = removal.remove_layer1(sid, attested=True)
    assert res.status == "done"
    assert res.modality == "video"
    assert res.fields_removed
    out = pathlib.Path(res.output_blob_path).read_bytes()
    assert _hash(out) == res.output_sha256


def test_batch_removal_flow():
    import shutil
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not installed")
    p = DEMO / "ai_generated_signed.jpg"
    if not p.exists():
        pytest.skip("demo assets missing")
    sid = pipeline.new_scan_from_bytes(p.read_bytes(), p.name)
    pipeline.run_scan(sid)
    bid = "testbatch" + sid[:6]
    db.create_batch(bid, [sid], "generic", True)
    removal.run_batch(bid, [sid], "generic", True)
    row = db.get_batch(bid)
    assert row["status"] == "done"
    assert row["output_blob_path"]
    import zipfile
    z = zipfile.ZipFile(row["output_blob_path"])
    assert "manifest.json" in z.namelist()