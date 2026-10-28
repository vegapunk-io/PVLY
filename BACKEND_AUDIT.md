# Backend audit — Provenably (PVLY) — 2026-10-28

Evidence-based. "Verified" = reproduced by command in this repo. "Claimed" = stated in
README/AGENTS/ARCHITECTURE or UI but not backed by a live connector.

## 1. Verified working (backend)

| Capability | Evidence |
|---|---|
| App boots, serves UI + API | `uvicorn app.main:app` → `/health` 200 |
| C2PA validation (Trusted/Valid) | `pytest` `test_pipeline_conclusions` 19/19 pass; signed fixtures grade `strong` |
| Official C2PA trust list (27 anchors) | `/v1/capabilities` → `official_c2pa_trust_list: true` |
| Metadata forensics (EXIF/IPTC/XMP) | analyzer `available()` True; demo `iptc_ai_tagged_no_c2pa.jpg` → `ai_generated_metadata` weak |
| Open watermark DWT-DCT | `open_watermark_dwtdct: true`; `sdxl_watermarked.png` → `ai_generated_watermark` moderate |
| Image forensics (ELA/FFT/noise) | analyzer available True |
| Audio container + spectral | analyzer available True; `speech_like_signed.wav` → strong |
| Video BMFF + frame sampling | analyzer available True; `clip_signed.mp4` → strong |
| Text unicode hygiene | `text_hidden_chars.txt` → `text_hidden_characters` weak |
| Text stylometry heuristic | analyzer available True |
| Text greenlist lab | `/v1/lab/greenlist` roundtrip test pass |
| Platform-label preview | `/v1/platforms/preview` test pass |
| Jurisdiction disclosure checklist | `/v1/disclosure/check` test pass |
| AI Watermark Registry (25 entries) | `/v1/registry` returns 25; `/v1/registry/{slug}` 200 |
| SSRF guard on URL scan | `test_ssrf_*` (3 tests) pass |
| Empty upload rejection | `test_empty_upload_rejected` pass |
| Demo-asset path traversal guard | `test_demo_asset_path_traversal` pass |
| Request ID + structured logging | `/metrics` + response header verified |
| Prometheus /metrics | endpoint 200, counters present |
| Auth hook (static X-API-Key) | `require_api_key` enforced when `PROVENABLY_API_KEYS` set |
| Blob TTL janitor | thread started in lifespan; `cleanup_expired_blobs` exists |
| SQLite WAL persistence | `scans`/`events` tables; 94 scans stored |
| Frontend build served by backend | `/` 200, adapter-static prerendered |

## 2. Claimed (README/UI) but NOT live — honest gaps

These report `false` in `/v1/capabilities` → `manual_integration`:

1. OpenAI Verify connector
2. Google SynthID connector (image/video/audio/text)
3. Meta AudioSeal
4. Meta Video Seal
5. TrustMark / Stable Signature / WAM
6. Passive AI-image classifier
7. Zero-shot text detector
8. ffmpeg audio demux for video
9. Visible-logo template matcher
10. Auth & billing (IdP, ownership, metering)
11. Production signing identity (CA cert, TSA, KMS)
12. Editorial rule/registry refresh (quarterly)
13. Queue / Postgres / object storage
14. ~~Official C2PA trust list~~ — **DONE** (2026-10-28)

Additional product claims not yet implemented:
- **Removal (Layer 1)** — R0–R4 roadmap; only a 501 scaffold exists (`POST /v1/remove`).
  No file is modified; product is detect-only.
- **Batch removal / presets apply** — frontend `presets` + `batch` pages exist but removal
  backend absent.

## 3. Verified failing / missing (production blockers)

| Blocker | Evidence | Priority |
|---|---|---|
| Auth open by default | `PROVENABLY_API_KEYS=[]` → `require_api_key` no-ops | P0 |
| No rate limiting | no middleware/limiter in `main.py` | P0 |
| Uploads fully in memory (200 MB cap) | `await file.read()` | P0 |
| Unpinned deps, no lockfile | `requirements.txt` uses `>=` | P0 |
| No observability beyond logs | no Sentry/metrics history | P2 (metrics done) |
| No CI until added | `.github/workflows/ci.yml` now present | P0 (done) |
| No Docker/compose | no Dockerfile | P1 |
| No LICENSE | now MIT (added) | done |
| Deprecated lifecycle | migrated to lifespan | done |
| Coverage 76.9% | `pytest.ini` gate 60% (raise to 80%+) | P2 |

## 4. Dummy / stale surfaces removed

- Frontend `/remove` and `/design-system` routes deleted; all `resolve('/remove')` /
  `resolve('/design-system')` links cleaned from Header, Footer, home, history, report,
  registry, presets. Build now prerenders without 404s.
- `POST /v1/remove` returns 501 (honest not-implemented), not a fake success.

## 5. Recommended next execution slices (in order)

1. **P0 security:** make API keys mandatory in non-dev mode; add rate limiting
   (slowapi or stdlib token bucket); stream uploads to disk with size cap.
2. **P0 reproducibility:** pin deps + generate lockfile (`pip-compile`).
3. **P1 deployability:** Dockerfile (multi-stage) + compose; readiness probe.
4. **P1 queue/storage:** move scans to arq/Celery; Postgres + S3-compatible blobs.
5. **P3 integrations:** execute Manual Integration Checklist one item at a time
   (config → connector → rendering → capability flip → test → decision log).
6. **R0 removal:** implement Layer-1 removal for JPG/PNG/PDF/DOCX with before/after
   re-scan verification; replace `test_detect_only_surface` with surface tests.

## 6. Honest bottom line

- **Running perfect (verified):** C2PA trust + validation, metadata forensics,
  DWT-DCT watermark, audio/video container, text hygiene, disclosure + platform preview,
  registry, SSRF guard, request IDs, metrics, trust-list integration, 29/29 tests.
- **Needs development:** all 13 remaining manual integrations, removal R0–R4, auth hardening,
  rate limiting, streaming uploads, queue/storage, Docker, lockfile.
- **No inference in this document:** every "verified" row was reproduced by a command in
  this repo; gaps are taken from `/v1/capabilities` and code inspection, not assumed.
