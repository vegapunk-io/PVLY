# PRD — Provenably Sanitizer ("MD Remover")

Status: Draft v1.0
Owner: Product / Engineering
Last updated: 2026-10-23
Related code: `app/` (existing detector), new `app/sanitizer/` (this product)

---

## 1. Summary

Add a **Sanitizer mode** to Provenably that removes **container metadata and provenance manifests** from files before publishing, and verifies the result. It complements the existing **Detect** (C2PA checker) capability and adds **platform-ready export** presets for social platforms.

One-line pitch: *Check a file for AI provenance, strip the metadata that identifies it, then prove what was removed — in one pass.*

---

## 2. Problem & Motivation

Creators, privacy-conscious users, and newsrooms need to publish media without leaking:

- Camera GPS/device/owner info (EXIF).
- Editing history and software fingerprints (XMP, IPTC, generator strings).
- Content Credentials (C2PA/JUMBF) that may reveal AI generation or authorship.
- Hidden document properties (author, revision history, tracked changes, comments).
- Tags/encoder strings in audio/video containers.

Existing tools are piecemeal (ExifTool CLI, mat2, hand re-encoding) and none combine **detect → strip → verify** with **platform presets** in one workflow.

---

## 3. Goals & Non-Goals

### Goals
- G1. Reliably remove **metadata and C2PA manifests** from JPG, PNG, WebP, PDF, DOCX, and audio/video containers.
- G2. Provide a **C2PA checker** that reports trust state, AI source type, and tamper before/after.
- G3. **Verify** the sanitized output by re-scanning and diffing.
- G4. Offer **platform presets** (LinkedIn, Facebook, Instagram, Threads, Pinterest, X, YouTube, Reddit, Snapchat, TikTok).
- G5. Batch processing, REST API, audit trail, privacy-preserving retention controls.

### Non-Goals
- NG1. **Guaranteed watermark removal.** Statistical watermarks (AudioSeal, VideoSeal, SynthID, green-list text) are only *degraded* by re-encoding/paraphrase; never claim removal.
- NG2. Forgery, impersonation, or defeating law-enforcement/forensic analysis.
- NG3. DRM circumvention.
- NG4. Text LLM watermark removal in v1 (research only, see §12).

---

## 4. Personas

| Persona | Need |
|---|---|
| Creator / influencer | Publish images without leaking GPS/device; pass platform checks cleanly |
| Privacy user | Strip metadata before sharing photos/documents |
| Newsroom / OSINT | Sanitize sources; know what was removed for audit |
| Platform / moderation | Understand what metadata reaches them |
| Developer | Programmatic strip + report via API |

---

## 5. Scope & Formats

### In scope (v1)
| Format | Detection | Metadata strip | Notes |
|---|---|---|---|
| JPG/JPEG | C2PA, EXIF, XMP, IPTC | ✅ | Remove APP11/JUMBF, EXIF, XMP, IPTC, comments, thumbnails |
| PNG | C2PA (`caBX`), tEXt/iTXt/zTXt, eXIf | ✅ | Remove ancillary chunks |
| WebP | C2PA chunk, EXIF/XMP/ICCP | ✅ | RIFF chunk removal; optional lossless re-mux |
| PDF | XMP `/Metadata`, `/Info`, attachments | ✅ | Also strip embedded image metadata |
| DOCX/DOC | core/app/custom props, comments, tracked changes, embedded media | ✅ | OOXML zip/XML rewrite |
| WAV/MP3/M4A | RIFF INFO, ID3, MP4 tags | ✅ | Audio metadata only |
| MP4/MOV | udta/container tags, C2PA | ✅ | Container metadata only |

### Out of scope (v1)
- Watermark removal (see §12), live video streams, RAW camera formats, HEIC/AVIF (v2 candidate), spreadsheets/slides (v2).

---

## 6. Functional Requirements

### FR-1 Upload & Detect
- Accept single/batch uploads; reject > size cap (default 100 MB/file) and unsupported types with clear errors.
- Run C2PA + metadata analyzers; return a **Detect Report** (reuse existing report schema):
  - `file{name,sha256,mime,size}`
  - `c2pa{state,issuer,dss,source_type,actions,ingredients,tamper}`
  - `metadata{exif,xmp,iptc,png_text,id3,container}`
  - `conclusion{provenance_class,evidence_grade,notes}`
  - `coverage` (what ran / not configured)

### FR-2 Sanitize
- `strip(file, policy) -> (sanitized_bytes, RemoveReport)`.
- **Lossless-first**: remove metadata without re-encoding pixels where the format allows.
- **Policy options:** `keep_icc` (default true), `keep_orientation` (bake into pixels, default true), `strip_color_profile` (default false), `reencode` (default off).
- **RemoveReport** lists per-field actions: `removed[]`, `kept[]`, `failed[]` with reason.
- Must be **idempotent** (running twice yields no change).
- Never silently corrupt: validate output decodes; on failure return original + error.

### FR-3 Verify
- Re-run Detect on sanitized bytes.
- Return a **diff**: fields gone, fields remaining, and a verdict `clean | residual_metadata | residual_c2pa | residual_watermark`.
- Must confirm C2PA = absent and no EXIF/XMP/critical tags remain (per policy).

### FR-4 Platform Presets
- Presets define: max resolution, output format, quality, metadata removal set, and notes on what the platform itself strips/keeps.
- Presets: `linkedin, facebook, instagram, threads, pinterest, x, youtube, reddit, snapchat, tiktok` + `generic`.
- "Platform-ready export" applies resize/convert + strip in one step, returns file + report + preset applied.

### FR-5 Batch & API
- Batch upload, per-file status, ZIP of sanitized outputs + JSON manifest.
- REST endpoints (see §8), API key auth, rate limits.
- Webhook/polling for async jobs.

### FR-6 Audit & Privacy
- Audit record per job: `{job_id, sha256_in, sha256_out, policy, removed_fields, user, ts}`.
- Retention modes: `ephemeral` (delete blobs immediately after response), `ttl` (default 24 h), `keep_report_only`.
- Never log file contents.

### FR-7 UI
- Pages: **Sanitize** (drop zone → detect → strip → verify → download), **Batch**, **Platform presets**, **API docs**, **Audit**.
- Show before/after diff visually; warn when residual watermark likely remains.

---

## 7. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | CPU-only for metadata strip; GPU optional for re-encode/watermark research |
| NFR-2 | p95 strip latency < 2 s for ≤10 MB image; async for docs/AV |
| NFR-3 | Idempotent, deterministic output |
| NFR-4 | No silent data loss; always validate output decodes |
| NFR-5 | Horizontal scale via queue + stateless workers |
| NFR-6 | Privacy: no content logging; TTL janitor |
| NFR-7 | Test coverage with golden fixtures (before/after hashes) per format |
| NFR-8 | Accessible UI; no build step (Jinja2 + HTMX/Alpine) |

---

## 8. API Design (v1)

```
POST /v1/detect                 multipart file -> DetectReport
POST /v1/sanitize               multipart file + policy -> {job_id} or (wait=true) file+report
GET  /v1/sanitize/{job_id}      status + RemoveReport
GET  /v1/sanitize/{job_id}/file download sanitized bytes
POST /v1/verify                 multipart file -> VerifyResult
POST /v1/presets/{preset}/export multipart file -> sanitized+resized file+report
GET  /v1/presets                list presets
GET  /v1/jobs/{job_id}/audit    audit record
```

Policy schema:
```json
{
  "keep_icc": true,
  "keep_orientation": true,
  "strip_color_profile": false,
  "reencode": false,
  "formats": {"jpeg": {"quality": 92}}
}
```

RemoveReport schema:
```json
{
  "job_id": "…",
  "file": {"name":"…","sha256_in":"…","sha256_out":"…","mime":"image/jpeg","bytes_in":0,"bytes_out":0},
  "removed": [{"group":"exif","field":"GPSLatitude","value_redacted":true}],
  "kept": [{"group":"icc","field":"profile"}],
  "failed": [{"group":"xmp","field":"…","reason":"…"}],
  "verify": {"c2pa":"absent","exif":"absent","xmp":"absent","verdict":"clean"},
  "watermark_note": "Metadata removed; statistical watermarks (if any) are not removed.",
  "preset": "instagram"
}
```

---

## 9. Data Model

- `jobs(id, kind, status, preset, policy_json, file_in_sha, file_out_sha, mime, bytes_in, bytes_out, error, created_at, updated_at)`
- `job_fields(job_id, group, field, action, reason)`
- `audit(id, job_id, user, action, ts)`
- `presets(slug, name, spec_json, version)`
- Reuse `db.py` patterns (SQLite WAL → Postgres).

---

## 10. Tech Stack

| Layer | Choice |
|---|---|
| API | FastAPI + Pydantic (reuse) |
| UI | Jinja2 + HTMX/Alpine (no build) |
| Image | Pillow, pyexiftool/exiftool, imagecodecs/libwebp, c2pa-python |
| PDF | pikepdf (qpdf) + PyMuPDF |
| DOCX | python-docx + raw OOXML (zip/XML) |
| Audio | mutagen, soundfile, ffmpeg |
| Video | ffmpeg sidecar |
| Analysis | numpy/scipy + existing analyzers |
| Queue | arq or Celery+RQ + Redis |
| DB | SQLite→Postgres/SQLAlchemy |
| Storage | local → S3/GCS with TTL |
| Auth/Billing | X-API-Key → JWT/IdP + Stripe |
| Deploy | Docker + docker-compose; nginx; Cloud Run/Fly |
| Tests | pytest + golden files |
| Observability | structlog, Sentry, Prometheus |

---

## 11. Roadmap

| Phase | Deliverable | Duration |
|---|---|---|
| 0 | Scaffold `app/sanitizer/`, plugin interface, golden fixtures | 1 wk |
| 1 | JPG/PNG/WebP detect+strip+verify; `/v1/sanitize`; UI | 2–3 wk (✅ shipped) |
| 2 | PDF + DOCX (+ recursive embedded media) | 2 wk (✅ shipped) |
| 3 | Audio/video metadata strip (mutagen/ffmpeg) | 2 wk |
| 4 | 10 platform presets + batch/ZIP + API + audit | 1–2 wk |
| 5 | Queue + Postgres + S3 + auth/billing | 2–3 wk |
| 6 | Watermark degradation research (optional) | ongoing |

v1 (phases 0–4): ~8–10 weeks, 1 dev.

---

## 12. Watermark Reality (must be stated in UI)

- **Removable:** container metadata, EXIF/XMP/IPTC, C2PA/JUMBF, DOC/PDF props, ID3/RIFF/MP4 tags.
- **Not removable (best-effort only):** AudioSeal, VideoSeal, SynthID, green-list text marks. Re-encoding/noise/paraphrase may degrade them with quality loss and no guarantee.
- UI copy: *"Metadata removed. Embedded watermarks, if present, are not removed."*

---

## 13. Legal & Ethical Guardrails

- Require user **attestation** ("I own this content / privacy use").
- Jurisdiction-aware warning: removing AI provenance to misrepresent content may violate EU AI Act Art. 50 and platform ToS.
- Keep **Detect** available; never market as a way to evade disclosure laws.
- Audit trail for accountability; no content retention by default.
- Document that C2PA is a no-removal spec; stripping is a privacy action that destroys attribution.

---

## 14. Acceptance Criteria (v1)

- [x] JPG/PNG/WebP: after sanitize, `exiftool -a -G1` shows no EXIF/XMP/IPTC/C2PA; pixels byte-identical when `reencode=false`.
- [x] Verify reports `c2pa: absent`, `exif: absent`, `xmp: absent`, `verdict: clean`.
- [x] Idempotence: sanitize(sanitize(x)) == sanitize(x) output hash.
- [x] PDF/DOCX: `/Info`+XMP removed; no author/comments/tracked changes; embedded images stripped.
- [ ] Audio/Video: no ID3/RIFF/udta tags; duration/streams unchanged.
- [ ] All 10 presets produce valid outputs with the correct dimensions/format.
- [ ] Batch of 50 files completes; ZIP + manifest correct.
- [ ] API returns documented schemas; 4xx on unsupported/oversize.
- [ ] Golden-fixture pytest suite passes in CI.
- [ ] No content logged; `ephemeral` mode leaves no files on disk.

---

## 15. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Lossy re-encode degrades quality | Default `reencode=false`; lossless strip |
| Format edge cases (WebP variants, PDF XMP) | Golden fixtures per format; fuzz tests |
| False "clean" if a new tag type appears | Verify re-scan + whitelist checks; update tags table |
| User expectation of watermark removal | Explicit UI copy + report note |
| Legal exposure | Attestation, warnings, audit, Detect retained |
| Scale (video) | Queue + worker autoscaling; size caps |

---

## 16. Open Questions

1. Do we support HEIC/AVIF/RAW in v2? (high demand for mobile photos)
2. Should `x`/`snapchat` presets also re-encode to defeat container fingerprint? (they recompress anyway)
3. Monetization: per-file vs per-GB vs subscription?
4. Self-host/on-prem requirement for newsrooms?
5. Do we ship the watermark-degradation module at all, given legal risk?

---

## 17. Success Metrics

- Strip success rate ≥ 99.5% (valid output, metadata gone).
- Verify pass rate ≥ 99%.
- p95 latency targets met.
- Zero reported "watermark removed" false claims.
- Retention: 0 files left after ephemeral jobs.
