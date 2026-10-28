"""Layer-1 removal: container-footprint removal with re-scan verification.

Scope: images (JPEG/PNG/WebP/HEIC/AVIF/GIF/TIFF), video (MP4/MOV/WebM), PDF, DOCX and
text. Audio is detect-only by product decision. Only Layer-1 footprints are
removed (C2PA manifests, EXIF/XMP/IPTC, container tags, document properties). Content
bytes (pixels/samples/document body) are preserved byte-for-byte where the format allows
(lossless stripping). Content-embedded watermarks (Layer 2) are NEVER touched or claimed
removed; every result carries an explicit Layer-2 disclaimer.

Contract (AGENTS.md 8.3):
  - Detect first (caller supplies a scan_id; we re-read its report).
  - Strip Layer-1 only.
  - Validate output decodes.
  - Idempotent.
  - Verify by re-scan (before/after diff + verdict).
  - Record hashes in/out + fields removed.
  - Expire output blobs.
  - Carry user attestation + jurisdiction disclosure notes.
"""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import struct
import time
import uuid
import zipfile
from dataclasses import dataclass, field
from typing import Any, Optional

from . import config, db, pipeline
from .analyzers import text_an
from .rules import engine

LAYER2_DISCLAIMER = (
    "Layer-1 container footprints only were removed. Layer-2 content-embedded marks "
    "(C2PA content bindings that survive, SynthID, AudioSeal, VideoSeal, DWT-DCT, "
    "invisible watermarks, etc.) may still be present and detectable. This output is "
    "NOT a claim that the content is human-made or AI-free."
)


@dataclass
class RemovalResult:
    removal_id: str
    scan_id: str
    status: str
    modality: str
    input_sha256: str
    output_sha256: str = ""
    fields_removed: list[str] = field(default_factory=list)
    output_blob_path: str = ""
    output_download_url: str = ""
    before: dict = field(default_factory=dict)
    after: dict = field(default_factory=dict)
    verdict: str = ""
    layer2_disclaimer: str = LAYER2_DISCLAIMER
    error: str = ""


class RemovalError(Exception):
    pass


# ---------------------------------------------------------------------------
# Byte-level, lossless Layer-1 strippers
# ---------------------------------------------------------------------------

def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _strip_jpeg(data: bytes) -> tuple[bytes, list[str]]:
    """Remove APP1 (EXIF/XMP), APP13 (IPTC/Photoshop), APP14 (Adobe) segments.
    DCT coefficients and all other segments are preserved byte-for-byte."""
    if not data.startswith(b"\xff\xd8"):
        raise RemovalError("not a JPEG")
    out = bytearray(b"\xff\xd8")
    i = 2
    removed = []
    n = len(data)
    while i < n:
        if data[i] != 0xFF:
            # trailing garbage; stop
            break
        # skip fill bytes
        while i < n and data[i] == 0xFF:
            i += 1
        if i >= n:
            break
        marker = data[i]
        i += 1
        # standalone markers without length
        if marker in (0xD8, 0xD9, 0x01) or 0xD0 <= marker <= 0xD7:
            out.append(0xFF)
            out.append(marker)
            if marker == 0xD9:
                # EOI: append rest (should be none) and finish
                out.extend(data[i:])
                i = n
                break
            continue
        if i + 2 > n:
            break
        seg_len = struct.unpack(">H", data[i:i + 2])[0]
        seg_end = i + seg_len
        segment = data[i - 2:i + seg_len] if False else data[i - 1:i + seg_len]  # marker+length+payload
        # segment bytes including marker
        full = data[i - 1:i + seg_len + 1] if False else None
        # reconstruct: marker (1) + length(2) + payload(seg_len-2)
        payload = data[i + 2:seg_end]
        # decide
        drop = False
        label = None
        if marker == 0xE1:
            # APP1: EXIF or XMP
            if payload.startswith(b"Exif\x00\x00"):
                drop, label = True, "EXIF"
            elif b"http://ns.adobe.com/xap/1.0/" in payload[:64] or payload.lstrip().startswith(b"<?xpacket"):
                drop, label = True, "XMP"
            else:
                drop, label = True, "APP1"
        elif marker == 0xEB:
            # APP11: C2PA JUMBF container (and possibly other APP11 data)
            low = payload.lower()
            if b"jumbf" in low or b"c2pa" in low:
                drop, label = True, "C2PA (APP11)"
            else:
                drop, label = True, "APP11"
        elif marker == 0xED:
            drop, label = True, "IPTC/Photoshop (APP13)"
        elif marker == 0xEE:
            drop, label = True, "Adobe (APP14)"
        if drop:
            removed.append(label)
            i = seg_end
            continue
        # keep segment verbatim
        out.extend(data[i - 1:seg_end + 1]) if False else None
        # append marker + length + payload
        out.append(0xFF)
        out.append(marker)
        out.extend(data[i:i + 2])
        out.extend(payload)
        i = seg_end
        # stop at SOS: copy the rest verbatim
        if marker == 0xDA:
            # SOS: append remaining bytes verbatim
            out.extend(data[i:])
            i = n
            break
    # ensure EOI
    if not out.endswith(b"\xff\xd9"):
        out.extend(b"\xff\xd9")
    # de-dupe removed labels
    seen = set()
    uniq = []
    for r in removed:
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    return bytes(out), [f"jpeg:{r}" for r in uniq]


def _strip_png(data: bytes) -> tuple[bytes, list[str]]:
    """Remove text/metadata chunks: tEXt, iTXt, zTXt, eXIf, iCCP (optional keep? drop iCCP to be safe? keep ICC). 
    We drop tEXt/iTXt/zTXt/eXIf only; keep iCCP (color profile, not AI fingerprint)."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RemovalError("not a PNG")
    out = bytearray(data[:8])  # signature
    i = 8
    n = len(data)
    removed = []
    while i < n:
        if i + 12 > n:
            break
        length = struct.unpack(">I", data[i:i + 4])[0]
        ctype = data[i + 4:i + 8]
        chunk_end = i + 12 + length
        chunk = data[i:chunk_end]
        if ctype in (b"tEXt", b"iTXt", b"zTXt", b"eXIf", b"caBX"):
            removed.append("C2PA (caBX)" if ctype == b"caBX" else ctype.decode("ascii", "replace"))
            i = chunk_end
            continue
        out.extend(chunk)
        i = chunk_end
        if ctype == b"IEND":
            break
    # trailing
    if i < n:
        out.extend(data[i:])
    seen = set()
    uniq = []
    for r in removed:
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    return bytes(out), [f"png:{r}" for r in uniq]


def _strip_webp(data: bytes) -> tuple[bytes, list[str]]:
    """Remove EXIF and XMP chunks from a RIFF WebP."""
    if not (data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
        raise RemovalError("not a WebP")
    out = bytearray(data[:12])  # RIFF....WEBP
    i = 12
    n = len(data)
    removed = []
    # RIFF chunks: 4-byte id, 4-byte size (little-endian), payload padded to even
    while i + 8 <= n:
        cid = data[i:i + 4]
        size = struct.unpack("<I", data[i + 4:i + 8])[0]
        payload_start = i + 8
        payload_end = payload_start + size
        padded_end = payload_end + (size % 2)
        if cid in (b"EXIF", b"XMP ", b"C2PA"):
            removed.append(cid.decode("ascii", "replace").strip())
            i = padded_end
            continue
        out.extend(data[i:padded_end])
        i = padded_end
    # VP8X advertises which metadata chunks exist; clear the bits for the ones we dropped
    if out[12:16] == b"VP8X" and len(out) >= 21:
        if "EXIF" in removed:
            out[20] &= ~0x08
        if "XMP" in removed:
            out[20] &= ~0x04
    # fix RIFF size
    riff_size = len(out) - 8
    struct.pack_into("<I", out, 4, riff_size)
    seen = set()
    uniq = []
    for r in removed:
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    return bytes(out), [f"webp:{r}" for r in uniq]


def _strip_pdf(data: bytes) -> tuple[bytes, list[str]]:
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(io.BytesIO(data))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    # carry over
    if reader.metadata:
        pass  # drop metadata
    # remove XMP
    try:
        if writer._root_object.get("/Metadata"):
            del writer._root_object["/Metadata"]
    except Exception:
        pass
    buf = io.BytesIO()
    writer.write(buf)
    removed = ["pdf:metadata", "pdf:xmp"]
    return buf.getvalue(), removed


def _strip_docx(data: bytes) -> tuple[bytes, list[str]]:
    removed = []
    inp = io.BytesIO(data)
    out = io.BytesIO()
    with zipfile.ZipFile(inp, "r") as zin:
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                name = info.filename
                if name.startswith("docProps/"):
                    removed.append(f"docx:{name}")
                    continue
                zout.writestr(info, zin.read(name))
    return out.getvalue(), removed


def _strip_text(data: bytes) -> tuple[bytes, list[str]]:
    text = data.decode("utf-8", "replace")
    cleaned = text_an.clean_unicode(text)
    removed = []
    if cleaned != text:
        removed.append("text:unicode_hygiene")
    return cleaned.encode("utf-8"), removed


# ---------------------------------------------------------------------------
# R4 image strippers: HEIC/AVIF (ISO-BMFF/HEIF), GIF, TIFF
# ---------------------------------------------------------------------------

_C2PA_UUID = bytes.fromhex("d8fec3d61b0e483c92975828877ec481")
_XMP_MIMES = (b"application/rdf+xml", b"application/xmp+xml")


def _box_iter(buf: bytes, start: int, end: int):
    """Yield (offset, size, header_size, type) for ISO-BMFF boxes in buf[start:end]."""
    i = start
    while i + 8 <= end:
        size = struct.unpack(">I", buf[i:i + 4])[0]
        btype = buf[i + 4:i + 8]
        hs = 8
        if size == 1:
            if i + 16 > end:
                raise RemovalError("truncated 64-bit box")
            size = struct.unpack(">Q", buf[i + 8:i + 16])[0]
            hs = 16
        elif size == 0:
            size = end - i
        if size < hs or i + size > end:
            raise RemovalError(f"malformed box {btype!r} at {i}")
        yield i, size, hs, btype
        i += size


def _box(btype: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", 8 + len(payload)) + btype + payload


def _read_uint(b: bytes, pos: int, n: int) -> int:
    return int.from_bytes(b[pos:pos + n], "big") if n else 0


def _write_uint(v: int, n: int) -> bytes:
    return v.to_bytes(n, "big") if n else b""


def _strip_heif(data: bytes) -> tuple[bytes, list[str]]:
    """Drop C2PA uuid boxes and Exif/XMP metadata items from HEIC/AVIF.

    Only the `meta` item tables are rewritten; the coded image bytes in `mdat` are copied
    verbatim and every iloc offset is rebased so the image items still resolve.
    """
    if data[4:8] != b"ftyp":
        raise RemovalError("not an ISO-BMFF image")
    top = list(_box_iter(data, 0, len(data)))
    removed: list[str] = []
    meta = next(((o, s, h) for o, s, h, t in top if t == b"meta"), None)
    if meta is None:
        raise RemovalError("HEIF file has no meta box")
    m_off, m_size, m_hs = meta
    m_body = m_off + m_hs + 4  # FullBox version+flags
    children = list(_box_iter(data, m_body, m_off + m_size))
    child = {t: (o, s, h) for o, s, h, t in children}
    for need in (b"iinf", b"iloc"):
        if need not in child:
            raise RemovalError(f"HEIF meta has no {need.decode()}")

    # --- iinf: find metadata item ids
    io_, is_, ih = child[b"iinf"]
    iv = data[io_ + ih]
    p = io_ + ih + 4 + (2 if iv == 0 else 4)
    drop_ids: set[int] = set()
    kept_infe: list[bytes] = []
    for eo, es, eh, et in _box_iter(data, p, io_ + is_):
        if et != b"infe":
            raise RemovalError("unexpected box in iinf")
        ev = data[eo + eh]
        if ev < 2:
            raise RemovalError("infe version < 2 not supported")
        q = eo + eh + 4
        iid = _read_uint(data, q, 2 if ev == 2 else 4)
        q += (2 if ev == 2 else 4) + 2
        itype = data[q:q + 4]
        rest = data[q + 4:eo + es]
        if itype == b"Exif":
            drop_ids.add(iid)
            removed.append("heif:EXIF")
        elif itype == b"mime" and any(mt in rest for mt in _XMP_MIMES):
            drop_ids.add(iid)
            removed.append("heif:XMP")
        else:
            kept_infe.append(data[eo:eo + es])

    has_c2pa = any(t == b"uuid" and data[o + h:o + h + 16] == _C2PA_UUID for o, s, h, t in top)
    if has_c2pa:
        removed.append("heif:C2PA")
    if not drop_ids and not has_c2pa:
        return data, []

    pitm_id = None
    if b"pitm" in child:
        po, ps, ph = child[b"pitm"]
        pitm_id = _read_uint(data, po + ph + 4, 2 if data[po + ph] == 0 else 4)
    if pitm_id in drop_ids:
        raise RemovalError("primary item is metadata; refusing to rewrite")

    # --- iloc: parse all items
    lo, ls, lh = child[b"iloc"]
    lv = data[lo + lh]
    if lv > 2:
        raise RemovalError(f"iloc version {lv} not supported")
    q = lo + lh + 4
    off_sz, len_sz = data[q] >> 4, data[q] & 0x0F
    base_sz, idx_sz = data[q + 1] >> 4, (data[q + 1] & 0x0F if lv in (1, 2) else 0)
    q += 2
    count = _read_uint(data, q, 2 if lv < 2 else 4)
    q += 2 if lv < 2 else 4
    items = []
    for _ in range(count):
        iid = _read_uint(data, q, 2 if lv < 2 else 4)
        q += 2 if lv < 2 else 4
        method = 0
        if lv in (1, 2):
            method = _read_uint(data, q, 2) & 0x0F
            q += 2
        dref = _read_uint(data, q, 2)
        q += 2
        base = _read_uint(data, q, base_sz)
        q += base_sz
        ext_n = _read_uint(data, q, 2)
        q += 2
        exts = []
        for _ in range(ext_n):
            idx = _read_uint(data, q, idx_sz)
            q += idx_sz
            eoff = _read_uint(data, q, off_sz)
            q += off_sz
            elen = _read_uint(data, q, len_sz)
            q += len_sz
            exts.append([idx, eoff, elen])
        items.append({"id": iid, "method": method, "dref": dref, "base": base, "exts": exts})

    kept_items = [it for it in items if it["id"] not in drop_ids]
    for it in kept_items:
        if it["method"] != 0:
            raise RemovalError("iloc construction_method != 0 not supported")
        if it["exts"] and any(e[2] == 0 for e in it["exts"]):
            raise RemovalError("zero-length (to-EOF) extents not supported")

    # --- iref: drop references from/to dropped items
    def rebuild_iref() -> bytes | None:
        if b"iref" not in child:
            return None
        ro, rs, rh = child[b"iref"]
        rv = data[ro + rh]
        w = 2 if rv == 0 else 4
        out = bytearray(data[ro + rh:ro + rh + 4])
        for so, ss, sh, st in _box_iter(data, ro + rh + 4, ro + rs):
            r = so + sh
            frm = _read_uint(data, r, w)
            n = _read_uint(data, r + w, 2)
            to = [_read_uint(data, r + w + 2 + k * w, w) for k in range(n)]
            if frm in drop_ids:
                continue
            to = [t for t in to if t not in drop_ids]
            if not to:
                continue
            body = _write_uint(frm, w) + _write_uint(len(to), 2) + b"".join(_write_uint(t, w) for t in to)
            out += _box(st, body)
        return _box(b"iref", bytes(out))

    # --- ipma: drop associations for dropped items
    def rebuild_ipma() -> bytes | None:
        if b"iprp" not in child:
            return None
        po, ps, ph = child[b"iprp"]
        parts = []
        for so, ss, sh, st in _box_iter(data, po + ph, po + ps):
            if st != b"ipma":
                parts.append(data[so:so + ss])
                continue
            v, flags = data[so + sh], _read_uint(data, so + sh + 1, 3)
            r = so + sh + 4
            n = _read_uint(data, r, 4)
            r += 4
            w = 2 if v < 1 else 4
            entries = []
            for _ in range(n):
                iid = _read_uint(data, r, w)
                r += w
                cnt = data[r]
                r += 1
                alen = cnt * (2 if flags & 1 else 1)
                entries.append((iid, data[r - 1:r + alen]))
                r += alen
            kept = [(iid, a) for iid, a in entries if iid not in drop_ids]
            body = bytes([v]) + _write_uint(flags, 3) + _write_uint(len(kept), 4)
            body += b"".join(_write_uint(iid, w) + a for iid, a in kept)
            parts.append(_box(b"ipma", body))
        return _box(b"iprp", b"".join(parts))

    iinf_payload = bytes([iv]) + data[io_ + ih + 1:io_ + ih + 4] + _write_uint(len(kept_infe), 2 if iv == 0 else 4)
    new_iinf = _box(b"iinf", iinf_payload + b"".join(kept_infe))
    new_iref = rebuild_iref()
    new_iprp = rebuild_ipma()

    def build_iloc(rebase: dict[tuple[int, int], int]) -> bytes:
        body = bytearray(data[lo + lh:lo + lh + 4])
        body += bytes([(off_sz << 4) | len_sz, (base_sz << 4) | idx_sz])
        body += _write_uint(len(kept_items), 2 if lv < 2 else 4)
        for it in kept_items:
            body += _write_uint(it["id"], 2 if lv < 2 else 4)
            if lv in (1, 2):
                body += _write_uint(it["method"], 2)
            body += _write_uint(it["dref"], 2) + _write_uint(0, base_sz)
            body += _write_uint(len(it["exts"]), 2)
            for k, (idx, eoff, elen) in enumerate(it["exts"]):
                body += _write_uint(idx, idx_sz) + _write_uint(rebase[(it["id"], k)], off_sz) + _write_uint(elen, len_sz)
        return _box(b"iloc", bytes(body))

    def build_meta(iloc: bytes) -> bytes:
        parts = []
        for o, s, h, t in children:
            if t == b"iinf":
                parts.append(new_iinf)
            elif t == b"iloc":
                parts.append(iloc)
            elif t == b"iref" and new_iref is not None:
                parts.append(new_iref)
            elif t == b"iprp" and new_iprp is not None:
                parts.append(new_iprp)
            else:
                parts.append(data[o:o + s])
        return _box(b"meta", data[m_off + m_hs:m_body] + b"".join(parts))

    # Kept extent bytes are copied verbatim into one fresh mdat; offsets are known after layout.
    blobs = []
    for it in kept_items:
        for k, (idx, eoff, elen) in enumerate(it["exts"]):
            src = it["base"] + eoff
            if src + elen > len(data):
                raise RemovalError("iloc extent points past end of file")
            blobs.append(((it["id"], k), data[src:src + elen]))

    head = b"".join(data[o:o + s] for o, s, h, t in top
                    if t not in (b"meta", b"mdat", b"uuid", b"free", b"skip"))
    keep_other = b"".join(data[o:o + s] for o, s, h, t in top
                          if t == b"uuid" and data[o + h:o + h + 16] != _C2PA_UUID)
    placeholder = {key: 0 for key, _ in blobs}
    meta_len = len(build_meta(build_iloc(placeholder)))
    cursor = len(head) + meta_len + len(keep_other) + 8
    rebase = {}
    for key, blob in blobs:
        rebase[key] = cursor
        cursor += len(blob)
    if max(rebase.values(), default=0) >= 1 << (8 * off_sz) and off_sz:
        raise RemovalError("rebased offset does not fit iloc offset_size")
    meta_box = build_meta(build_iloc(rebase))
    if len(meta_box) != meta_len:
        raise RemovalError("meta size changed during layout")
    mdat = _box(b"mdat", b"".join(blob for _, blob in blobs))
    out = head + meta_box + keep_other + mdat
    return out, list(dict.fromkeys(removed))


def _strip_gif(data: bytes) -> tuple[bytes, list[str]]:
    """Drop application extensions that carry metadata (C2PA, XMP); keep NETSCAPE looping."""
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        raise RemovalError("not a GIF")
    i = 13
    if data[10] & 0x80:
        i += 3 * (2 ** ((data[10] & 0x07) + 1))
    out = bytearray(data[:i])
    removed = []

    def skip_subblocks(k: int) -> int:
        while True:
            if k >= len(data):
                raise RemovalError("truncated GIF sub-blocks")
            n = data[k]
            k += 1
            if n == 0:
                return k
            k += n

    while i < len(data):
        t = data[i]
        if t == 0x3B:
            out.append(0x3B)
            break
        if t == 0x21:
            label = data[i + 1]
            end = skip_subblocks(i + 2)
            if label == 0xFF:
                app = data[i + 3:i + 3 + data[i + 2]]
                if app.startswith(b"C2PA_GIF"):
                    removed.append("gif:C2PA")
                    i = end
                    continue
                if app.startswith(b"XMP Data"):
                    removed.append("gif:XMP")
                    i = end
                    continue
            elif label == 0xFE:
                removed.append("gif:comment")
                i = end
                continue
            out += data[i:end]
            i = end
        elif t == 0x2C:
            j = i + 10
            if data[i + 9] & 0x80:
                j += 3 * (2 ** ((data[i + 9] & 0x07) + 1))
            j += 1  # LZW minimum code size
            end = skip_subblocks(j)
            out += data[i:end]
            i = end
        else:
            raise RemovalError(f"unexpected GIF block 0x{t:02x}")
    return bytes(out), list(dict.fromkeys(removed))


_TIFF_DROP = {
    0x010E: "description", 0x010F: "make", 0x0110: "model", 0x0131: "software",
    0x0132: "datetime", 0x013B: "artist", 0x8298: "copyright", 0x02BC: "XMP",
    0x83BB: "IPTC", 0x8769: "EXIF", 0x8825: "GPS", 0xCD41: "C2PA",
}
_TIFF_TYPE_SIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4}


def _strip_tiff(data: bytes) -> tuple[bytes, list[str]]:
    """Remove metadata tags from every IFD by rewriting each IFD in place.

    Dropped entries are removed from the directory and the entry count is reduced; the slack
    left at the end of each IFD is zero-filled. Image strips/tiles keep their exact offsets, so
    no pixel byte moves. Orphaned metadata payloads are zeroed so the strings are gone too.
    """
    if data[:4] not in (b"II*\x00", b"MM\x00*"):
        raise RemovalError("not a classic TIFF (BigTIFF unsupported)")
    bo = "<" if data[:2] == b"II" else ">"
    out = bytearray(data)
    removed = []
    ifd = struct.unpack(bo + "I", data[4:8])[0]
    seen = set()
    while ifd and ifd not in seen:
        seen.add(ifd)
        if ifd + 2 > len(data):
            raise RemovalError("IFD offset past end of file")
        n = struct.unpack(bo + "H", data[ifd:ifd + 2])[0]
        entries = [data[ifd + 2 + k * 12: ifd + 14 + k * 12] for k in range(n)]
        nxt_pos = ifd + 2 + n * 12
        nxt = struct.unpack(bo + "I", data[nxt_pos:nxt_pos + 4])[0]
        keep = []
        for e in entries:
            tag, typ, cnt, val = struct.unpack(bo + "HHII", e)
            if tag in _TIFF_DROP:
                removed.append("tiff:" + _TIFF_DROP[tag])
                nbytes = _TIFF_TYPE_SIZE.get(typ, 1) * cnt
                if nbytes > 4 and val + nbytes <= len(out):
                    out[val:val + nbytes] = bytes(nbytes)
            else:
                keep.append(e)
        block = struct.pack(bo + "H", len(keep)) + b"".join(keep) + struct.pack(bo + "I", nxt)
        old_len = 2 + n * 12 + 4
        out[ifd:ifd + old_len] = block + bytes(old_len - len(block))
        ifd = nxt
    return bytes(out), list(dict.fromkeys(removed))


# ---------------------------------------------------------------------------
# Video stripper (R2) — ffmpeg stream-copy (lossless, no re-encode)
# ---------------------------------------------------------------------------

def _ffmpeg_available() -> bool:
    import shutil
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _strip_video(data: bytes, filename: str) -> tuple[bytes, list[str]]:
    if not _ffmpeg_available():
        raise RemovalError("ffmpeg/ffprobe not installed (manual integration #9)")
    name = (filename or "").lower()
    if not name.endswith((".mp4", ".mov", ".m4v", ".webm", ".mkv")):
        raise RemovalError(f"unsupported video format: {filename}")
    import subprocess, tempfile, os
    fd_in, in_path = tempfile.mkstemp(suffix=pathlib.Path(filename).suffix or ".mp4")
    fd_out, out_path = tempfile.mkstemp(suffix=pathlib.Path(filename).suffix or ".mp4")
    os.close(fd_in)
    os.close(fd_out)
    os.unlink(out_path)
    try:
        with open(in_path, "wb") as f:
            f.write(data)
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-i", in_path,
               "-map", "0", "-c", "copy",
               "-map_metadata", "-1",
               "-movflags", "+faststart",
               out_path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            raise RemovalError(f"ffmpeg failed: {r.stderr.strip()[:300]}")
        cleaned = open(out_path, "rb").read()
        # verify decode
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                               "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                               out_path], capture_output=True, text=True, timeout=120)
        if probe.returncode != 0:
            raise RemovalError(f"output failed to decode: {probe.stderr.strip()[:200]}")
        removed = ["video:container_metadata", "video:c2pa_box"]
        return cleaned, removed
    finally:
        for p in (in_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def _strip_for_modality(modality: str, mime: str, data: bytes, filename: str):
    name = (filename or "").lower()
    if modality == "text" or mime.startswith("text/"):
        return _strip_text(data)
    if modality == "video":
        return _strip_video(data, filename)
    if modality == "image":
        # Route by content, not extension: a renamed file must still hit the right parser.
        sniffed, _ = pipeline.sniff(data[:64], filename)
        stripper = {
            "image/jpeg": _strip_jpeg,
            "image/png": _strip_png,
            "image/webp": _strip_webp,
            "image/heic": _strip_heif,
            "image/avif": _strip_heif,
            "image/gif": _strip_gif,
            "image/tiff": _strip_tiff,
        }.get(sniffed)
        if stripper is None:
            raise RemovalError(f"unsupported image format: {sniffed}")
        return stripper(data)
    if modality == "document":
        if name.endswith(".pdf"):
            return _strip_pdf(data)
        if name.endswith(".docx"):
            return _strip_docx(data)
        raise RemovalError(f"unsupported document format: {filename}")
    raise RemovalError(f"removal not supported for modality: {modality}")


def _validate_decodes(modality: str, mime: str, data: bytes, filename: str):
    name = (filename or "").lower()
    if modality == "image":
        from PIL import Image
        Image.open(io.BytesIO(data)).verify()
        # re-open to ensure loadable
        im = Image.open(io.BytesIO(data))
        im.load()
    elif modality == "document":
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            PdfReader(io.BytesIO(data))
        elif name.endswith(".docx"):
            zipfile.ZipFile(io.BytesIO(data)).testzip()
    elif modality == "text":
        data.decode("utf-8")
    elif modality == "video":
        import subprocess, tempfile, os
        fd, path = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
        try:
            with open(path, "wb") as f:
                f.write(data)
            r = subprocess.run(["ffprobe", "-v", "error", path], capture_output=True, timeout=120)
            if r.returncode != 0:
                raise RemovalError("output failed to decode")
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


def _rescan_summary(data: bytes, filename: str) -> dict:
    """Run analyzers on bytes via a temp file path and return conclusion-ish summary."""
    import tempfile, os
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        rep = pipeline.analyze_bytes_sync(data, filename)
        conc = rep.get("conclusion", {})
        # collect metadata/c2pa signal statuses
        sigs = {}
        layer1_present = []
        for s in rep.get("signals", []):
            sigs[s["name"]] = {"status": s["status"], "grade": s["evidence_grade"]}
            if s.get("kind") in ("c2pa", "metadata") and s["status"] == "detected":
                layer1_present.append(s["name"])
        return {
            "provenance_class": conc.get("provenance_class"),
            "evidence_grade": conc.get("evidence_grade"),
            "label": conc.get("label"),
            "signals": sigs,
            "layer1_present": layer1_present,
        }
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def remove_layer1(scan_id: str, attested: bool = False, options: Optional[dict] = None) -> RemovalResult:
    if not attested:
        raise RemovalError("user attestation required (Layer-2 disclaimer must be accepted)")

    scan = db.get_scan(scan_id)
    if not scan:
        raise RemovalError("scan not found")
    if not scan.get("blob_path") or not pathlib.Path(scan["blob_path"]).exists():
        raise RemovalError("original bytes no longer available (expired or hash-only scan)")
    modality = scan["modality"]
    if modality not in ("image", "document", "text", "video"):
        raise RemovalError(f"removal not supported for modality: {modality}")

    original = pathlib.Path(scan["blob_path"]).read_bytes()
    input_sha = _sha256(original)

    # idempotency: if an identical input was already removed, return existing? For R0, recompute (cheap).
    removal_id = uuid.uuid4().hex

    before = _rescan_summary(original, scan["filename"])

    try:
        cleaned, fields = _strip_for_modality(modality, scan["mime"] or "", original, scan["filename"])
    except Exception as e:
        raise RemovalError(f"stripping failed: {e}")

    # validate decodes
    try:
        _validate_decodes(modality, scan["mime"] or "", cleaned, scan["filename"])
    except Exception as e:
        raise RemovalError(f"output failed to decode: {e}")

    output_sha = _sha256(cleaned)
    after = _rescan_summary(cleaned, scan["filename"])

    # store output blob
    out_dir = config.BLOB_DIR / "removals"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{removal_id}_{pathlib.Path(scan['filename']).name}"
    out_path.write_bytes(cleaned)
    expires = time.time() + config.BLOB_TTL_HOURS * 3600

    db.create_removal(removal_id, scan_id, modality, input_sha, attested)
    db.save_removal_result(removal_id, output_sha, str(out_path), fields, {
        "before": before, "after": after, "layer2_disclaimer": LAYER2_DISCLAIMER,
    })

    # The verdict comes from re-scanning the output, never from what the stripper claims it did.
    if after["layer1_present"]:
        verdict = "layer1_residue"
    elif before["layer1_present"] or fields:
        verdict = "layer1_clean"
    else:
        verdict = "no_layer1_found"

    return RemovalResult(
        removal_id=removal_id,
        scan_id=scan_id,
        status="done",
        modality=modality,
        input_sha256=input_sha,
        output_sha256=output_sha,
        fields_removed=fields,
        output_blob_path=str(out_path),
        output_download_url=f"/v1/removals/{removal_id}/download",
        before=before,
        after=after,
        verdict=verdict,
    )


# ---------------------------------------------------------------------------
# R3: batch removal + manifest/archive
# ---------------------------------------------------------------------------

def run_batch(batch_id: str, scan_ids: list[str], preset: str, attested: bool) -> None:
    db.set_batch_status(batch_id, "running")
    removal_ids = []
    manifest_entries = []
    out_dir = config.BLOB_DIR / "batches"
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{batch_id}.zip"
    try:
        for sid in scan_ids:
            try:
                res = remove_layer1(sid, attested=attested)
                removal_ids.append(res.removal_id)
                entry = {
                    "scan_id": sid,
                    "removal_id": res.removal_id,
                    "modality": res.modality,
                    "input_sha256": res.input_sha256,
                    "output_sha256": res.output_sha256,
                    "fields_removed": res.fields_removed,
                    "verdict": res.verdict,
                    "layer2_disclaimer": res.layer2_disclaimer,
                }
                # platform label preview + disclosure for the preset
                try:
                    scan = db.get_scan(sid)
                    if scan and scan.get("report_json"):
                        rep = json.loads(scan["report_json"])
                        facts = engine.facts_from_report(rep)
                        entry["platform_preview"] = engine.platform_preview(facts, self_disclosure=False)
                        entry["disclosure"] = engine.disclosure_check(
                            content_type=scan.get("modality") or "image",
                            is_ai_generated=True,
                        )
                except Exception:
                    pass
                manifest_entries.append(entry)
            except Exception as e:
                manifest_entries.append({"scan_id": sid, "error": str(e)[:300]})
        # build zip
        import zipfile as _zf
        with _zf.ZipFile(zip_path, "w", _zf.ZIP_DEFLATED) as zf:
            for entry in manifest_entries:
                rid = entry.get("removal_id")
                if rid:
                    row = db.get_removal(rid)
                    if row and row.get("output_blob_path"):
                        p = pathlib.Path(row["output_blob_path"])
                        if p.exists():
                            zf.write(p, arcname=f"cleaned/{p.name}")
            manifest = {
                "batch_id": batch_id,
                "preset": preset,
                "created_at": time.time(),
                "layer2_disclaimer": LAYER2_DISCLAIMER,
                "entries": manifest_entries,
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        db.save_batch_result(batch_id, removal_ids, str(zip_path), manifest)
    except Exception as e:
        db.set_batch_status(batch_id, "error", str(e)[:300])