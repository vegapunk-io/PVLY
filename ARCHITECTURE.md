# ARCHITECTURE.md — Provenably (PVLY)

> System architecture as it **currently exists** (`0.1.0-prototype`, verified 2026-10-24).
> Companion docs: [`AGENTS.md`](AGENTS.md) (operating rules) · [`DESIGN.md`](DESIGN.md)
> (product/UX) · [`README.md`](README.md).
> **Every technical decision must be logged in §14.**

---

## 1. System purpose

Given a file (image/audio/video/text/document) or a public URL, produce one graded
**Provenance Report**. Detection only — the product never modifies content (wedge decided
2026-10-24, A-012). All-CPU, single-process prototype designed so the
scale-up swap (queue, Postgres, S3, GPU workers) requires **no route changes**.

## 2. Architecture at a glance

```
                         ┌─────────────────────────────────────────────────────────┐
  Browser (Jinja2 UI) ──▶│  FastAPI app  app/main.py                              │
  API client ──────────▶ │  · UI routes (10)        · /v1 JSON API (17)           │
                         │  · SSRF guard            · X-API-Key hook              │
                         │  · BackgroundTasks       · TTL janitor thread          │
                         └────────────────────────┬───────────────────────────────┘
                                                  │ run_scan(scan_id)
                                     ┌────────────▼────────────┐
                                     │ Pipeline app/pipeline.py│
                                     │ sniff → 8 analyzers     │
                                     │ → aggregate → persist   │
                                     └──────┬───────────┬──────┘
              ┌────────────▼──┐  ┌─────▼───────────────┐  ┌───────▼────────┐
              │ Analyzers     │  │ Rules engine        │  │ SQLite (WAL)   │
              │ app/analyzers/│  │ app/rules/engine.py │  │ app/db.py      │
              │ + Signal model│  │ + 3 JSON datasets   │  │ + local blobs  │
              └───────────────┘  └─────────────────────┘  └────────────────┘
```

**Design invariants:** analyzers isolated (one crash = one `error` signal) · evidence
grades gate the verdict · pipeline is a pure entry point `pipeline.run_scan(scan_id)` (a
future arq/Celery worker calls the same function) · flat DB schema for trivial Postgres
migration · no frontend build step.

## 3. Tech stack (current, with rationale)

| Layer | Choice | Why | Scale-up path |
|---|---|---|---|
| API/UI | FastAPI ≥0.115 + Jinja2 + Pydantic 2, vanilla JS | Boring, typed, OpenAPI free, zero build | Same; nginx/Cloud Run + CDN |
| Jobs | FastAPI `BackgroundTasks` → `pipeline.run_scan` | No infra for prototype | arq/Celery/RQ; GPU workers on same queue |
| Storage | SQLite WAL + local blob dir + TTL janitor | Zero-config, flat schema | Postgres/SQLAlchemy; S3/GCS + lifecycle |
| Provenance | `c2pa-python` 0.38 (c2pa-rs 0.91) | Official SDK: validation + demo signing | Same; + official trust list, remote manifests |
| Media | Pillow, OpenCV-headless, PyWavelets, numpy | CPU-only watermark/metadata work | + ffmpeg sidecar (audio demux) |
| Auth | Static `X-API-Key` (on only if configured) | Prototype hook | JWT/IdP + Stripe metering |
| Tests | pytest + httpx TestClient | Fast (~3 s), golden fixtures | + CI (missing — K2) |

Python 3.11 observed. Dependencies are loose `>=` pins in `requirements.txt` (no lockfile — K6).
Heavy/GPU deps (torch, audioseal, videoseal, trustmark, transformers) are intentionally
**commented out** — worker-only manual integrations.

## 4. Component inventory

| Module | LOC | Responsibility |
|---|---|---|
| `app/main.py` | 443 | FastAPI app, all routes, SSRF-guarded fetch, API-key dependency, startup + janitor, `capabilities()` |
| `app/pipeline.py` | 193 | `sniff()` magic-byte modality detection; scan creation; analyzer orchestration (isolated, timed); report assembly; blob cleanup |
| `app/aggregate.py` | 91 | Signals → conclusion (priority rules §6); `coverage()` |
| `app/db.py` | 113 | SQLite schema + helpers (`scans`, `events`), thread lock, WAL |
| `app/config.py` | 45 | All env-driven settings; creates data dirs on import |
| `app/analyzers/base.py` | 63 | `Signal`, `Context`, `Analyzer` contract |
| `app/analyzers/c2pa_an.py` | 245 | C2PA validation via c2pa-rs; trust config (per-thread); DST/action/ingredient extraction; `sign_file` |
| `app/analyzers/jumbf.py` | 190 | Pure-Python JUMBF box walker ("how it works" structure dump) |
| `app/analyzers/metadata_an.py` | 224 | EXIF, XMP/IPTC `DigitalSourceType`, PNG text (A1111 `parameters`), generator strings, JPEG segment map |
| `app/analyzers/dwtdct.py` | 99 | DWT-DCT invisible-watermark codec port (numpy/pywt, no torch) |
| `app/analyzers/imwm_an.py` | 99 | SD/SDXL watermark decode + binomial p-value; Stable Signature/TrustMark/WAM stubs |
| `app/analyzers/forensics_an.py` | 82 | JPEG quality, canonical sizes, noise — context only; passive classifier stub |
| `app/analyzers/audio_an.py` | 152 | WAV spectral facts, MP3 ID3 summary; AudioSeal/SynthID-Audio stubs |
| `app/analyzers/video_an.py` | 131 | BMFF box walk, per-frame DWT-DCT sampling; Video Seal/logo/audio-track stubs |
| `app/analyzers/text_an.py` | 205 | Unicode hidden-char scan/clean, stylometry, green-list z-test + Lab generator |
| `app/analyzers/vendor_an.py` | 69 | OpenAI Verify + Google SynthID connectors (credential-gated) |
| `app/rules/engine.py` | 154 | Pure functions: `facts_from_report`, `platform_preview`, `disclosure_check`, registry lookup |
| `tools/dev_cert.py` | 71 | TEST root CA + claim-signing cert → `data/certs/` |
| `tools/make_demo_assets.py` | 315 | Generates 17 demo fixtures (signed/tampered/watermarked/text/audio/video) |
| `tools/fetch_trust_list.py` | 67 | Fetch official C2PA trust anchors → `data/trust/anchors.pem` (manual) |

## 5. Data flows

### 5.1 Scan (async default / sync with `wait=true`)
```
POST /v1/scans (file | text | url)
  → size cap (MAX_UPLOAD_MB) → [url: SSRF guard] → pipeline.new_scan_from_bytes
  → sniff(data[:64]) → (mime, modality) → sha256 → blob write → db.create_scan(status=queued)
  → BackgroundTasks: pipeline.run_scan(scan_id)
      for each analyzer where modality ∈ analyzer.modalities:
          available()? → run(ctx) timed, exceptions captured as error Signals
      aggregate(signals) → conclusion ; coverage(signals)
      engine.facts_from_report → platform_preview
      db.save_report → status=done ; if hash_only: delete blob
GET /v1/scans/{id}  ·  GET /report/{id} (HTML)  ·  GET /v1/scans/{id}/report.json
```

### 5.2 ~~Sanitize~~ — REMOVED 2026-10-24 (A-012)
The Detect→Strip→Verify sanitizer (`/v1/sanitize`, `/v1/detect`, `/sanitize`, `app/sanitizer/`,
`sanitize_jobs`) was removed in full by founder decision; the product is detection-only.
Regression-guarded by `test_detect_only_surface` (old routes must 404).

### 5.3 Rules / registry (stateless)
```
POST /v1/disclosure/check    facts → per-jurisdiction checklist (open_items)
POST /v1/platforms/preview   (scan_id|facts) → per-platform label prediction
GET  /v1/registry[/{slug}]   25-generator dataset   ·   GET /v1/rules/{platforms,jurisdictions}
```

### 5.4 Retention
Daemon janitor thread (every 600 s) deletes scan blobs past `blob_expires_at`
(= created + `BLOB_TTL_HOURS`) and nulls the pointer; reports persist.

## 6. Evidence & aggregation model (core IP — do not weaken)

`Signal = {kind, name, status, evidence_grade, summary, data, method, manual_integration, duration_ms}`
· grades: `strong > moderate > weak > none` · kinds: `c2pa, metadata, open_watermark,
vendor_watermark, passive, forensics, text_hygiene, text_watermark, container, connector`.

**Aggregation priority (`app/aggregate.py`, first match wins):**
1. C2PA hard-binding mismatch → `tampered_after_signing` (strong)
2. Valid C2PA w/ source type → `ai_generated_declared | ai_assisted_declared | captured_declared | signed_no_source_type` (grade = trust level)
3. Vendor watermark detected → `ai_generated_watermark` (strong)
4. Open watermark detected → `ai_generated_watermark` (best grade; forgeable ⇒ note attached)
5. Text: green-list → `text_watermark_detected`; hidden chars → `text_hidden_characters` (weak)
6. Generator metadata → `ai_generated_metadata` (**always weak** — unsigned/editable)
7. Otherwise → `no_provenance_signal` (none) + explicit "absence ≠ human origin" note

`coverage = {live, manual, errors, manual_modules[]}` ships in every report.

## 7. API inventory (27 routes)

**UI (HTML):** `/` = `/scan` (Scan) · `/demo` · `/report/{scan_id}` · `/registry` ·
`/registry/{slug}` · `/laws` · `/tools` · `/lab` · `/docs-guide`
**Scans:** `POST /v1/scans` · `GET /v1/scans` · `GET /v1/scans/{id}` ·
`GET /v1/scans/{id}/report.json` · `POST /v1/scans/demo/{name}` · `GET /v1/scans/{id}/preview.jpg` ·
`GET /demo-assets/{name}`
**Rules/Text/Meta:** `GET /v1/registry[/{slug}]` · `GET /v1/rules/platforms` ·
`GET /v1/rules/jurisdictions` · `POST /v1/disclosure/check` · `POST /v1/platforms/preview` ·
`POST /v1/text/unicode` · `POST /v1/lab/greenlist` · `GET /v1/capabilities` · `GET /health` ·
OpenAPI `/api/docs`

Auth (`X-API-Key`, only when `PROVENABLY_API_KEYS` set): scans read/write.
Public: UI, demo, registry/rules reads, preview capability URLs (K5).

## 8. Data model

```sql
scans(id PK, created_at, updated_at, status queued|running|done|error, modality,
      filename, mime, size, sha256, hash_only, blob_path, blob_expires_at, error, report_json)
events(id AUTOINCREMENT, ts, scan_id, kind, detail)   -- audit-ish trail (created)
```
IDs are `uuid4().hex[:12]`. Reports are stored as JSON blobs (`report_json`), not normalized.

**Report JSON (scan):** `{scan_id, product{name,version}, created_at, completed_at,
duration_ms, file{filename,mime,size,sha256}, modality, conclusion{provenance_class,label,
evidence_grade,decisive_signal,notes[]}, signals[], coverage, timings[], trust_sources[],
hash_only, platform_preview[], facts}`

## 9. Analyzer matrix — live vs. manual

| Capability | State | Module | Enabling step |
|---|---|---|---|
| C2PA validation (JPEG/PNG/WAV/MP4) | ✅ live | `c2pa_an` | — (trust list = manual #1) |
| Metadata forensics | ✅ live | `metadata_an` | — |
| DWT-DCT watermark (SD/SDXL) + video frames | ✅ live | `dwtdct`, `imwm_an`, `video_an` | — |
| Image/audio/video forensic context | ✅ live (context only) | `forensics_an`, `audio_an`, `video_an` | — |
| Text unicode/stylometry/green-list | ✅ live | `text_an` | — |
| Official C2PA trust list | 🔧 manual | `tools/fetch_trust_list.py` | Run script → `data/trust/anchors.pem` |
| OpenAI Verify · Google SynthID | 🔧 manual (partner-gated) | `vendor_an` | Credentials + endpoint env vars |
| AudioSeal · Video Seal · TrustMark · Stable Signature · WAM | 🔧 manual (torch/GPU) | `audio_an`, `video_an`, `imwm_an` | Install on workers |
| Passive image classifier · zero-shot text detector | 🔧 manual (GPU) | `forensics_an`, `text_an` | Deploy model svc; grade ≤ weak |
| ffmpeg audio demux · visible-logo matcher | 🔧 manual | `video_an` | ffmpeg binary; logo crops |
| Auth/billing · production signing · queue/Postgres/S3 | 🔧 manual | `main.py`, `c2pa_an.sign_file`, `db.py` | See README checklist #11/#12/#14 |

Live truth is always `GET /v1/capabilities` — update it with any change above.

## 10. Configuration (`app/config.py`, all env-overridable)

| Variable | Default | Meaning |
|---|---|---|
| `PROVENABLY_DATA_DIR` | `./data` | DB + blobs + certs + trust |
| `BLOB_TTL_HOURS` | `24` | Scan-blob retention |
| `HASH_ONLY` | `false` | Delete bytes right after analysis |
| `MAX_UPLOAD_MB` | `200` | Upload/URL size cap |
| `PROVENABLY_API_KEYS` | *(empty=open)* | Comma-separated static keys |
| `TRUST_ANCHORS_PEM` / `TRUST_ALLOWED_PEM` | `data/trust/*.pem` | Official C2PA anchors |
| `INCLUDE_DEMO_TRUST_ANCHOR` | `true` | Trust the TEST CA (demo only — disable in prod) |
| `OPENAI_VERIFY_API_KEY/_ENDPOINT`, `GOOGLE_SYNTHID_ENDPOINT`, `GOOGLE_ACCESS_TOKEN` | empty | Vendor connectors |
| `URL_FETCH_TIMEOUT` | `15` | URL ingestion timeout (s) |

## 11. Security architecture (current + gaps)

**In place:** SSRF guard (DNS resolve → reject private/loopback/link-local/reserved/
multicast; http(s) only; size cap) · upload size caps · demo path-traversal guard ·
password-PDF rejection · TTL/hash-only retention · optional `X-API-Key` · no content logging.
**Gaps (must close pre-production, = AGENTS.md K5):** open-by-default auth; unauthenticated
capability URLs (report, preview) with 48-bit IDs; no rate limiting;
whole-upload in-memory reads; SSRF TOCTOU/redirect re-resolution; unsandboxed untrusted-file
parsers (Pillow/OpenCV) in-process.

## 12. Testing architecture

| Suite | Covers | Notes |
|---|---|---|
| `tests/test_smoke.py` (105 LOC) | 12 demo-fixture conclusions (parametrized), green-list round-trip, unicode clean, disclosure engine, full API flow, `sniff()`, detect-only surface (sanitizer routes 404) | Skips fixture tests if demo assets ungenerated |

**Current result (2026-10-24, after A-012): 13 passed / 5 failed** — same pre-existing K1 trust-anchor grading
(`moderate` vs expected `strong` on all signed fixtures). No CI (K2). Demo fixtures double
as test fixtures via `tools/make_demo_assets.py` (17 assets incl. tampered, stripped,
watermark-then-JPEG-q75 fragility demo, signed WAV/MP4).

## 13. Known technical debt & intended roadmap

- **Debt:** single-commit history · unpinned deps/no lockfile · deprecated startup event ·
  SQLite global lock · in-process jobs · no Docker/CI/LICENSE · rules data verified
  2026-10-14, quarterly refresh owed · report JSON not versioned.
- **Former Sanitizer PRD phases 0–6: WITHDRAWN 2026-10-24 (A-012)** — `docs/PRD.md` deleted
  (git history `beb4143`); queue/Postgres/S3 + auth/billing remain valid Detect roadmap items.
- **Scale triggers (documented):** queue+Postgres+S3 above a few hundred scans/day or any
  real video volume; GPU workers when torch detectors go live.

## 14. Decision Log (append-only — see AGENTS.md §9)

| ID | Date | Decision | Context / Why | Alternatives rejected | Consequences | Status |
|---|---|---|---|---|---|---|
| A-001 | ≤2026-10-14 | "Deliberately boring" stack: FastAPI+Jinja2+SQLite, no build step | CPU-only, 1-dev prototype; scale by swapping layers, not routes | SPA framework; Postgres from day 1 | Fast to run anywhere; UI ceiling; K5 hardening owed | Accepted |
| A-002 | ≤2026-10-14 | Evidence-grade model; weak never outranks strong; forensics never decisive | AI-detector market over-claims; defensibility is the product | Single "% AI" score | Most unsigned files → `no_provenance_signal` (honest, risks perceived uselessness) | Accepted |
| A-003 | ≤2026-10-14 | Unbuilt capabilities ship as wired `not_configured` connectors + coverage in every report | "Clean" must never over-claim; manual steps visible to buyers | Hiding stubs; mock results | 14-item manual checklist is the de-facto roadmap | Accepted |
| A-004 | ≤2026-10-14 | Delegate C2PA to official c2pa-rs; add pure-Python JUMBF walker for education | Correctness + trust semantics are hard; walker aids transparency/demo | Hand-rolled C2PA validation | Dep on c2pa-python settings API (cf. K1 thread-local issue) | Accepted |
| A-005 | ≤2026-10-14 | Pure numpy/pywt DWT-DCT port instead of `invisible-watermark` package | Avoid torch/onnx weight in CPU prototype; bit-compatible required | Package + heavy deps | Own codec to maintain; bit-accuracy tested via fixtures | Accepted |
| A-006 | ≤2026-10-14 | Analyzer isolation + per-analyzer timings in pipeline | One bad file/parser must not kill reports | Fail-fast pipeline | Errors surface as signals; slight complexity | Accepted |
| A-007 | ≤2026-10-14 | Rules/registry as versioned JSON + pure-function engine (not DB) | Editorial data, unit-testable, git-reviewable | DB-backed rules service now | Refresh = PR; needs quarterly re-verification cadence | Accepted |
| A-008 | 2026-10-23 (PRD) | Sanitizer: lossless-first, idempotent, Detect→Strip→Verify; NEVER claim watermark removal | Privacy utility without false "clean AI" claims; verifiable diff is differentiator | Re-encode-always; silent strip | Segment-level walkers to maintain per format; legal guardrails required (K7) | **Superseded by A-012** |
| A-009 | ≤2026-10-14 | Retention: blob TTL 24h + `hash_only`; reports persist | Privacy-by-default for untrusted user media | Keep everything | Sanitizer-blob expiry gap (K4) moot after A-012 | Accepted |
| A-010 | ≤2026-10-14 | Static API-key hook, enforced only if configured | Prototype openness with a clear swap point | Full auth now | Cannot deploy publicly as-is (K5) | Accepted (prototype only) |
| A-011 | 2026-10-24 | Adopt AGENTS/ARCHITECTURE/DESIGN + mandatory Decision/Change-Review logging before further development | Founder directive: every decision reviewable later; ends mega-commit pattern | Docs-as-code only in README | This system governs all future changes (AGENTS.md §9) | Accepted |
| A-012 | 2026-10-24 | **Detect-only: remove the Sanitizer everywhere** (code, routes, `/sanitize` UI, `/v1/detect`, `sanitize_jobs`, pikepdf/lxml deps, sanitizer tests, `docs/PRD.md`); homepage becomes Scan (file/text/URL tabs, recent scans) | Founder directive resolving DESIGN D1: one product wedge, no dual Detect-vs-remove positioning, no removal legal exposure | Keep both surfaces; deprioritize-only (hide nav) | −1,078 LOC; 27 routes; README "no removal" true; K3/K4/K7 closed; code recoverable at `beb4143`; regression test locks surface | Accepted |

## 15. Document history

| Date | Change | Author |
|---|---|---|
| 2026-10-24 | Initial creation from full codebase audit + live test run (27/32 passing, K1). | Engineering (agent-assisted), pending founder review |
| 2026-10-24 | A-012 executed: sanitizer architecture removed (diagram, flows, routes, schema, matrix, tests); counts updated (27 routes, 18 tests, 13 pass / 5×K1). | Founder + Engineering |
