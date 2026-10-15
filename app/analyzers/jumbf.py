"""Pure-Python locator + box-tree walker for C2PA manifest stores (JUMBF, ISO/IEC 19566-5).

This is NOT a validator (the official c2pa SDK does validation). It exists to show *how it works*:
where the bytes live inside JPEG / PNG / MP4 / WebP / WAV containers and what the box tree looks like.
"""
from __future__ import annotations

import struct

C2PA_BMFF_UUID = bytes.fromhex("D8FEC3D61B0E483C92975828877EC481")
JUMBF_SUFFIX = bytes.fromhex("00110010800000AA00389B71")  # all C2PA JUMBF type UUIDs end with this


def _box_type_name(uuid16: bytes) -> str:
    head = uuid16[:4]
    if uuid16[4:] == JUMBF_SUFFIX and all(32 <= b < 127 for b in head):
        tag = head.decode("ascii")
        return {
            "c2pa": "c2pa (manifest store)", "c2ma": "c2ma (manifest)", "c2as": "c2as (assertion store)",
            "c2cl": "c2cl (claim)", "c2cs": "c2cs (claim signature)", "c2vc": "c2vc (credential store)",
            "c2db": "c2db (databox store)", "cbor": "cbor (CBOR content)", "json": "json (JSON content)",
            "uuid": "uuid (UUID content)", "jp2c": "jp2c (codestream)",
        }.get(tag, tag)
    if uuid16 == bytes.fromhex("40CB0C32BB8A489DA70B2AD6F47F4369"):
        return "embedded file (e.g. thumbnail)"
    return uuid16.hex()


def parse_boxes(data: bytes, depth: int = 0, max_depth: int = 6) -> list[dict]:
    """Walk a JUMBF byte string and return a nested list of boxes."""
    out, pos, n = [], 0, len(data)
    while pos + 8 <= n:
        lbox, tbox = struct.unpack(">I4s", data[pos:pos + 8])
        hdr = 8
        if lbox == 1:
            lbox = struct.unpack(">Q", data[pos + 8:pos + 16])[0]
            hdr = 16
        elif lbox == 0:
            lbox = n - pos
        if lbox < hdr or pos + lbox > n:
            out.append({"type": tbox.decode("latin1"), "size": lbox, "note": "truncated/invalid length"})
            break
        body = data[pos + hdr:pos + lbox]
        box = {"type": tbox.decode("latin1"), "size": lbox, "offset": pos}
        if tbox == b"jumb" and depth < max_depth:
            children = parse_boxes(body, depth + 1, max_depth)
            # the first child is the description box 'jumd'
            if children and children[0]["type"] == "jumd":
                box["label"] = children[0].get("label")
                box["content_type"] = children[0].get("content_type")
            box["children"] = children
        elif tbox == b"jumd":
            if len(body) >= 17:
                box["content_type"] = _box_type_name(body[:16])
                toggles = body[16]
                p = 17
                if toggles & 0x02:
                    end = body.find(b"\x00", p)
                    box["label"] = body[p:end].decode("utf-8", "replace") if end != -1 else None
                    p = end + 1
                if toggles & 0x04 and p + 4 <= len(body):
                    box["id"] = struct.unpack(">I", body[p:p + 4])[0]
                    p += 4
                if toggles & 0x08:
                    box["has_signature_field"] = True
        out.append(box)
        pos += lbox
    return out


# ------------------------------------------------------------------ container locators

def _jpeg_segments(data: bytes):
    """Yield (marker, offset, length, payload) for JPEG segments until SOS."""
    pos = 2
    n = len(data)
    while pos + 4 <= n:
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if marker == 0xDA:  # start of scan: entropy coded data follows
            break
        seglen = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        yield marker, pos, seglen + 2, data[pos + 4:pos + 2 + seglen]
        pos += 2 + seglen


def locate_jpeg(data: bytes) -> dict | None:
    boxes: dict[int, dict] = {}
    segs = []
    for marker, off, length, payload in _jpeg_segments(data):
        if marker != 0xEB or len(payload) < 16 or payload[:2] != b"JP":
            continue
        en = struct.unpack(">H", payload[2:4])[0]
        z = struct.unpack(">I", payload[4:8])[0]
        lbox, tbox = struct.unpack(">I4s", payload[8:16])
        b = boxes.setdefault(en, {"header": payload[8:16], "parts": {}, "lbox": lbox, "tbox": tbox})
        b["parts"][z] = payload[16:]
        segs.append({"offset": off, "length": length, "instance": en, "sequence": z})
    if not boxes:
        return None
    en = sorted(boxes)[0]
    b = boxes[en]
    body = b"".join(b["parts"][k] for k in sorted(b["parts"]))
    jumbf = b["header"] + body
    return {"container": "JPEG", "embedding": "APP11 (0xFFEB) segments, CI='JP'", "segments": segs,
            "segment_count": len(segs), "bytes": len(jumbf), "jumbf": jumbf}


def locate_png(data: bytes) -> dict | None:
    pos = 8
    n = len(data)
    while pos + 8 <= n:
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        if ctype == b"caBX":
            jumbf = data[pos + 8:pos + 8 + length]
            return {"container": "PNG", "embedding": "caBX chunk", "segments": [{"offset": pos, "length": length + 12}],
                    "segment_count": 1, "bytes": len(jumbf), "jumbf": jumbf}
        pos += 12 + length
    return None


def locate_riff(data: bytes) -> dict | None:
    if data[:4] != b"RIFF":
        return None
    form = data[8:12].decode("latin1")
    pos = 12
    n = len(data)
    while pos + 8 <= n:
        cid, length = struct.unpack("<4sI", data[pos:pos + 8])
        if cid == b"C2PA":
            jumbf = data[pos + 8:pos + 8 + length]
            return {"container": f"RIFF/{form}", "embedding": "'C2PA' chunk", "segments": [{"offset": pos, "length": length + 8}],
                    "segment_count": 1, "bytes": len(jumbf), "jumbf": jumbf}
        pos += 8 + length + (length & 1)
    return None


def locate_bmff(data: bytes) -> dict | None:
    pos = 0
    n = len(data)
    while pos + 8 <= n:
        size, btype = struct.unpack(">I4s", data[pos:pos + 8])
        hdr = 8
        if size == 1:
            size = struct.unpack(">Q", data[pos + 8:pos + 16])[0]
            hdr = 16
        elif size == 0:
            size = n - pos
        if size < hdr:
            break
        if btype == b"uuid" and data[pos + hdr:pos + hdr + 16] == C2PA_BMFF_UUID:
            body = data[pos + hdr + 16:pos + size]
            # FullBox version/flags (4), purpose (null-terminated), optional merkle offset (8), then JUMBF
            purpose_end = body.find(b"\x00", 4)
            purpose = body[4:purpose_end].decode("latin1", "replace") if purpose_end != -1 else "?"
            j = body.find(b"jumb")
            jumbf = body[j - 4:] if j >= 4 else b""
            return {"container": "ISO-BMFF (MP4/MOV/HEIF)", "embedding": "top-level 'uuid' box (C2PA UUID)",
                    "purpose": purpose, "segments": [{"offset": pos, "length": size}], "segment_count": 1,
                    "bytes": len(jumbf), "jumbf": jumbf}
        pos += size
    return None


def locate_manifest_store(data: bytes) -> dict | None:
    if data[:3] == b"\xff\xd8\xff":
        return locate_jpeg(data)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return locate_png(data)
    if data[:4] == b"RIFF":
        return locate_riff(data)
    if len(data) > 12 and data[4:8] in (b"ftyp", b"moov", b"mdat", b"free", b"wide"):
        return locate_bmff(data)
    return None


def describe(data: bytes) -> dict | None:
    loc = locate_manifest_store(data)
    if not loc:
        return None
    jumbf = loc.pop("jumbf", b"")
    tree = parse_boxes(jumbf) if jumbf else []
    loc["box_tree"] = tree
    loc["manifest_labels"] = [c.get("label") for b in tree for c in b.get("children", []) if c.get("type") == "jumb"]
    return loc
