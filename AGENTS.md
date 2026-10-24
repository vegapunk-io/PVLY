# AGENTS.md — Provenably (PVLY)

> **Read [`PHILOSOPHY.md`](PHILOSOPHY.md) first** (mission: Detect → Remove → Verify, all formats, platform-ready — founder clarification 2026-10-24, P-011/A-013), then this file. It is the binding operating manual for every human and AI agent
> working in this repository. Then read [`ARCHITECTURE.md`](ARCHITECTURE.md) (how the system
> is built) and [`DESIGN.md`](DESIGN.md) (how the product/UX works). Every decision and every
> non-trivial change MUST be recorded in these documents (see §9).
>
> Status: `0.1.0-prototype` · Last reviewed: 2026-10-24 · Owner: Founder / Engineering

---

## 1. What this product is

**Provenably** — AI content provenance & compliance. One graded **Provenance Report** per
file (image, audio, video, text). **Philosophy: DETECT → REMOVE → VERIFY, platform-ready**
(founder clarification 2026-10-24, `PHILOSOPHY.md`, P-011/A-013). NOTE the honest gap:
code is *currently* Detect-only (removal was deleted under the superseded P-010); restoring
removal is roadmap R0–R4 — do not describe removal as shipped until it is.

- **Detect:** C2PA/Content Credentials validation, metadata forensics, open watermark
  decoders, forensic context, text hygiene, platform-label preview, jurisdiction
  disclosure checklist, AI Watermark Registry (25 generators).
- **Detect only.** Provenably inspects content; it never modifies, strips, or "cleans" it
  (the text hidden-character cleaner in Text tools is unicode hygiene, not evasion).

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
4. **Removal scope (Layer 1 only).** Per `PHILOSOPHY.md §5`, removal means **container
   footprints** (C2PA manifests, EXIF/XMP/IPTC, container tags, doc props) — removed
   lossless-first and **proven by re-scan**. Content-embedded watermarks (Layer 2: SynthID,
   AudioSeal, VideoSeal, DWT-DCT…) are NEVER claimed removed; no "undetectable AI" positioning;
   removal ships only with user attestation + jurisdiction disclosure notes.
5. **Analyzer isolation.** One analyzer crashing must never kill a report (enforced in
   `app/pipeline.py`). New analyzers must not break this.
6. **Read-only scanning.** Analysis never modifies the uploaded file; the stored blob
   must remain byte-identical to the upload (its SHA-256 is part of the report).
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
| Tests | 18 tests collected: **13 pass, 5 FAIL** (see §7 — known bug K1, fix before new features) |
| CI / Docker / LICENSE | **Absent** — known gaps, tracked in ARCHITECTURE.md §13 |
| Deployment | Local/uvicorn only; no production deployment yet |
| Homepage | `/` renders **Scan** (Detect) — wedge DECIDED 2026-10-24 (DESIGN.md P-010) |

## 4. Repository map (where things live)

```
app/
  main.py            FastAPI app: UI routes + /v1 API, SSRF guard, API-key hook, janitor (527 LOC)
  pipeline.py        magic-byte sniffing, analyzer orchestration, persistence, TTL cleanup
  aggregate.py       evidence-graded conclusion + coverage (priority rules — ARCHITECTURE.md §6)
  db.py              SQLite (WAL): scans, events
  config.py          ALL configuration via env vars (12-factor)
  analyzers/         base.py (Signal/Context/Analyzer contract) + one module per signal family
  rules/             platforms.json (10) · jurisdictions.json (6) · registry.json (25) · engine.py
  templates/ static/ Jinja2 pages (10), style.css, app.js — NO build step (DESIGN.md)
tools/               dev_cert.py (TEST CA) · make_demo_assets.py (17 fixtures) · fetch_trust_list.py
tests/               test_smoke.py (pipeline + API + rules + detect-only surface)
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
   (analyzer contract §8, golden demo fixtures, rules-JSON schema).
3. **Tests are mandatory.** New behavior = new/extended test. Pipeline changes need a
   smoke conclusion test; route changes need a surface test (cf. `test_detect_only_surface`).
4. **Run the full suite** before proposing a change; report pass/fail honestly.
5. **Small, reviewable commits.** One logical change per commit, imperative subject line.
   (Do NOT repeat the single-mega-commit pattern of `beb4143`.)
6. **Document the decision** in the same change (§9). Undocumented decisions do not exist.
7. **No new dependency** without recording why (vs. stdlib/existing deps) in ARCHITECTURE.md's
   Decision Log, and noting CPU-only/GPU impact.
8. **No build step.** Frontend stays Jinja2 + vanilla JS/CSS unless a Decision Record says otherwise.
9. **Keep README and these three docs consistent.** If they disagree, fix
   them in the same change and note it in the Decision Log.

## 7. Known issues (do not re-discover; fix in priority order)

| # | Issue | Evidence | Required fix |
|---|---|---|---|
| K1 | Demo trust anchor not honored: signed fixtures grade `moderate`, expected `strong`. 5 failing tests (`test_pipeline_conclusions` for signed jpg/composite/wav/mp4). | `pytest -q` (2026-10-24). Suspect per-thread c2pa-rs settings in `app/analyzers/c2pa_an.py::_load_trust`. | Fix anchor loading; suite must be green before feature work. |
| K2 | No CI — K1 shipped unnoticed. | `.github/` absent. | Add GitHub Actions: install → dev_cert → demo assets → pytest. |
| K3 | ~~README contradictions (test count, "no removal", homepage)~~ **RESOLVED 2026-10-24** by the Detect-only decision: README/test count corrected, "no removal" is true again, homepage is Scan. | Fix in commit "Make Detect the product wedge…" | — |
| K4 | ~~Sanitized outputs never expire~~ **RESOLVED 2026-10-24** — sanitizer (and its blobs/table) removed entirely. | — | — |
| K5 | Auth open by default; report/preview are unauthenticated capability URLs (12-hex IDs); no rate limiting; ≤200 MB uploads read fully into memory. | `app/main.py: require_api_key`, `create_scan`, `scan_preview`. | Required before any public deploy (ARCHITECTURE.md §11). |
| K6 | Deprecated `@app.on_event("startup")`; unpinned `>=` deps, no lockfile. | `app/main.py:96`, `requirements.txt`. | Migrate to lifespan; pin/lock deps. |
| K7 | ~~Sanitizer attestation guardrails unimplemented~~ **RESOLVED 2026-10-24** — product surface removed; no attestation needed for a read-only detector. | — | — |

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

### 8.3 Removal features (Detect → Remove → Verify)
- Removal is a **core objective** (`PHILOSOPHY.md`), currently NOT implemented (deleted under
  superseded P-010/A-012; source recoverable at `beb4143`). Rebuild strictly per roadmap
  R0 (images/PDF/DOCX restore) → R1 audio → R2 video → R3 platform presets (PHILOSOPHY §8).
- Every removal path must: Detect first, strip Layer-1 only (§2.4), validate output
  decodes, be idempotent, Verify by re-scan (before/after diff + verdict), record
  hashes-in/out + fields removed, expire output blobs, and carry the Layer-2 disclaimer.
- `test_detect_only_surface` guards today's Detect-only code; replace it in the R0 change
  with surface tests for the restored routes (per A-013), never just delete it.

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
   Tests: <added/updated, suite result> · Docs updated: AGENTS/ARCHITECTURE/DESIGN/README
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
- [ ] README updated if user-facing claims changed
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
| 2026-10-24 | Founder decision: wedge = Detect. Sanitizer removed everywhere; rules §2.4/§2.6/§8.3 rewritten, K3/K4/K7 resolved, homepage = Scan. | Founder + Engineering |
| 2026-10-24 | Founder philosophy clarification supersedes the above: Detect → Remove → Verify, all formats, platform-ready. PHILOSOPHY.md added; §1/§2.4/§8.3 re-aimed; code gap (Detect-only until R0) recorded honestly. | Founder + Engineering |
