# Provenably — AI content provenance & compliance (prototype 0.1.0)

One graded **Provenance Report** per file (image, audio, video, text) that merges:

* **Content Credentials (C2PA)** validation via `c2pa-rs` — trust state, digital source type, actions, ingredients, hard-binding mismatch (tamper) detection; JPEG/PNG/WAV/MP4
* **Metadata forensics** — EXIF, XMP/IPTC `DigitalSourceType`, PNG text (A1111 `parameters`), generator strings, JPEG segment map
* **Open watermark decoders** — DWT-DCT `invisible-watermark` as shipped by SD 1.x/2.x and diffusers' SDXL pipeline (pure numpy/pywt port, bit accuracy + binomial p-value); per-frame scan for video
* **Forensic context** (never used for the verdict) — JPEG quality, canonical generator sizes, noise; audio bandwidth/flatness; MP4 box structure
* **Text** — hidden-character scan + cleaner, transparent stylometric features, keyed green-list watermark z-test (educational Lab)
* **Rules engine** — platform label preview (Instagram, Facebook, Threads, YouTube, TikTok, LinkedIn, X, Pinterest, Google, KDP) and a deployer disclosure checklist (EU AI Act Art. 50, California SB 942/AB 853, India SGI rules 2026, China GB 45438-2025, Korea, US federal)
* **AI Watermark Registry** — 25 generators with visible/invisible/C2PA/IPTC/detector facts, confidence and last-verified dates

Everything that cannot run honestly in a CPU-only prototype (vendor verifiers, torch detectors, GPU classifiers,
official trust list, auth/billing, production signing) is **wired in and reported as `not_configured` /
`not_installed`** in every report, with the exact enabling step. See *Manual integration checklist* below.

---

## Run

```bash
cd provenably
pip install -r requirements.txt          # CPU only; ~1 min
python tools/dev_cert.py                 # TEST root CA + claim-signing cert -> data/certs/
python tools/make_demo_assets.py         # 17 fixtures -> demo_assets/
(cd frontend && npm ci && npm run build) # SvelteKit production UI -> frontend/build/
uvicorn app.main:app --host 0.0.0.0 --port 8000
# or simply: ./run.sh
```

Open http://localhost:8000 — Landing · Scan · Report · Remove (R0 pending) · Batch · Presets · Registry · Rules · Tools · Lab · API.
Interactive OpenAPI at `/api/docs`. Backend tests: `pytest -q`. Frontend gate: `cd frontend && npm run verify`.

## Stack (deliberately boring and scalable)

| Layer | Prototype | Scale-up path (no route changes) |
|---|---|---|
| API | FastAPI + Pydantic | same JSON routes behind nginx/Cloud Run |
| UI | SvelteKit/Svelte 5 + TypeScript, static build served by FastAPI | move `frontend/build` to a CDN/static host without API route changes |
| Jobs | `BackgroundTasks` → `pipeline.run_scan(scan_id)` | arq/Celery/RQ worker calling the same function; GPU workers subscribe to the same queue |
| Storage | SQLite (WAL) + local blobs with TTL janitor | Postgres via SQLAlchemy (schema is flat), S3/GCS blobs with lifecycle rules |
| Provenance | `c2pa-python` 0.38 (c2pa-rs 0.91) | same library; add official trust list + remote-manifest fetch |
| Media | Pillow, OpenCV-headless, PyWavelets, numpy | same; ffmpeg sidecar for audio demux |
| Auth | `X-API-Key` dependency, enforced only when `PROVENABLY_API_KEYS` set | replace `require_api_key()` with JWT/IdP + Stripe metering |

Design rules baked in: analyzers are isolated (one crash never kills a report), every signal carries an
**evidence grade** (`strong / moderate / weak / none`) and the aggregator never lets a weak signal outrank a strong
one; passive/forensic signals **never** decide the verdict; each report shows **coverage** (what ran vs. what is
manual) so a "clean" result cannot be over-read.

## API in 60 seconds

```bash
# synchronous scan
curl -s -F "file=@photo.jpg" -F "wait=true" localhost:8000/v1/scans | jq .conclusion
# async
curl -s -F "file=@clip.mp4" localhost:8000/v1/scans          # -> {"id": "...", "status": "queued"}
curl -s localhost:8000/v1/scans/<id>                          # -> status + report
# text, with the Lab key
curl -s -F "text=<marked.txt" -F "greenlist_key=demo-key" -F "wait=true" localhost:8000/v1/scans
# URL (SSRF-guarded: public hosts only)
curl -s -F "url=https://example.com/image.jpg" -F "wait=true" localhost:8000/v1/scans
# demo fixture
curl -s -X POST "localhost:8000/v1/scans/demo/ai_generated_tampered.jpg?wait=true" | jq .conclusion
# rules
curl -s -X POST localhost:8000/v1/disclosure/check -H 'content-type: application/json' \
  -d '{"content_type":"video","is_ai_generated":true,"depicts_real_person":true}'
curl -s -X POST localhost:8000/v1/platforms/preview -H 'content-type: application/json' -d '{"scan_id":"<id>"}'
curl -s localhost:8000/v1/registry?modality=image
curl -s localhost:8000/v1/capabilities      # live vs manual in this deployment
```

Report JSON (abridged): `conclusion{provenance_class,label,evidence_grade,decisive_signal,notes}`,
`signals[]{kind,name,status,evidence_grade,summary,data,method,manual_integration}`, `coverage`,
`platform_preview[]`, `facts`, `trust_sources`, `timings`, `file{sha256,…}`.

Provenance classes: `ai_generated_declared`, `ai_assisted_declared`, `captured_declared`, `signed_no_source_type`,
`tampered_after_signing`, `ai_generated_watermark`, `ai_generated_metadata`, `text_watermark_detected`,
`text_hidden_characters`, `no_provenance_signal`.

## Demo fixtures (what each proves)

| File | Expected conclusion |
|---|---|
| `ai_generated_signed.jpg` | ai_generated_declared · strong |
| `camera_capture_signed.jpg` | captured_declared · strong |
| `ai_edited_composite_signed.jpg` | ai_assisted_declared · strong (ingredient = signed camera file) |
| `ai_generated_tampered.jpg` | tampered_after_signing · strong (`assertion.dataHash.mismatch`) |
| `ai_generated_stripped.jpg` | no_provenance_signal (what a screenshot leaves) |
| `iptc_ai_tagged_no_c2pa.jpg`, `a1111_parameters.png` | ai_generated_metadata · weak |
| `sdxl_watermarked.png` | ai_generated_watermark · moderate (100 % bit accuracy) |
| `sdxl_watermarked_q75.jpg` | no_provenance_signal — JPEG chroma subsampling destroys the mark (honest fragility demo) |
| `text_hidden_chars.txt` | text_hidden_characters · weak |
| `text_greenlist_marked.txt` | text_watermark_detected · moderate (key `demo-key`) |
| `speech_like_signed.wav`, `clip_signed.mp4` | ai_generated_declared · strong |

All signatures use the **TEST** certificate (`issuer: Provenably Demo`); the demo root CA is a trust anchor only
because `INCLUDE_DEMO_TRUST_ANCHOR=true`. Real-world credentials (ChatGPT, Gemini, Firefly, Pixel) validate as
*Valid / moderate* until the official trust list is installed (below).

---

## MANUAL INTEGRATION CHECKLIST

Each item is already wired (config → connector → report rendering) and visible in `/docs-guide` and `/v1/capabilities`.

| # | Module | Where | What to do |
|---|---|---|---|
| 1 | **Official C2PA trust list** | `tools/fetch_trust_list.py` → `data/trust/anchors.pem` | Run the script (verify the bundle URL against the C2PA conformance programme); restart. Optionally add your own enterprise CA. |
| 2 | **OpenAI Verify connector** (SynthID image/audio + C2PA) | `app/analyzers/vendor_an.py`, env `OPENAI_VERIFY_API_KEY/_ENDPOINT` | Confirm endpoint path + response schema in OpenAI docs; connector normalises `detected`/`watermark_detected`. |
| 3 | **Google SynthID Detector connector** | `vendor_an.py`, env `GOOGLE_ACCESS_TOKEN`, `GOOGLE_SYNTHID_ENDPOINT` | Public web tool exists (7 Oct 2026); API access is partner-gated — apply, then fill env. |
| 4 | **AudioSeal** (Meta, open) | `audio_an.py` auto-enables | `pip install torch torchaudio audioseal` on the worker. |
| 5 | **Video Seal** (Meta, open) | `video_an.py` placeholder | `pip install torch` + videoseal; call extractor where marked. |
| 6 | **TrustMark** (Adobe), **Stable Signature**, **WAM** | `imwm_an.py` placeholders | `pip install trustmark`; Stable Signature/WAM need Meta weights. |
| 7 | **Passive AI-image classifier** | `forensics_an.py` placeholder | Deploy UnivFD/CLIP-ViT or GenImage-trained model on a GPU service; publish calibrated FPR per domain; report as *weak* evidence max. |
| 8 | **Zero-shot text detector** (Binoculars / Fast-DetectGPT) | `text_an.py` placeholder | Two 7B models on GPU; expose score + FPR; still never sole evidence. |
| 9 | **Audio track demux for video** | `video_an.py` | `apt-get install ffmpeg`; extract WAV and reuse audio analyzers. |
| 10 | **Visible-logo template matcher** | `video_an.py` note | Collect logo crops per generator into `data/templates/<tool>/`; cv2 multi-scale matchTemplate. |
| 11 | **Auth & billing** | `app/main.py::require_api_key` | Static keys via `PROVENABLY_API_KEYS`, or swap for JWT/IdP + Stripe usage metering (`$0.02 image / $0.03 text / $0.08 audio-min / $0.15 video-min` from the blueprint). |
| 12 | **Production signing** (for the "sign before publishing" feature) | `c2pa_an.sign_file` | CA-issued claim-signing cert (claimSigning EKU), RFC 3161 TSA URL, KMS-backed private key. |
| 13 | **Rules refresh** | `app/rules/*.json` | Entries carry `confidence` + `last_verified`; re-verify quarterly (flagged: CA SB 942 user threshold, SynthID third-party API). |
| 14 | **Queue + Postgres + object storage** | `pipeline.run_scan`, `db.py` | Needed above a few hundred scans/day or any video volume. |

## Security & privacy defaults

* URL ingestion resolves DNS and rejects private/loopback/link-local/multicast targets; http(s) only; size cap.
* Uploads are deleted after `BLOB_TTL_HOURS` (default 24 h) by a janitor thread; `hash_only=true` deletes immediately after analysis and keeps only SHA-256 + report.
* Reports never state "human-made" or "no watermark" — only which checks ran and what they found.
* The Remove backend is not implemented yet (PHILOSOPHY R0); the UI never claims a server-side removal succeeded. The text cleaner is hygiene only and does not touch statistical watermarks.

## Layout

```
app/
  main.py            FastAPI routes (UI + /v1 API), SSRF guard, API-key hook, janitor
  pipeline.py        magic-byte sniffing, analyzer orchestration, persistence, TTL cleanup
  aggregate.py       evidence-graded conclusion + coverage
  db.py              SQLite schema/helpers (scans, events)
  config.py          env-driven settings
  analyzers/         base.py (Signal/Context), c2pa_an, jumbf, metadata_an, dwtdct, imwm_an,
                     forensics_an, audio_an, video_an, text_an, vendor_an
  rules/             platforms.json, jurisdictions.json, registry.json, engine.py
  templates/, static/  legacy Jinja fallback
frontend/              SvelteKit production frontend (src/routes, src/lib, scripts/check-bundle-budget.mjs)
tools/               dev_cert.py, make_demo_assets.py, fetch_trust_list.py
tests/test_smoke.py  pipeline + API + rules tests
```
