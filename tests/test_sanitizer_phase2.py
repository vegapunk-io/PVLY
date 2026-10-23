"""Phase 2 sanitizer tests: PDF (pikepdf) and DOCX (zipfile + lxml)."""
import io
import pathlib
import sys
import zipfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app import db  # noqa: E402
from app.sanitizer import docx as docxmod  # noqa: E402
from app.sanitizer import image as san  # noqa: E402
from app.sanitizer import pdf as pdfmod  # noqa: E402
from app.main import app  # noqa: E402

pikepdf = pytest.importorskip("pikepdf")
client = TestClient(app)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


@pytest.fixture(scope="session", autouse=True)
def _db():
    db.init_db()


def _jpeg_with_exif() -> bytes:
    img = Image.new("RGB", (8, 8), (200, 10, 10))
    ex = Image.Exif()
    ex[0x010F] = "SecretCam"
    ex[0x0110] = "SecretModel"
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=ex)
    return buf.getvalue()


def _pdf_bytes(attachment: bool = True) -> bytes:
    p = pikepdf.new()
    p.add_blank_page(page_size=(200, 200))
    p.docinfo["/Author"] = "Jane Doe"
    p.docinfo["/Title"] = "Secret Title"
    with p.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta["dc:title"] = "Secret Title"
        meta["xmp:CreatorTool"] = "SecretTool"
    if attachment:
        p.attachments["secret.txt"] = pikepdf.AttachedFileSpec(
            p, b"hidden payload", mime_type="text/plain")
    buf = io.BytesIO()
    p.save(buf)
    p.close()
    return buf.getvalue()


def _docx_bytes() -> bytes:
    parts = {}
    parts["[Content_Types].xml"] = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="jpg" ContentType="image/jpeg"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
<Override PartName="/docProps/custom.xml" ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/>
</Types>'''
    parts["_rels/.rels"] = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties" Target="docProps/custom.xml"/>
</Relationships>'''
    parts["word/_rels/document.xml.rels"] = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.jpg"/>
</Relationships>'''
    parts["word/document.xml"] = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}"><w:body><w:p>
<w:r><w:t>Hello </w:t></w:r>
<w:ins w:id="1" w:author="Alice" w:date="2020-01-01T00:00:00Z"><w:r><w:t>INSERTED</w:t></w:r></w:ins>
<w:del w:id="2" w:author="Alice" w:date="2020-01-01T00:00:00Z"><w:r><w:delText>DELETED</w:delText></w:r></w:del>
<w:commentRangeStart w:id="0"/><w:r><w:t> reviewed</w:t></w:r><w:commentRangeEnd w:id="0"/>
<w:r><w:commentReference w:id="0"/></w:r>
<w:r><w:rPr><w:b/><w:rPrChange w:id="9" w:author="Alice"><w:rPr/></w:rPrChange></w:rPr><w:t>!</w:t></w:r>
</w:p><w:sectPr/></w:body></w:document>'''.encode()
    parts["word/comments.xml"] = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W}"><w:comment w:id="0" w:author="Bob" w:initials="B"><w:p><w:r><w:t>secret comment</w:t></w:r></w:p></w:comment></w:comments>'''.encode()
    parts["docProps/core.xml"] = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>Secret Title</dc:title><dc:creator>Jane Doe</dc:creator><cp:lastModifiedBy>John Roe</cp:lastModifiedBy><cp:revision>7</cp:revision>
<dcterms:created xsi:type="dcterms:W3CDTF">2020-01-01T00:00:00Z</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">2020-02-01T00:00:00Z</dcterms:modified>
</cp:coreProperties>'''
    parts["docProps/app.xml"] = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
<Company>Acme Corp</Company><Manager>Boss</Manager><Application>Word</Application></Properties>'''
    parts["docProps/custom.xml"] = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
<property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="2" name="Secret"><vt:lpwstr>hidden</vt:lpwstr></property></Properties>'''
    parts["word/media/image1.jpg"] = _jpeg_with_exif()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in parts.items():
            z.writestr(n, b)
    return buf.getvalue()


def test_pdf_strip_info_xmp_and_attachments():
    data = _pdf_bytes()
    before = san.inspect_bytes(data)
    assert before["format"] == "pdf"
    assert before["info"] and before["xmp"] is True
    assert before["attachments"] == ["secret.txt"]

    out, rep = san.sanitize_bytes(data, "x.pdf")
    after = san.inspect_bytes(out)

    assert after["info"] == {}
    assert after["xmp"] is False and after["attachments"] == []
    assert after["pages"] == 1
    assert rep["verify"]["verdict"] == "clean"
    assert rep["verify"]["residual"] == {}
    assert rep["lossless"] is False
    assert out[:4] == b"%PDF"


def test_pdf_password_protected_is_rejected():
    p = pikepdf.new()
    p.add_blank_page(page_size=(100, 100))
    buf = io.BytesIO()
    p.save(buf, encryption=pikepdf.Encryption(owner="owner", user="user", R=6))
    p.close()
    with pytest.raises(san.UnsupportedFormat):
        san.sanitize_bytes(buf.getvalue(), "locked.pdf")


def test_docx_strip_properties_comments_and_tracked_changes():
    data = _docx_bytes()
    before = san.inspect_bytes(data)
    assert before["format"] == "docx"
    assert before["core"]["creator"] == "Jane Doe"
    assert before["app"]["company"] == "Acme Corp"
    assert before["comments"] is True
    assert before["custom_properties"] is True
    assert before["tracked_changes"]["ins"] == 1 and before["tracked_changes"]["del"] == 1
    assert before["media_metadata"] is True

    out, rep = san.sanitize_bytes(data, "x.docx")
    after = san.inspect_bytes(out)

    assert after["core"] == {}
    assert "company" not in after["app"] and "manager" not in after["app"]
    assert after["comments"] is False and after["custom_properties"] is False
    assert after["tracked_changes"] == {"ins": 0, "del": 0, "moveFrom": 0, "moveTo": 0}
    assert after["media_metadata"] is False
    assert rep["verify"]["verdict"] == "clean"
    assert rep["verify"]["residual"] == {}

    with zipfile.ZipFile(io.BytesIO(out)) as z:
        names = set(z.namelist())
        assert "word/comments.xml" not in names and "docProps/custom.xml" not in names
        doc = z.read("word/document.xml").decode("utf-8")
        assert "INSERTED" in doc and "DELETED" not in doc
        assert "w:ins" not in doc and "w:del" not in doc and "commentReference" not in doc
        assert "Alice" not in doc and "Bob" not in doc
        assert san.inspect_bytes(z.read("word/media/image1.jpg"))["exif"] is False
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "comments.xml" not in rels and "media/image1.jpg" in rels


def test_docx_detected_from_magic_not_extension():
    data = _docx_bytes()
    assert san.detect_format(data) == "docx"
    assert san.detect_format(data, "misleading.bin") == "docx"


def test_legacy_doc_is_rejected():
    with pytest.raises(san.UnsupportedFormat):
        san.sanitize_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 32, "x.doc")


def test_api_pdf_and_docx_roundtrip():
    pdf_data = _pdf_bytes()
    r = client.post("/v1/sanitize", files={"file": ("x.pdf", pdf_data, "application/pdf")})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["file"]["format"] == "pdf" and j["verify"]["verdict"] == "clean"
    got = client.get(j["download_url"])
    assert got.status_code == 200 and got.content[:4] == b"%PDF"
    assert pdfmod.inspect_pdf_bytes(got.content)["info"] == {}

    docx_data = _docx_bytes()
    d = client.post("/v1/detect", files={"file": ("x.docx", docx_data, "application/octet-stream")}).json()
    assert d["inspection"]["format"] == "docx" and d["inspection"]["comments"] is True

    r = client.post("/v1/sanitize", files={"file": ("x.docx", docx_data,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["file"]["format"] == "docx" and j["verify"]["verdict"] == "clean"
    got = client.get(j["download_url"])
    assert got.status_code == 200 and got.content[:2] == b"PK"
    assert docxmod.inspect_docx_bytes(got.content)["comments"] is False
