"""DOCX sanitizer (Phase 2) using zipfile + lxml.

Word .docx is a ZIP of XML parts. This removes:
  - core properties (author, last modified by, title, revision, created/modified)
  - extended properties (company, manager)
  - custom properties part
  - comments / people parts (and their content-type + relationship entries)
  - tracked changes (w:ins / w:moveTo unwrapped, w:del / w:moveFrom deleted)
  - formatting-change records (w:*PrChange)
  - metadata inside embedded JPEG/PNG/WebP media

Legacy binary .doc is NOT supported (returns UnsupportedFormat -> HTTP 415).
"""
from __future__ import annotations

import hashlib
import io
import logging
import zipfile
from dataclasses import asdict

from lxml import etree

from . import image
from .image import SUPPORTED_MIME, SanitizePolicy, UnsupportedFormat, _coerce_policy

log = logging.getLogger(__name__)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
DCTERMS = "http://purl.org/dc/terms/"
APP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"

DROP_PARTS = [
    "docProps/custom.xml",
    "word/comments.xml",
    "word/commentsExtended.xml",
    "word/commentsIds.xml",
    "word/commentsExtensible.xml",
    "word/people.xml",
]
CORE_PERSONAL = ("creator", "last_modified_by", "revision", "title", "subject",
                 "keywords", "description", "category", "created", "modified")
MEDIA_EXT = (".jpg", ".jpeg", ".png", ".webp")

MINIMAL_CORE = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
    'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    '<dc:title></dc:title><dc:creator></dc:creator><cp:lastModifiedBy></cp:lastModifiedBy>'
    '</cp:coreProperties>'
).encode("utf-8")

MINIMAL_APP = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    '<Application>Provenably</Application></Properties>'
).encode("utf-8")


def _to_xml(root) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _open_zip(data: bytes) -> zipfile.ZipFile:
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except Exception as e:
        raise UnsupportedFormat(f"not a readable .docx (zip): {e}")
    names = set(z.namelist())
    if "word/document.xml" not in names:
        z.close()
        raise UnsupportedFormat("not a Word .docx (missing word/document.xml); legacy .doc is not supported")
    return z


def _text(root, ns: str, tag: str) -> str:
    el = root.find(f"{{{ns}}}{tag}")
    return (el.text or "").strip() if el is not None else ""


def _core_info(z: zipfile.ZipFile, names: set[str]) -> dict:
    if "docProps/core.xml" not in names:
        return {}
    try:
        root = etree.fromstring(z.read("docProps/core.xml"))
    except Exception:
        return {}
    fields = {
        "creator": _text(root, DC, "creator"),
        "last_modified_by": _text(root, CP, "lastModifiedBy"),
        "revision": _text(root, CP, "revision"),
        "title": _text(root, DC, "title"),
        "subject": _text(root, DC, "subject"),
        "keywords": _text(root, CP, "keywords"),
        "description": _text(root, DC, "description"),
        "category": _text(root, CP, "category"),
        "created": _text(root, DCTERMS, "created"),
        "modified": _text(root, DCTERMS, "modified"),
    }
    return {k: v for k, v in fields.items() if v}


def _app_info(z: zipfile.ZipFile, names: set[str]) -> dict:
    if "docProps/app.xml" not in names:
        return {}
    try:
        root = etree.fromstring(z.read("docProps/app.xml"))
    except Exception:
        return {}
    fields = {
        "company": _text(root, APP, "Company"),
        "manager": _text(root, APP, "Manager"),
        "application": _text(root, APP, "Application"),
        "app_version": _text(root, APP, "AppVersion"),
    }
    return {k: v for k, v in fields.items() if v}


def _tracked(root) -> dict:
    stats = {}
    for tag in ("ins", "del", "moveFrom", "moveTo"):
        try:
            stats[tag] = len(list(root.iter(f"{{{W}}}{tag}")))
        except Exception:
            stats[tag] = 0
    return stats


def inspect_docx_bytes(data: bytes) -> dict:
    z = _open_zip(data)
    try:
        names = set(z.namelist())
        lower = {n.lower() for n in names}
        core = _core_info(z, names)
        app = _app_info(z, names)

        tracked = {"ins": 0, "del": 0, "moveFrom": 0, "moveTo": 0}
        for n in names:
            if not _is_text_part(n.lower()):
                continue
            try:
                part = etree.fromstring(z.read(n))
            except Exception:
                continue
            for k, v in _tracked(part).items():
                tracked[k] += v

        media = []
        media_meta = False
        for n in names:
            low = n.lower()
            if low.endswith("/"):
                continue
            if not (low.startswith("word/media/") or low.startswith("docprops/thumbnail.")):
                continue
            if not low.endswith(MEDIA_EXT):
                continue
            try:
                info = image.inspect_bytes(z.read(n))
            except Exception:
                continue
            has = bool(info.get("exif") or info.get("xmp") or info.get("c2pa")
                       or info.get("text_chunks") or info.get("timestamp"))
            media.append({"name": n, "format": info.get("format"), "metadata": has})
            media_meta = media_meta or has

        return {
            "format": "docx",
            "core": core,
            "app": app,
            "custom_properties": "docprops/custom.xml" in lower,
            "comments": "word/comments.xml" in lower,
            "tracked_changes": tracked,
            "media": media,
            "media_metadata": media_meta,
            "c2pa": False,
        }
    finally:
        z.close()


def _is_text_part(low_name: str) -> bool:
    if low_name in ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml"):
        return True
    return (low_name.startswith("word/header") or low_name.startswith("word/footer")) \
        and low_name.endswith(".xml")


def _clean_content_types(data: bytes, drop: set[str]) -> bytes:
    root = etree.fromstring(data)
    drop_parts = {("/" + n).lower() for n in drop}
    removed = 0
    for el in list(root):
        if el.tag == f"{{{CT}}}Override":
            part = (el.get("PartName") or "").lower()
            if part in drop_parts:
                root.remove(el)
                removed += 1
    return _to_xml(root) if removed else data


def _clean_rels(data: bytes) -> tuple[bytes, int]:
    root = etree.fromstring(data)
    drop_type = ("/comments", "/commentsextended", "/commentsids", "/commentsextensible",
                 "/people", "/custom-properties")
    drop_target = ("comments.xml", "commentsextended.xml", "commentsids.xml",
                   "commentsextensible.xml", "people.xml", "custom.xml")
    removed = 0
    for el in list(root):
        if el.tag != f"{{{REL}}}Relationship":
            continue
        rtype = (el.get("Type") or "").lower()
        target = (el.get("Target") or "").lower()
        if rtype.endswith(drop_type) or any(t in target for t in drop_target):
            root.remove(el)
            removed += 1
    return (_to_xml(root), removed) if removed else (data, 0)


def _clean_document(data: bytes) -> tuple[bytes, dict]:
    root = etree.fromstring(data)
    stats = {}

    for tag in ("del", "moveFrom"):
        els = list(root.iter(f"{{{W}}}{tag}"))
        for el in els:
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
        stats[tag] = len(els)

    for tag in ("ins", "moveTo"):
        els = list(root.iter(f"{{{W}}}{tag}"))
        for el in els:
            parent = el.getparent()
            if parent is None:
                continue
            idx = list(parent).index(el)
            for child in list(el):
                parent.insert(idx, child)
                idx += 1
            parent.remove(el)
        stats[tag] = len(els)

    change_tags = ("rPrChange", "pPrChange", "sectPrChange", "tblPrChange",
                   "trPrChange", "tcPrChange", "numberingChange")
    change_total = 0
    for tag in change_tags:
        els = list(root.iter(f"{{{W}}}{tag}"))
        for el in els:
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
        change_total += len(els)
    stats["property_changes"] = change_total

    comment_total = 0
    for tag in ("commentRangeStart", "commentRangeEnd", "commentReference"):
        els = list(root.iter(f"{{{W}}}{tag}"))
        for el in els:
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
        comment_total += len(els)
    stats["comment_refs"] = comment_total

    return _to_xml(root), stats


def _strip_media(raw: bytes, name: str, policy: SanitizePolicy) -> tuple[bytes, bool]:
    media_policy = SanitizePolicy(keep_icc=policy.keep_icc, reencode=False,
                                  keep_orientation=policy.keep_orientation)
    try:
        out, rep = image.sanitize_bytes(raw, name, media_policy)
    except Exception as e:
        log.debug("media sanitize failed for %s: %s", name, e)
        return raw, False
    return out, rep.get("verify", {}).get("verdict") == "clean"


def _residual(info: dict) -> dict:
    r = {}
    if any(info.get("core", {}).get(k) for k in CORE_PERSONAL):
        r["core_properties"] = True
    app = info.get("app", {})
    if app.get("company") or app.get("manager"):
        r["app_properties"] = True
    if info.get("custom_properties"):
        r["custom_properties"] = True
    if info.get("comments"):
        r["comments"] = True
    if any(info.get("tracked_changes", {}).values()):
        r["tracked_changes"] = True
    if info.get("media_metadata"):
        r["media_metadata"] = True
    if info.get("c2pa"):
        r["c2pa"] = True
    return r


def sanitize_docx_bytes(data: bytes, filename: str = "file",
                        policy: SanitizePolicy | dict | None = None) -> tuple[bytes, dict]:
    policy = _coerce_policy(policy)
    before = inspect_docx_bytes(data)
    warnings: list[str] = []
    removed: list[str] = []

    z = _open_zip(data)
    try:
        infos = z.infolist()
        lower_names = {i.filename.lower() for i in infos if not i.filename.endswith("/")}
        drop = {p for p in DROP_PARTS if p.lower() in lower_names}
        drop_lower = {d.lower() for d in drop}

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in infos:
                name = item.filename
                low = name.lower()
                if low in drop_lower:
                    removed.append(name)
                    continue
                raw = z.read(name)

                if low == "[content_types].xml":
                    raw = _clean_content_types(raw, drop)
                elif low.endswith(".rels"):
                    raw, n = _clean_rels(raw)
                    if n:
                        removed.append(f"relationship entries in {name}")
                elif low == "docprops/core.xml":
                    raw = MINIMAL_CORE
                    removed.append("core properties (author/title/dates/revision)")
                elif low == "docprops/app.xml":
                    raw = MINIMAL_APP
                    removed.append("extended properties (company/manager)")
                elif _is_text_part(low):
                    raw, stats = _clean_document(raw)
                    label = "document" if low == "word/document.xml" else name
                    if stats.get("del") or stats.get("moveFrom"):
                        removed.append(f"{label}: deleted text ({stats.get('del', 0) + stats.get('moveFrom', 0)})")
                    if stats.get("ins") or stats.get("moveTo"):
                        removed.append(f"{label}: tracked-change markup ({stats.get('ins', 0) + stats.get('moveTo', 0)})")
                    if stats.get("property_changes"):
                        removed.append(f"{label}: formatting-change records ({stats['property_changes']})")
                    if stats.get("comment_refs"):
                        removed.append(f"{label}: comment anchors ({stats['comment_refs']})")
                elif low.startswith("word/media/") or low.startswith("docprops/thumbnail."):
                    if low.endswith(MEDIA_EXT):
                        new_raw, ok = _strip_media(raw, name, policy)
                        if ok and new_raw != raw:
                            raw = new_raw
                            removed.append(f"embedded image metadata: {name}")
                        elif ok:
                            raw = new_raw
                        else:
                            warnings.append(f"could not sanitize embedded image: {name}")

                zout.writestr(item, raw)
    finally:
        z.close()

    out = buf.getvalue()
    after = inspect_docx_bytes(out)
    residual = _residual(after)

    report = {
        "job_id": None,
        "file": {
            "filename": filename, "format": "docx", "mime": SUPPORTED_MIME["docx"],
            "sha256_in": hashlib.sha256(data).hexdigest(),
            "sha256_out": hashlib.sha256(out).hexdigest(),
            "bytes_in": len(data), "bytes_out": len(out),
        },
        "policy": asdict(policy),
        "detected": before,
        "removed": [{"field": r} for r in removed],
        "kept": [],
        "verify": {"before": before, "after": after, "residual": residual,
                   "verdict": "clean" if not residual else "residual_metadata"},
        "lossless": False,
        "pixels_identical": None,
        "watermark_note": "Document properties, comments, tracked changes and embedded image "
                          "metadata are removed. Embedded statistical watermarks are not removed.",
        "warnings": warnings,
    }
    return out, report
