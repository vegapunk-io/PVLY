<h1 align="center">
  <img src="frontend/src/lib/assets/brand/provenably-mark.png" width="110" height="110" alt="Provenably check mark" align="middle">
  Provenably
</h1>

<p align="center">
  <strong>See what AI left in your media. Remove the footprints you control. Prove it. Publish platform-ready.</strong>
</p>

<p align="center">
  Detect → Remove → Verify → Platform-ready
</p>

---

The current **0.1.0 prototype** has a live, evidence-graded Detect backend and a complete SvelteKit product interface. The Remove workflow and platform presets are implemented in the frontend, but the lossless Remove endpoint itself is the next backend milestone (**R0**). Provenably does not fake a clean file, a successful removal, or a vendor-watermark result that has not actually run.

> **Direction of record:** [`PHILOSOPHY.md`](PHILOSOPHY.md). Provenably’s removal boundary is **Layer-1** provenance data — C2PA manifests, EXIF/XMP/IPTC metadata, document properties, hidden Unicode, and comparable attached data. It will never claim to remove **Layer-2** signals embedded in content itself, such as invisible pixel/audio/video/text watermarks or patterns recognized by platform detectors.

Removal is a privacy and publishing-hygiene tool for content you own or are authorized to modify. The planned Remove flow keeps the Detect report and before/after audit trail, and carries platform/jurisdiction disclosure notes: removing attached metadata does not remove a duty to disclose synthetic content. Provenably is not built for forgery, impersonation, DRM circumvention, or defeating forensic investigation.

---

## What is live today

### Evidence-graded Detect

Submit exactly one uploaded file, one text payload, or one public URL and receive one Provenance Report containing:

- a bounded conclusion (`ai_generated_declared`, `tampered_after_signing`, `ai_generated_watermark`, `no_provenance_signal`, and related classes);
- an evidence grade — **strong**, **moderate**, **weak**, or **none**;
- the decisive signal and the method behind every check;
- analyzer timings, errors, trust sources, and an explicit coverage block;
- extracted facts and a researched platform-label preview.

Provenably is deliberately **not** a black-box “87% AI” detector. Cryptographic and watermark evidence outranks unsigned metadata; passive/forensic observations are context; “no signal found” never becomes “certified human.”

### Live analyzers

| Area | Current capability |
|---|---|
| **C2PA / Content Credentials** | Official `c2pa-python`/`c2pa-rs` validation for image, audio, video, and document inputs where the container supports it; trust-aware grading, source-type/action/ingredient extraction, tamper details, and a pure-Python JUMBF structure dump for education. |
| **Image metadata** | EXIF, XMP/IPTC `DigitalSourceType`, PNG text and Stable Diffusion/A1111 parameters, generator strings, and a JPEG segment map. Unsigned metadata is always weak evidence. |
| **Open image watermarks** | Bit-compatible numpy/PyWavelets DWT-DCT decode for SD/SDXL-style marks with bit accuracy and binomial p-value, including sampled video frames. Reports note that open watermarks are forgeable. |
| **Image forensics** | JPEG quality, canonical dimensions, and noise context. Passive classifier output is not shipped and, when added, will be capped at weak evidence. |
| **Audio** | WAV bandwidth, spectral-flatness, silence, and clipping facts plus an MP3 ID3 summary. AudioSeal and SynthID-Audio remain credential/worker integrations rather than fake results. |
| **Video** | BMFF box walk with brands, duration, tracks/handlers, encoder tag, and per-frame DWT-DCT sampling. Video Seal, audio-track demuxing, and a visible-logo matcher remain manual integrations. |
| **Text** | Hidden Unicode/ZWJ/bidi/variation-selector scan with a cleaned preview and downloadable result, stylometry context, and a guarded green-list z-test plus Lab generator. |
| **Vendor connectors** | OpenAI Verify and Google SynthID connectors are wired as honest `not_configured` / `requires_credentials` signals until partner access is configured. |
| **Coverage** | Every report carries live/manual/error counts and names the manual modules it could not run. `GET /v1/capabilities` is the runtime source of truth. |

### Research, rules, and platform readiness

- **AI Watermark & Provenance Registry:** 25 researched generator/vendor entries describing visible marks, invisible watermarks, C2PA/IPTC behavior, public detectors, robustness notes, confidence, and review dates.
- **Disclosure guidance:** six deployer-facing jurisdictions — EU, California, India, China, South Korea, and US federal — with confidence and verification metadata. It is structured research, not legal advice.
- **Platform preview:** 11 backend destinations separate the exact viewer-facing wording from documented provenance/detection routes, creator duties, edit behavior, confidence, and sources.
- **Presets:** Generic master plus YouTube, Instagram, TikTok, LinkedIn, Pinterest, Reddit, X, and Facebook presets in the frontend. Preset application to cleaned outputs arrives with the Remove roadmap; the catalog and policy handoff are present now.
- **Batch Detect:** the browser can queue up to 50 files sequentially against the live single-scan API, isolate per-file errors, link each full report, and download a real JSON manifest. A native `/v1/batch` job remains R3.

### Platform-label research at a glance

Platform behavior changes and must be re-verified quarterly. The current catalog was researched on **2026-10-24**:

| Destination | Viewer-facing outcome | Principal documented routes |
|---|---|---|
| Instagram / Facebook / Threads | **“AI info”** | C2PA and IPTC indicators, creator disclosure, Meta AI markers, detection systems |
| YouTube | **“Made with AI”** under “How this content was made” | Creator declaration, YouTube GenAI tools, valid C2PA, internal detection |
| TikTok | **“Creator labeled as AI-generated”** or TikTok-applied **“AI-generated”** | Creator toggle, native tools/effects, C2PA, models, invisible watermarking |
| LinkedIn | Lowercase **cr** Content Credentials marker | Signed C2PA provenance; the marker alone does not necessarily mean AI |
| Pinterest | **“AI modified”** | IPTC analysis, classifiers, owner indication |
| Reddit | No universal site-wide AI label | Indication, subreddit rules, flair, and moderation |
| X | **“Made with AI”** disclosure | Creator disclosure; reported C2PA-linked automation whose full criteria are not public |
| Google Search / Images | Provenance context in **About this image** | C2PA, IPTC, and SynthID-related provenance where available |
| Amazon KDP | No public reader label specified | AI-generated content must be disclosed to Amazon during publishing |

The API/report source of record is `app/rules/platforms.json`; the prerendered frontend uses the contract-tested mirror in `frontend/src/lib/data/platform-labels.ts`. Both must be updated together.

---

## Product and interface status

| Surface | Status | Present behavior |
|---|---|---|
| Detect / Scan | **Live** | File, text, public URL, demo fixtures, synchronous/asynchronous scans, and hash-only requests |
| Provenance Report | **Live** | Grade, conclusion, signals, coverage, trust sources, facts, and 11-destination preview |
| Batch Detect | **Live in browser** | Up to 50 sequential real scans plus a downloadable manifest; no native batch endpoint yet |
| Registry, Rules, Text Tools, Lab | **Live** | Researched datasets, disclosure/platform checks, Unicode cleaner, and green-list experiments |
| Remove | **Workflow live; endpoint R0** | Upload, real detection, footprint/readiness review, and policy selection are present; no cleaned file is produced until `/v1/remove` ships |
| Presets | **Catalog/UI live; application R3** | Destination, output, footprint, and disclosure policies can be selected and carried into Remove |
| History / Settings | **Prototype** | Deployment-wide scan history plus browser-local preferences and a session-only API key; not per-user accounts |
| Auth / Pricing checkout | **Interface only** | Account and billing surfaces explain the unavailable state and disable paid actions rather than pretending to authenticate or charge |

### Frontend routes

The SvelteKit application contains 17 page surfaces:

- `/` — product landing page
- `/scan` and `/report/{id}` — live Detect and report
- `/remove` and `/batch` — end-to-end Detect→Remove readiness and Batch Detect workflows
- `/presets` — Generic master and eight destination presets
- `/registry`, `/registry/{slug}`, and `/rules` — research and disclosure surfaces
- `/tools` and `/lab` — Unicode and green-list utilities
- `/api`, `/history`, `/pricing`, `/settings`, and `/auth` — API/status, deployment history, proposed plans, browser preferences, and account-readiness surfaces
- `/design-system` — internal, noindex design and typography reference

Legacy `/demo`, `/laws`, and `/docs-guide` paths redirect to their current equivalents. If the frontend has not been built, FastAPI retains a legacy HTML fallback for the original product routes.

### Design system

The interface uses a founder-approved, Zapier-derived mechanism system documented in [`DESIGN.md`](DESIGN.md) (decisions P-014–P-020):

- warm canvas `#fffefb`, soft surface `#f8f4f0`, coffee ink `#201515`, and one primary orange `#ff4f00`;
- Provenably’s primary check mark is forced to `#ff4f00`; the untouched founder-supplied source is retained only as provenance under `frontend/src/lib/assets/brand/source/`;
- six supplied platform marks are preserved without tracing, recoloring, cropping, or masking and served as optimized 144×144 lossless WebP derivatives; destinations without supplied artwork use lightweight glyph fallbacks;
- flat surfaces, complete hairline frames, and semantic evidence tags; no linear gradients, no decorative shadows, and no colored side-stripe accent bars;
- self-hosted **Hanken Grotesk Variable** for display, body, UI, tables, and reports; **JetBrains Mono Variable** only for hashes, IDs, filenames, code, and format chips;
- Latin-only font subsets, a conditional true-italic face, `font-synthesis: none`, and route/component-split mono loading for low-end devices.

The most recent verified production bundle (2026-10-24) measured **142.3 KiB JavaScript gzip** and **17.8 KiB CSS gzip**, within enforced budgets of 260 KiB and 85 KiB respectively. Public pages are prerendered and hydrate selectively.

---

## Architecture

```text
Browser / API client
        │
        ▼
FastAPI application (app/main.py)
  ├─ serves the static SvelteKit build and legacy fallback
  ├─ exposes the same-origin /v1 JSON API
  ├─ applies upload limits, SSRF guard, and optional X-API-Key auth
  └─ starts scan jobs and the blob-retention janitor
        │
        ▼
Pipeline (app/pipeline.py)
  sniff → isolated analyzers → aggregate → rules → persist report
        │                 │                 │
        ▼                 ▼                 ▼
  app/analyzers/      app/rules/       SQLite WAL + local blobs
```

| Layer | Current choice | Product/scale note |
|---|---|---|
| Frontend | SvelteKit 3, Svelte 5, TypeScript, Vite 8, `adapter-static` | Independent static artifact; prerendered public routes and small route chunks |
| Backend API | FastAPI + Pydantic 2, same-origin JSON API and static host | The analyzer pipeline is reused behind the SvelteKit UI |
| Jobs | FastAPI `BackgroundTasks` calling `pipeline.run_scan(scan_id)` | Queue/worker swap planned without changing API routes |
| Storage | SQLite WAL + local blob directory + TTL janitor | Postgres/object-storage migration remains a production step |
| Provenance | `c2pa-python` 0.38 / c2pa-rs 0.91 | Official validation and test signing; production trust/signing remain manual |
| Media/data | Pillow, OpenCV-headless, NumPy, PyWavelets | CPU-only prototype; GPU detectors belong on workers |
| Rules | Versioned JSON + pure-function rules engine | Editorial changes are Git-reviewable and unit-testable |

### Evidence model

Every analyzer emits typed signals with `kind`, `name`, `status`, `evidence_grade`, `summary`, `data`, `method`, `manual_integration`, and `duration_ms`. Aggregation is priority-based:

1. C2PA hard-binding mismatch
2. Valid C2PA with source type
3. Vendor watermark
4. Open watermark
5. Text watermark / hidden-character findings
6. Generator metadata — **always weak**
7. Otherwise, `no_provenance_signal`, with the explicit note that absence of evidence is not proof of human origin

One analyzer failure becomes one error signal; it does not silently discard the rest of the report.

---

## Quick start

### Prerequisites

- Python 3.11 (the currently verified runtime)
- Node.js 22 or newer
- npm 11 or newer
- A POSIX-style shell for `run.sh`

### Run everything

```bash
git clone https://github.com/vegapunk-io/PVLY.git
cd PVLY

python3 -m venv .venv
source .venv/bin/activate

./run.sh
```

`run.sh` installs backend requirements if imports are missing, generates the TEST C2PA certificate and 17 demo fixtures if needed, installs/builds the frontend if no build exists, and starts Uvicorn on `0.0.0.0:${PORT:-8000}`.

Open:

- Website: <http://localhost:8000>
- API reference page: <http://localhost:8000/api>
- OpenAPI: <http://localhost:8000/api/docs>
- Health: <http://localhost:8000/health>
- Live capabilities: <http://localhost:8000/v1/capabilities>

Because `run.sh` binds to all interfaces while API-key enforcement is open by default, use the manual `127.0.0.1` command below or configure `PROVENABLY_API_KEYS` before exposing the server beyond a trusted local environment.

### Manual production-shaped run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python tools/dev_cert.py
python tools/make_demo_assets.py

cd frontend
npm ci
npm run build
cd ..

uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend development

After installing the backend requirements and generating the certificate/demo fixtures above, run FastAPI from the repository root in one terminal:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then run Vite in another:

```bash
cd frontend
npm install
npm run dev
```

Vite serves the frontend at <http://localhost:5173> and proxies backend paths to `127.0.0.1:8000`, preserving same-origin relative API calls. See [`frontend/README.md`](frontend/README.md) for frontend-specific commands and build budgets.

### Tests and verification

Generate the test certificate and demo fixtures first; otherwise fixture-dependent backend tests may skip.

```bash
# Backend
pytest -q

# Frontend: Svelte Check, Prettier check, ESLint, Vitest, production build, bundle budget
cd frontend
npm run verify
```

**Known issue K1:** the backend suite is not yet fully green. Five signed demo fixtures can be graded `moderate` instead of their intended `strong` because the demo trust anchor is not consistently honored; the suspected cause is the analyzer’s c2pa-rs settings/thread boundary. This is tracked in [`AGENTS.md`](AGENTS.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md); it must be fixed before treating the backend suite as a release gate. The frontend verification suite and targeted API-flow checks are separate gates.

---

## API

FastAPI serves interactive OpenAPI documentation at `/api/docs`; the product-oriented reference is at `/api`.

### Scan workflow

```bash
# Synchronous scan (exactly one of file, text, or url)
curl -s -F file=@photo.jpg -F wait=true \
  http://localhost:8000/v1/scans

# Asynchronous scan, followed by status/report retrieval
curl -s -F url=https://example.com/image.jpg \
  http://localhost:8000/v1/scans
curl -s http://localhost:8000/v1/scans/<id>
curl -s http://localhost:8000/v1/scans/<id>/report.json

# Text with a user-supplied green-list key
curl -s -F "text=<marked.txt" -F greenlist_key="<secret>" -F wait=true \
  http://localhost:8000/v1/scans
```

Optional scan fields include `hash_only`, `greenlist_key`, and `wait`.

### Endpoint inventory

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/v1/scans` | Create a scan from exactly one `file`, `text`, or public `url` |
| `GET` | `/v1/scans` | Recent scans for this deployment |
| `GET` | `/v1/scans/{id}` | Scan status/detail |
| `GET` | `/v1/scans/{id}/report.json` | Completed JSON report |
| `GET` | `/v1/scans/{id}/preview.jpg` | Image-derived report preview where available |
| `GET` | `/v1/demo-files` | Generated demo fixture inventory |
| `POST` | `/v1/scans/demo/{name}` | Scan a generated demo fixture by name |
| `GET` | `/demo-assets/{name}` | Download a generated demo fixture |
| `GET` | `/v1/registry` and `/v1/registry/{slug}` | Generator/provenance registry |
| `GET` | `/v1/rules/platforms` | Researched platform-label dataset |
| `GET` | `/v1/rules/jurisdictions` | Disclosure jurisdiction dataset |
| `POST` | `/v1/platforms/preview` | Predict destination outcomes from `scan_id` or facts |
| `POST` | `/v1/disclosure/check` | Evaluate disclosure facts by jurisdiction |
| `POST` | `/v1/text/unicode` | Find and clean hidden Unicode characters |
| `POST` | `/v1/lab/greenlist` | Generate/detect green-list-marked demonstration text |
| `GET` | `/v1/capabilities` | Live versus manual integration inventory |
| `GET` | `/health` | Service/database health |

When `PROVENABLY_API_KEYS` is configured, the static `X-API-Key` check protects scan creation, list, detail, and report-JSON endpoints. Demo, registry/rules reads, rules checks, text utilities, capabilities, health, and image-preview URLs currently remain public; that split is part of the prototype hardening work below.

There is not yet a `/v1/remove`, native `/v1/batch`, `/v1/presets`, account/auth, API-key issuance, or billing endpoint. The external API, report JSON, and coverage model are designed so those capabilities can be added without changing the existing Detect workflow.

### Report JSON

A completed report includes:

```text
scan_id, product, created_at, completed_at, duration_ms,
file{filename,mime,size,sha256}, modality,
conclusion{provenance_class,label,evidence_grade,decisive_signal,notes[]},
signals[], coverage, timings[], trust_sources[], hash_only,
platform_preview[], facts
```

Each `platform_preview` item can include the exact `label_text`, placement `label_subtext`, `detection_summary`, `metadata_signals`, `creator_duty`, likely label decision, reasons, confidence, `last_verified`, and source links.

Current provenance classes are `ai_generated_declared`, `ai_assisted_declared`, `captured_declared`, `signed_no_source_type`, `tampered_after_signing`, `ai_generated_watermark`, `ai_generated_metadata`, `text_watermark_detected`, `text_hidden_characters`, and `no_provenance_signal`.

---

## Demo fixtures

`python tools/make_demo_assets.py` generates 17 self-contained fixtures, many of which double as golden test inputs. Highlights include:

| Fixture | Intended conclusion | Demonstrates |
|---|---|---|
| `ai_generated_signed.jpg` | `ai_generated_declared` | Signed C2PA AI assertion |
| `camera_capture_signed.jpg` | `captured_declared` | Signed capture assertion with device/EXIF context |
| `ai_edited_composite_signed.jpg` | `ai_assisted_declared` | Composite AI-assisted provenance |
| `ai_generated_tampered.jpg` | `tampered_after_signing` | Spliced manifest and changed pixels |
| `iptc_ai_tagged_no_c2pa.jpg` / `a1111_parameters.png` | `ai_generated_metadata` | Unsigned XMP/IPTC and PNG/generator metadata treated as weak |
| `sdxl_watermarked.png` | `ai_generated_watermark` | Open DWT-DCT watermark and statistical decode |
| `sdxl_watermarked_q75.jpg` | `no_provenance_signal` | Watermark fragility after JPEG recompression |
| `clip_signed.mp4` / `speech_like_signed.wav` | `ai_generated_declared` | C2PA in video/audio containers |
| `text_greenlist_marked.txt` | `text_watermark_detected` | Green-list round trip; the demo endpoint supplies the documented `demo-key` |
| `text_hidden_chars.txt` | `text_hidden_characters` | Zero-width/bidi artifacts and clean preview |
| `ai_generated_stripped.jpg` | `no_provenance_signal` | Metadata/manifest loss and the limits of absence |

The remaining fixtures are plain/control variants for manual comparison. The certificates are **TEST** credentials created only for demos; never use them as production signing material.

---

## Configuration, privacy, and security

Settings are environment-driven in `app/config.py`. `.env.example` lists common values, but the backend does not load a `.env` file automatically; export the variables in the process environment.

| Variable | Default | Meaning |
|---|---:|---|
| `PROVENABLY_DATA_DIR` | `./data` | SQLite database, blobs, certificates, and trust material |
| `BLOB_TTL_HOURS` | `24` | How long uploaded bytes are retained before deletion |
| `HASH_ONLY` | `false` | Delete uploaded bytes immediately after analysis when enabled |
| `MAX_UPLOAD_MB` | `200` | Upload/public-URL size limit |
| `PROVENABLY_API_KEYS` | empty | Comma-separated static keys; empty means open local-prototype access |
| `TRUST_ANCHORS_PEM` | `data/trust/anchors.pem` | Fetched official C2PA trust anchors |
| `TRUST_ALLOWED_PEM` | `data/trust/allowed.pem` | Optional allowed signer list |
| `INCLUDE_DEMO_TRUST_ANCHOR` | `true` | Trust the generated TEST CA for demo fixtures; disable for production |
| `OPENAI_VERIFY_*`, `GOOGLE_SYNTHID_*`, `GOOGLE_ACCESS_TOKEN` | empty | Manual vendor-verifier configuration |
| `URL_FETCH_TIMEOUT` | `15` | Public URL fetch timeout in seconds |

Current defaults and safeguards:

- blob TTL deletion, with `hash_only` available per scan or globally;
- public-URL fetching restricted to HTTP(S), size-capped, and guarded against private/loopback/link-local/reserved/multicast destinations;
- upload size limits and demo-path traversal protection;
- optional `X-API-Key` enforcement for the core scan creation/list/detail/report endpoints when keys are configured;
- no third-party analytics SDK in the shipped frontend.

Important prototype limitations:

- reports and extracted metadata remain in SQLite after source blobs expire;
- history is deployment-wide until authenticated ownership exists;
- report/preview capability URLs, rate limiting, streaming uploads, parser sandboxing, redirect re-resolution, and production auth still require hardening;
- uploaded files are currently read into memory by a single-process app;
- public deployment requires the production work in [`ARCHITECTURE.md`](ARCHITECTURE.md), not just a reverse proxy.

---

## Manual Integration Checklist

**Wired, visible, not faked.** Demoable does not mean production-complete. The following remain explicit integration work; reports expose them through `coverage.manual_modules` and `/v1/capabilities`:

| # | Integration | Required work |
|---:|---|---|
| 1 | Official C2PA trust list | **Done (2026-10-28)**: fetched 27 anchors into `data/trust/anchors.pem`; `official_c2pa_trust_list` now `true`. Schedule refresh + production anchors remain. |
| 2 | OpenAI Verify connector | Obtain partner API access; confirm the endpoint/response schema and configure the wired connector. |
| 3 | Google SynthID detector connector | Obtain partner/API access for the relevant image, video, audio, and text paths; configure endpoint and credentials. |
| 4 | Meta AudioSeal | Add the torch/torchaudio/AudioSeal model to an audio/GPU worker. |
| 5 | Meta Video Seal | Add per-frame torch inference to a video/GPU worker. |
| 6 | TrustMark / Stable Signature / WAM | Add model-specific decoders, weights, and worker dependencies. |
| 7 | Passive AI-image classifier | Deploy and calibrate a model service with published false-positive rates; cap conclusions at weak evidence. |
| 8 | Zero-shot text detector | Deploy a supported detector such as a Binoculars/Fast-DetectGPT-style service; expose score/calibration and never use it as sole evidence. |
| 9 | Audio-track demux for video | Add a controlled ffmpeg sidecar/binary, extract audio safely, and reuse the audio analyzers. |
| 10 | Visible-logo template matcher | Build maintained logo/template data and multi-scale detection logic. |
| 11 | Auth and billing | Add an identity provider, ownership, issued API keys, metering, and billing; the current static `X-API-Key` is only a deployment hook. |
| 12 | Production signing identity | Obtain a CA-issued claim-signing certificate, timestamping configuration, and protected key storage; demo certificates are TEST material and cannot confer public trust. |
| 13 | Editorial rule/registry maintenance | Re-verify platform/jurisdiction/generator research quarterly and update confidence/dates. Platform labels were refreshed 2026-10-24; other datasets retain their own review dates. |
| 14 | Queue, Postgres, object storage | Required before meaningful scan/video volume or multi-instance deployment. |

---

## Roadmap

| Stage | Scope | Status |
|---|---|---|
| **Detect** | Image, audio, video, document, and text scanning with graded evidence | **Live prototype** |
| **R0 — Remove foundation** | Layer-1 removal for JPG, PNG, WebP, PDF, DOCX, and text; lossless-first; post-removal re-scan and before/after diff; Layer-2 disclaimer; output blob TTL | **In progress (images/PDF/DOCX/text live, 2026-10-28)** |
| **R1 — Audio** | WAV, MP3, M4A/AAC, FLAC, and OGG tag/C2PA-chunk removal with samples untouched | Planned |
| **R2 — Video** | MP4, MOV, and WebM container/C2PA-box removal via ffmpeg stream-copy (lossless); falls back to not_configured when ffmpeg absent | **In progress (MP4/MOV/WebM live, 2026-10-28)** |
| **R3 — Platform-ready delivery** | Applied presets, native batch jobs, cleaned outputs, manifests/archives (zip + manifest.json) | **In progress (batch + manifest live, 2026-10-28)** |
| **R4 — Extended formats** | HEIC/AVIF (HEIF item tables rewritten, coded image copied verbatim), GIF (application extensions), TIFF (IFD metadata tags); C2PA + EXIF/XMP/IPTC/GPS removed, pixels byte-identical, re-scan verified | **Live (2026-10-28)** |

Near-term engineering priorities include fixing K1, adding CI, production authentication/ownership, official trust operations, durable jobs/storage, parser isolation, and report-schema versioning.

---

## Repository map

```text
.
├── README.md                 # Product, setup, API, and status overview
├── PHILOSOPHY.md             # Founder product law: Detect → Remove → Verify → Platform-ready
├── DESIGN.md                 # Approved brand, UX, component, and typography system
├── ARCHITECTURE.md           # Current system design, contracts, debt, and technical decisions
├── AGENTS.md                 # Operating rules, known issues, verification, and documentation discipline
├── WIREFRAME.md              # End-to-end interface blueprint
├── frontend/                 # SvelteKit 3 + Svelte 5 + TypeScript + Vite application
│   ├── src/routes/           # 17 product/reference/system pages and redirects
│   ├── src/lib/components/   # Brand, platform, upload, tab, notice, and evidence components
│   ├── src/lib/data/         # Platform labels, presets, and presentation catalogs
│   └── src/lib/assets/       # Canonical brand/platform artwork and untouched supplied sources
├── app/
│   ├── main.py               # FastAPI routes, static/legacy serving, URL guard, janitor
│   ├── pipeline.py           # Modality sniffing and analyzer orchestration
│   ├── aggregate.py          # Evidence priority and coverage model
│   ├── analyzers/            # C2PA, metadata, watermark, media, text, and vendor checks
│   ├── rules/                # Platform/jurisdiction/registry data and pure rules engine
│   ├── templates/ + static/  # Legacy fallback rendered only when the Svelte build is absent
│   └── db.py + config.py     # SQLite persistence and environment configuration
├── tools/                    # TEST cert, demo-fixture, and official trust-list utilities
├── tests/                    # Backend smoke, API, rules, Unicode, and detect-surface tests
├── mockup/                   # Historical approved static visual archive
├── zapier/DESIGN.md          # Source design research adapted into Provenably's system
└── run.sh                    # Setup/build/run entry point
```

Generated `data/`, `demo_assets/`, `frontend/node_modules/`, and `frontend/build/` are local runtime/build artifacts rather than product source.

---

## Documentation and contribution discipline

- Start with [`PHILOSOPHY.md`](PHILOSOPHY.md) for product boundaries and honesty rules.
- Use [`DESIGN.md`](DESIGN.md) and `/design-system` before changing UI, brand artwork, platform marks, or typography.
- Use [`ARCHITECTURE.md`](ARCHITECTURE.md) for backend contracts, scaling triggers, and technical debt.
- Use [`AGENTS.md`](AGENTS.md) for working agreements, decision logs, known issues, and required verification.
- Use [`frontend/README.md`](frontend/README.md) for frontend commands, proxy behavior, font delivery, and bundle budgets.
- Preserve originals for founder-supplied artwork; ship and document optimized derivatives separately.
- Update both platform-label data sources and their contract tests when destination behavior changes.
- Never make an unimplemented detector, removal, account, or billing feature appear successful in UI copy, fixtures, tests, or API responses.

Provenably’s differentiator is the proof attached to every claim: what was checked, what was found, how strong the evidence is, what could not be checked, and—when Remove ships—exactly what changed.
