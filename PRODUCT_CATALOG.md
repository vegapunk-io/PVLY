# Product catalog — Provenably (PVLY) — 2026-10-28

Complete inventory of every feature, tool, service and product surface shipped or wired
in the repository. "Live" = verified runnable. "Wired" = code present, returns
not_configured/not_installed with enabling step. "Roadmap" = documented but unimplemented.

## A. Core product — Provenance Report (per file)

One graded report per uploaded file (image / audio / video / text / document).

- **C2PA / Content Credentials validation** (live) — official SDK, trust anchors,
  manifest extraction, signer, ingredients, soft bindings, AI disclosure.
- **Metadata forensics** (live) — EXIF / IPTC / XMP / PNG text chunks, AI tags.
- **Open watermark decoders** (live) — DWT-DCT (SDXL 48-bit) + IMWM.
- **Image forensic context** (live) — ELA, FFT, noise analysis.
- **Audio container + spectral** (live) — RIFF/BMFF C2PA chunks, spectral features.
- **Video BMFF + frame sampling** (live) — per-frame scan + container hash.
- **Text unicode hygiene** (live) — zero-width, homoglyphs, soft hyphen, etc.
- **Text stylometry heuristic** (live) — heuristic AI-text signals.
- **Text greenlist lab** (live) — toy watermark generate/detect (demo key).
- **Vendor connectors** (wired) — OpenAI Verify, Google SynthID (return not_configured).
- **Evidence grading** (live) — strong/moderate/weak/none; weak never outranks strong.
- **Coverage reporting** (live) — live vs manual modules per report.
- **Platform-label preview** (live) — 11 platforms' likely AI label.
- **Jurisdiction disclosure checklist** (live) — 6 jurisdictions.
- **AI Watermark Registry** (live) — 25 generators with provenance facts.

## B. Web application (frontend routes)

- `/` Home (Scan wedge)
- `/scan` Scan (file / text / URL, demo tab)
- `/report/{id}` Provenance Report
- `/report/{id}` JSON download, preview
- `/registry` + `/registry/{slug}` Generator registry
- `/rules` (alias `/laws`) Disclosure rules + platforms
- `/tools` Text unicode tools
- `/lab` Watermark lab
- `/batch` Batch scan
- `/history` Scan history + filters
- `/settings` Browser prefs + API key
- `/presets` Platform presets
- `/pricing` Pricing
- `/auth` Sign in (stub, auth pending)
- `/docs-guide` Docs guide
- `/api` API & status
- `/demo` Demo files

## C. HTTP API

Scans: POST /v1/scans, GET /v1/scans, GET /v1/scans/{id},
GET /v1/scans/{id}/report.json, POST /v1/scans/demo/{name},
GET /v1/scans/{id}/preview.jpg, POST /v1/remove (501 scaffold).

Meta: GET /v1/demo-files, GET /v1/capabilities, GET /health, GET /metrics,
GET /demo-assets/{name}.

Rules/registry: GET /v1/registry, GET /v1/registry/{slug},
GET /v1/rules/platforms, GET /v1/rules/jurisdictions,
POST /v1/disclosure/check, POST /v1/platforms/preview.

Text/lab: POST /v1/text/unicode, POST /v1/lab/greenlist.

## D. Tools & scripts

- `tools/dev_cert.py` — test CA + claim-signing cert.
- `tools/make_demo_assets.py` — 17 demo fixtures.
- `tools/fetch_trust_list.py` — official C2PA trust anchors (done: 27 anchors).

## E. Data & rules (editorial, versioned)

- `app/rules/platforms.json` — 10 platforms (labels, triggers, confidence, last_verified).
- `app/rules/jurisdictions.json` — 6 jurisdictions.
- `app/rules/registry.json` — 25 generators.

## F. Infrastructure / quality

- SQLite (WAL) persistence, blob TTL janitor, hash-only mode.
- SSRF guard, path-traversal guard, API-key hook, rate limiter, request IDs, /metrics.
- CI workflow (GitHub Actions), frontend verify (check/lint/tests/build/budget).
- Coverage gate (60%, actual 76.8%).

## G. Roadmap (not yet implemented)

- Removal R0–R4 (Layer-1 container footprints; re-scan verification).
- 13 manual integrations (SynthID, AudioSeal, VideoSeal, TrustMark, passive classifier,
  text detector, ffmpeg demux, logo matcher, auth/billing, production signing, rules refresh,
  queue/Postgres/S3, OpenAI/Google connectors).
- Auth hardening completion, streaming-to-disk uploads, dependency lockfile, Docker.

## Growth levers

1. Complete manual integrations → flip capabilities to true → higher trust/revenue.
2. Implement removal R0 → unlocks "Detect → Remove → Verify" product promise.
3. Auth + billing → monetization.
4. Queue/storage → scale and multi-tenant.
5. Frontend a11y/perf polish → broader adoption.
6. Registry/rules editorial refresh → SEO + authority.