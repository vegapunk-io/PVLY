# AGENTS.md — Provenably (PVLY)

> **Read this file first.** It is the binding operating manual for every human and AI agent
> working in this repository. Then read [`ARCHITECTURE.md`](ARCHITECTURE.md) (how the system
> is built) and [`DESIGN.md`](DESIGN.md) (how the product/UX works). Every decision and every
> non-trivial change MUST be recorded in these documents (see §9).
>
> Status: `0.1.0-prototype` · Last reviewed: 2026-10-24 · Owner: Founder / Engineering

---

## 1. What this product is

**Provenably** — AI content provenance & compliance. One graded **Provenance Report** per
file (image, audio, video, text), plus a **Sanitizer** that strips container metadata/C2PA
and verifies the result.

- **Detect:** C2PA/Content Credentials validation, metadata forensics, open watermark
  decoders, forensic context, text hygiene, platform-label preview, jurisdiction
  disclosure checklist, AI Watermark Registry (25 generators).
- **Sanitize:** Detect → Strip → Verify for JPEG/PNG/WebP/PDF/DOCX (see `docs/PRD.md`).

## 2. Non-negotiable rules (never violate)

1. **Honesty of evidence.** Every signal carries an evidence grade
   (`strong | moderate | weak | none`). The aggregator NEVER lets a weak signal outrank a
   strong one. Passive/forensic signals NEVER decide the verdict.
2. **Never over-claim.** A report must NEVER state "human-made", "no watermark", or
   "watermark removed". It states which checks ran and what they found. Every report
   surfaces **coverage** (live vs. manual modules).
3. **No silent stubs.** Anything that cannot run honestly is implemented as a wired
   connector returning `not_configured` / `not_installed` **with the exact enabling step**
   in `manual_integration`. Never fake a detector result.
4. **Sanitizer scope.** Sanitizer removes **container metadata & C2PA manifests only**.
   Embedded statistical watermarks (SynthID, AudioSeal, VideoSeal, DWT-DCT, green-list)
   are NEVER claimed removable. Required copy in every UI/report path:
   *"Metadata removed. Embedded watermarks, if present, are not removed."*
5. **Analyzer isolation.** One analyzer crashing must never kill a report (enforced in
   `app/pipeline.py`). New analyzers must not break this.
6. **Lossless-first sanitization.** Default `reencode=False`; pixels byte-identical where
   the format allows. Sanitizing must be **idempotent** and the output must decode —
   on failure return an error, never a silently corrupted file.
7. **Privacy defaults.** Uploads deleted after `BLOB_TTL_HOURS` (default 24h);
   `hash_only=true` deletes bytes immediately after analysis. Never log file contents.
8. **Rules data is editorial.** Every entry in `app/rules/*.json` carries `confidence` +
   `last_verified`. Never present rule output as legal advice.
9. **No secrets in git.** Config only via environment variables (`app/config.py`,
   `.env.example`). `.env`, `data/`, `demo_assets/` are git-ignored — keep them out.

## 3. Current state snapshot (verified 2026-10-24)

| Item | State |
|---|---|
| Version | `0.1.0-prototype` (`app/config.py: APP_VERSION`) |
| Repo history | Single commit `beb4143` on `main`; work happens on feature/session branches |
| Code size | ~4,700 LOC Python · ~1,000 LOC templates/CSS/JS · 51 tracked files |
| Tests | 32 tests collected: **27 pass, 5 FAIL** (see §7 — known bug, fix before new features) |
| CI / Docker / LICENSE | **Absent** — known gaps, tracked in ARCHITECTURE.md §13 |
| Deployment | Local/uvicorn only; no production deployment yet |
| Homepage | `/` renders **Sanitize**; README still leads with Detect — **open product decision** (DESIGN.md §11) |

## 4. Repository map (where things live)

```
app/
  main.py            FastAPI app: UI routes + /v1 API, SSRF guard, API-key hook, janitor (527 LOC)
  pipeline.py        magic-byte sniffing, analyzer orchestration, persistence, TTL cleanup
  aggregate.py       evidence-graded conclusion + coverage (priority rules — ARCHITECTURE.md §6)
  db.py              SQLite (WAL): scans, sanitize_jobs, events
  config.py          ALL configuration via env vars (12-factor)
  analyzers/         base.py (Signal/Context/Analyzer contract) + one module per signal family
  sanitizer/         image.py (JPEG/PNG/WebP + dispatch), pdf.py (pikepdf), docx.py (lxml/OOXML)
  rules/             platforms.json (10) · jurisdictions.json (6) · registry.json (25) · engine.py
  templates/ static/ Jinja2 pages (10), style.css, app.js — NO build step (DESIGN.md)
tools/               dev_cert.py (TEST CA) · make_demo_assets.py (17 fixtures) · fetch_trust_list.py
tests/               test_smoke.py · test_sanitizer.py · test_sanitizer_phase2.py
docs/PRD.md          Sanitizer PRD (phases, acceptance criteria)
README.md            User-facing overview + 14-item Manual Integration Checklist
```

## 5. Setup, run, test (exact commands)

```bash
# First-time setup (CPU-only, ~1 min). run.sh does all of this for you:
pip install -r requirements.txt
python tools/dev_cert.py            # TEST root CA + claim-signing cert -> data/certs/
python tools/make_demo_assets.py    # 17 demo fixtures -> demo_assets/
uvicorn app.main:app --host 0.0.0.0 --port 8000
# or simply: ./run.sh

pytest -q                           # full test suite (~3 s)
curl -s localhost:8000/health       # {"ok": true, ...}
curl -s localhost:8000/v1/capabilities   # live vs manual integration status
```

- UI: `http://localhost:8000` · OpenAPI: `/api/docs` · Health: `/health`
- Demo text-watermark key: `demo-key`
- Config: copy `.env.example` → `.env` (see ARCHITECTURE.md §10 for every variable).

## 6. How to make changes (workflow rules)

1. **Branch.** Never commit directly to `main`. Work on the assigned branch.
2. **Read before writing.** Identify the owning module from §4; follow its existing pattern
   (analyzer contract §8, sanitizer golden fixtures, rules-JSON schema).
3. **Tests are mandatory.** New behavior = new/extended test. Sanitizer changes need a
   golden-fixture test incl. idempotence. Pipeline changes need a smoke conclusion test.
4. **Run the full suite** before proposing a change; report pass/fail honestly.
5. **Small, reviewable commits.** One logical change per commit, imperative subject line.
   (Do NOT repeat the single-mega-commit pattern of `beb4143`.)
6. **Document the decision** in the same change (§9). Undocumented decisions do not exist.
7. **No new dependency** without recording why (vs. stdlib/existing deps) in ARCHITECTURE.md's
   Decision Log, and noting CPU-only/GPU impact.
8. **No build step.** Frontend stays Jinja2 + vanilla JS/CSS unless a Decision Record says otherwise.
9. **Keep README, `docs/PRD.md` and these three docs consistent.** If they disagree, fix
   them in the same change and note it in the Decision Log.

## 7. Known issues (do not re-discover; fix in priority order)

| # | Issue | Evidence | Required fix |
|---|---|---|---|
| K1 | Demo trust anchor not honored: signed fixtures grade `moderate`, expected `strong`. 5 failing tests (`test_pipeline_conclusions` for signed jpg/composite/wav/mp4). | `pytest -q` (2026-10-24). Suspect per-thread c2pa-rs settings in `app/analyzers/c2pa_an.py::_load_trust`. | Fix anchor loading; suite must be green before feature work. |
| K2 | No CI — K1 shipped unnoticed. | `.github/` absent. | Add GitHub Actions: install → dev_cert → demo assets → pytest. |
| K3 | README contradictions: "17 tests" (actually 32); "No removal/evasion anywhere" (Sanitizer exists); homepage described as Scan (actually Sanitize). | `README.md:31,127`; `app/main.py:113`. | Resolve once product wedge is decided (DESIGN.md §11). |
| K4 | Sanitized outputs never expire (janitor only cleans scan blobs). | `app/db.py: expired_blobs` scans `scans` only. | Add expiry to `sanitize_jobs` or ephemeral mode. |
| K5 | Auth open by default; report/preview/download are unauthenticated capability URLs (12-hex IDs); no rate limiting; ≤200 MB uploads read fully into memory. | `app/main.py: require_api_key`, `create_scan`, `sanitize_download`, `scan_preview`. | Required before any public deploy (ARCHITECTURE.md §11). |
| K6 | Deprecated `@app.on_event("startup")`; unpinned `>=` deps, no lockfile. | `app/main.py:96`, `requirements.txt`. | Migrate to lifespan; pin/lock deps. |
| K7 | PRD guardrails unimplemented: no user attestation in Sanitize UI. | `docs/PRD.md §13` vs `app/templates/sanitize.html`. | Implement before marketing Sanitizer publicly. |

## 8. Contracts you must follow

### 8.1 Adding / changing an analyzer
- Subclass `Analyzer` (`app/analyzers/base.py`): set `name`, `modalities`; implement
  `available() -> (bool, reason)` and `run(ctx) -> list[Signal]`.
- Emit `Signal(kind, name, status, evidence_grade, summary, data, method, manual_integration)`.
  `status` ∈ `detected | absent | info | inconclusive | error | not_configured | not_installed | skipped`.
- Forensic/passive signals: `kind` = `forensics`/`passive`, grade ≤ `weak`, never decisive.
- Register the instance in `pipeline.ANALYZERS` (order matters only for timings/display).
- If it needs a manual step: return `not_configured`/`not_installed` with the exact enabling
  step, add it to `/v1/capabilities` (`app/main.py: capabilities()`) and to the README
  Manual Integration Checklist. Add a test.

### 8.2 Changing aggregation
- Edit `app/aggregate.py` only. Preserve priority order (ARCHITECTURE.md §6) and the rule
  "weak never outranks strong". Add a conclusion test per new `provenance_class`.
- `provenance_class` values are a public API — never rename an existing one.

### 8.3 Changing the sanitizer
- Entry: `sanitizer.sanitize_bytes(data, filename, policy) -> (bytes, report)` and
  `sanitizer.inspect_bytes(data)`. Formats dispatch in `app/sanitizer/image.py`.
- Preserve: lossless default, idempotence, output-decodes validation, Verify (re-scan diff),
  `RemoveReport` schema (`removed/kept/failed/verify/watermark_note`).
- New format = new module + golden fixture + idempotence test + PRD acceptance-criteria update.

### 8.4 Changing rules/registry data
- JSON in `app/rules/`; pure functions in `app/rules/engine.py` (no I/O in logic paths).
- Every edited entry: bump `last_verified`, set honest `confidence`, add/refresh source notes.
- `engine.py` changes require `test_disclosure_engine`-style unit tests.

### 8.5 Changing API / DB
- Routes in `app/main.py`; JSON under `/v1/...`; auth via `Depends(require_api_key)` on
  anything that reads/writes user data (UI/demo/registry reads are intentionally public).
- DB schema is flat on purpose (`app/db.py`); any new table/column must keep the
  SQLite→Postgres migration path trivial (no SQLite-only types).

## 9. Decision & review documentation (MANDATORY)

**Every** product, design, architecture, or process decision — and every non-trivial
development change — must be recorded **in the same change** using this structure, so it
can be reviewed later:

1. **Decision Log** — chronological table maintained at the end of each document:
   `ARCHITECTURE.md §14` (technical), `DESIGN.md §12` (product/UX). One row per decision:
   `ID | Date | Decision | Context/Why | Alternatives rejected | Consequences | Status (Accepted/Superseded by …/Open)`.
2. **Decision Record template** (for significant decisions, paste into the relevant log or
   `docs/decisions/DR-<id>-<title>.md`):

   ```markdown
   ## DR-XXX — <title>
   - Date / Owner / Status:
   - Context (problem, constraints, evidence):
   - Decision:
   - Alternatives considered & why rejected:
   - Consequences (what becomes easier/harder, risks, follow-ups):
   - Review (reviewer, date, outcome):
   ```

3. **Change Review block** — required in every PR / change summary:

   ```markdown
   Change: <what> · Why: <linked decision DR-XXX>
   Touched: <modules/routes/schema> · API/UX impact: <none|describe>
   Tests: <added/updated, suite result> · Docs updated: AGENTS/ARCHITECTURE/DESIGN/README/PRD
   Risks & rollback: <describe>
   ```

4. **Open decisions** are tracked as `Status: Open` rows (e.g. product wedge, DESIGN.md §11)
   with an owner and revisit date. Never silently resolve an Open decision in code.

## 10. Definition of Done

- [ ] Behavior implemented in the owning module following §8 contracts
- [ ] Tests added/updated; `pytest -q` run and result reported
- [ ] No HONESTY rule (§2) weakened; new stubs are wired + visible in `/v1/capabilities`
- [ ] API/schema changes reflected in ARCHITECTURE.md §7–§9
- [ ] UX/copy changes reflected in DESIGN.md (§5–§8)
- [ ] Decision Log row added (§9); superseded decisions marked, not deleted
- [ ] README / PRD updated if user-facing claims changed
- [ ] No secrets, no `data/`/`demo_assets/` files committed

## 11. Manual-integration discipline

The 14 items in `README.md` → "Manual Integration Checklist" (trust list, OpenAI Verify,
Google SynthID, AudioSeal, Video Seal, TrustMark/Stable Signature/WAM, passive classifier,
text detector, ffmpeg demux, logo matcher, auth/billing, production signing, rules refresh,
queue/Postgres/S3) are the canonical backlog of "wired but not live". Completing one means:
config → connector → report rendering → `/v1/capabilities` flip → test → Decision Log row.

## 12. Document history

| Date | Change | Author |
|---|---|---|
| 2026-10-24 | Initial creation from full codebase audit (structure, contracts, known issues K1–K7, decision/review system). | Engineering (agent-assisted), pending founder review |
