# DESIGN.md — Provenably (PVLY)

> Product & UX/UI design as it **currently exists** (`0.1.0-prototype`, verified 2026-10-24).
> Companion docs: [`AGENTS.md`](AGENTS.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md) ·
> **Read [`PHILOSOPHY.md`](PHILOSOPHY.md) first** — founder philosophy clarified 2026-10-24 (P-011): Detect → Remove → Verify, all formats, platform-ready. Current code is temporarily Detect-only (see PHILOSOPHY §10 gap note).
> **Every product/UX decision must be logged in §12.** Open decisions live in §11.

---

## 1. Product definition (current)

**Provenably — AI content provenance & compliance.** One-liner in force:
*"One graded Provenance Report per file"* (README).

**Philosophy CLARIFIED — DETECT → REMOVE → VERIFY (founder, 2026-10-24, P-011, see
`PHILOSOPHY.md`).** Detect is the front door; removal of C2PA/metadata/AI footprints across
image/video/audio/document/text, verified and platform-ready, completes the job. This
supersedes the same-day Detect-only call (P-010); until roadmap R0 lands, shipped code is
Detect-only and copy must not promise removal.

## 2. Target personas (Detect-only, revised 2026-10-24 — unvalidated)

| Persona | Need | Primary surface |
|---|---|---|
| Newsroom / OSINT | Verify content provenance before publishing | Scan + Report |
| Creator / influencer | Know how platforms will label a file before posting | Scan + Rules |
| Compliance / publisher | EU/CA/India/China/Korea disclosure readiness | Detect + Rules |
| Platform / moderation | Understand what provenance signals arrive with uploads | Detect + Registry |
| Developer | Programmatic scan + report via API | `/v1` API + `/api/docs` |

## 3. Design principles (binding)

1. **Show evidence, not verdicts on authorship.** Footer on every page: *"Reports describe
   signals and their evidence grade; they are not a verdict on authorship… not legal advice."*
2. **Grade everything.** Conclusion always pairs a human label with its evidence grade and
   the decisive signal; weak evidence is visually weaker (§7 conclusion block).
3. **Coverage is part of the result.** what ran vs. what's `not_configured` (dashed "manual"
   tags) appears on the report and on *API & status* — a clean result must show its limits.
4. **Honest limits up front.** The Scan page states coverage limits before use (§8);
   fragility is demonstrated, not hidden (the q75-JPEG watermark-loss demo fixture).
   Detection is read-only — nothing in the product modifies user files.
5. **Flat, minimal, fast.** No gradients, no decorative shadows, system fonts, no build
   step, no tracking/analytics (current state), tables over cards for data density.
6. **Prototype is labelled.** The `prototype` chip in the nav and TEST-signer labelling stay
   until trust list + production signing are real.

## 4. Information architecture (current pages)

Nav (`app/templates/base.html`): **Provenably** *"AI content provenance & compliance"* ·
Scan · Demo files · Registry · Rules · Text tools · Lab · API & status · `prototype` chip.

| Route | Template | Purpose (H1) |
|---|---|---|
| `/` = `/scan` | `scan.html` | "Detect AI provenance" — tabs (File dropzone / Text / URL) posting to `/v1/scans`, hash-only + green-list options,"What gets checked", "Honest limits", recent scans |
| `/demo` | `demo.html` | "Demo files" — 17 fixtures, one-click scan (primary demo entry) |
| `/report/{id}` | `report.html` | Provenance Report: conclusion block, signals, coverage, platform preview, raw JSON |
| `/registry`, `/registry/{slug}` | `registry*.html` | "AI watermark & provenance registry" (25) · "Does {tool} watermark or sign its output?" |
| `/laws` | `laws.html` | "Disclosure checklist & platform rules" (6 jurisdictions, 10 platforms) |
| `/tools` | `tools.html` | "Hidden-character scanner & cleaner" (unicode hygiene) |
| `/lab` | `lab.html` | "Lab: how a statistical text watermark works" (green-list generate/detect) |
| `/docs-guide` | `docs.html` | "API & deployment status" — live vs manual capabilities, curl examples |

## 5. Core user flows (current)

**F1 Scan:** Scan page tabs (file/text/URL) or Demo files → HTML form posts to `/v1/scans` →
303 redirect to report page → polls until done →
conclusion (label + grade + decisive signal) → signals (expandable raw data) → coverage →
platform-label preview → download `report.json`.
~~**F2 Sanitize**~~ — REMOVED 2026-10-24 (P-010). No flow modifies files.
**F3 Check a generator:** Registry → filter by modality → generator page (visible mark /
invisible watermark / C2PA / IPTC / public detector / robustness + confidence + last-verified).
**F4 Compliance check:** Rules page / `POST /v1/disclosure/check` → per-jurisdiction open items.
**F5 Text hygiene:** paste text → hidden-char scan → cleaned output (keep-joiners / ASCII-dash options).
**F6 Learn:** Lab → generate green-list-marked text → detect with right/wrong key (z-score).

## 6. Visual design system (exact, from `app/static/style.css`)

**Tokens**
```css
--ink:#141414  --muted:#5f6368  --line:#e3e3e3  --soft:#f5f5f4
--accent:#1a4fd6  --ok:#136f3a  --warn:#a65d00  --bad:#b3261e
--sans: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif
--mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace
```
**Type:** base 16px, line-height 1.5 · H1 1.6rem/600 · H2 1.15rem/600 · H3 1rem/600 ·
`.small` .86rem · mono at .86em for hashes/IDs/code.
**Layout:** `.wrap` max-width **1040px**, 20px gutters · nav 52px, brand + items + spacer +
prototype chip (tagline hidden ≤1100px) · `.grid2`/`.grid3` collapse to 1 col ≤760px ·
main padding 28px/60px · footer with disclaimer + OpenAPI/health links.
**Brand mark:** inline SVG favicon — black square, white check path (no logo file exists yet).
**Motion:** only the indeterminate `.progress` slide animation; nothing else animates.

## 7. Component inventory (reuse these; don't invent new patterns)

| Component | Usage / semantics |
|---|---|
| `.conclusion` block | Report headline. Left border encodes grade: `strong`=green, `moderate`=blue, `weak`=amber, `none`=gray, `tampered`=red. **This mapping is a product-wide convention.** |
| `.tag` (`ok/warn/bad/accent/manual`) | Statuses & grades; `manual` = dashed border = not-configured module |
| `.dot` (ok/warn/bad/accent) | Inline status dots in lists |
| `.signal` row | One analyzer signal: name, meta (method/ms), summary, `.how` = manual-integration instruction (amber) |
| `details/summary` + `pre` | Progressive disclosure of raw signal JSON (max-height 420px) |
| `.kv` definition grid (180px labels) | File facts (sha256, mime, size) |
| `table` | Registry, rules, recent jobs — uppercase muted headers, row hover `#fafaf9` |
| `.drop` dropzone | Dashed border; `.over` → accent. File input inside (accessible fallback) |
| `.notice` / `.notice.info` | Warnings (amber tint) / info (blue tint) — used for honest-limits copy |
| `.box`, `.row`, `.steps` (numbered) | Side panels ("What gets removed", "Honest limits"), how-it-works steps |
| Buttons | Primary = ink/black fill; `.secondary` = white; `.small` variant. Focus: 2px accent outline |
| Forms | `.check` checkbox rows; labels above inputs; mono textarea for text tools |

Client JS (`app/static/app.js`, 185 LOC, no framework): `window.Provenably` namespace with
per-page initializers (`toolsPage()`, `labPage()`, `disclosurePage()`) plus generic tabs /
dropzone (`#drop`+`#file-form`, used by Scan) and report polling; `fetch` to `/v1`, `esc()` helper
— **always** escape interpolated values; the few `innerHTML` sinks rely on it.

## 8. Copy & voice rules (binding)

- Tone: precise, forensic, understated. State method + grade + limits in the same breath.
- **Forbidden claims:** "human-made", "100% AI/human", "no watermark", "watermark removed",
  "undetectable", any legal-advice phrasing. Use: "No provenance signal found **by the
  checks that ran**", "Absence of provenance is not evidence of human origin".
- **No removal language anywhere.** Never imply Provenably can strip metadata/manifests or
  remove/degrade watermarks, or help evade disclosure laws/platform labels. (Detect-only, P-010.)
- **Required labels:** TEST signer disclosed ("issuer: Provenably Demo"); `prototype` chip;
  rules data carries "researched 2026-10-14 · not legal advice".
- Provenance classes render their human `label` (e.g. "AI-generated (declared in a Content
  Credential)"), never the raw slug alone.

## 9. Accessibility & responsive (current state)

Present: semantic landmarks (nav/main/footer), native controls, visible focus outlines,
color+text pairing on grades (grade word always shown, not color-only — keep this),
breakpoints 1100px/760px, viewport meta.
Gaps (not yet audited): no ARIA live regions for async result injection, dropzone is
mouse-first (file input is the fallback), contrast of `--muted` on white unverified,
no reduced-motion handling for `.progress`. Any redesign must close these before launch.

## 10. Content assets (current)

- **Registry:** 25 generators (image/video/audio/text), fields per §5-F3, `confidence` +
  `last_verified` 2026-10-14, `_meta` disclaims removal techniques ("public answers only").
- **Rules:** 10 platforms (Instagram…KDP), 6 jurisdictions (EU, California, India SGI 2026,
  China, Korea, US federal), each `confidence`/`last_verified`. Quarterly refresh owed.
- **Demo fixtures (17):** the teaching set — signed AI / signed camera / composite w/
  ingredient / tampered / stripped / IPTC-only / A1111 PNG / SDXL watermark (+q75 loss) /
  clean text / hidden-char text / green-list text / signed+plain WAV / signed+plain MP4.

## 11. Open product/design decisions (must be resolved + logged, owner: Founder)

| ID | Decision needed | Why it blocks | Revisit |
|---|---|---|---|
| D1 | **Wedge — RE-CLOSED 2026-10-24 by founder clarification: DETECT → REMOVE → VERIFY** (PHILOSOPHY.md, P-011). Supersedes the same-day Detect-only decision; R0 restore pending founder go-ahead. | Positioning/copy must be re-aimed when R0 ships | Closed (direction) |
| D2 | ~~Sanitizer attestation/legal UX~~ **CLOSED 2026-10-24** — surface removed; moot for a read-only detector. | — resolved — | Closed |
| D3 | Monetization UX: per-scan vs subscription; where the paywall appears (blueprint only: $0.02 img / $0.03 text / $0.08 audio-min / $0.15 video-min). | Auth/billing scope | Before billing build |
| D4 | ~~Sanitizer batch/platform-preset UX~~ **CLOSED 2026-10-24** (P-010). *Replacement open item:* batch **scanning** UX (multi-file upload → report list/ZIP of JSON) — unspec'd. | Newsroom/moderation workflow | When batch is prioritized |
| D5 | HEIC/AVIF/RAW detection coverage + messaging (mobile photos currently sniff-only). | Creator persona coverage | v2 scoping |
| D6 | Brand: formal logo, landing/pricing pages, SEO treatment of Registry pages. | No marketing surface exists | With D1 |

## 12. Decision Log (append-only — see AGENTS.md §9)

| ID | Date | Decision | Context / Why | Alternatives rejected | Consequences | Status |
|---|---|---|---|---|---|---|
| P-001 | ≤2026-10-14 | One graded Provenance Report merges all signals; "not a verdict on authorship" | Trust through evidence transparency | Binary AI/not-AI score | Footer/report copy rules §8 | Accepted |
| P-002 | ≤2026-10-14 | Grade color-coding on conclusion block (strong green → tampered red) + grade word always in text | Scanability without color-only meaning | Score bars/percentages | Convention locked in §7 | Accepted |
| P-003 | ≤2026-10-14 | Coverage & manual modules shown in-product (`/docs-guide`, dashed tags) | Never let "clean" over-claim (ARCH A-003) | Hiding roadmap stubs | Capabilities page is a sales-honesty asset | Accepted |
| P-004 | ≤2026-10-14 | Flat/minimal visual system: no gradients/shadows, system fonts, tables-first | Forensic tool credibility; zero build | Marketing-style SaaS UI | Tokens §6 are the design system until D6 | Accepted |
| P-005 | ≤2026-10-14 | Registry as public, per-generator Q&A pages with confidence + last-verified | Reference/SEO value; "never documents removal" | Keeping data API-only | Quarterly re-verification obligation | Accepted |
| P-006 | ≤2026-10-14 | Demo fixtures as first-class product surface (17, one-click) | Teach trust/tamper/fragility without uploads | Upload-only empty state | Fixtures double as tests (ARCH §12) | Accepted |
| P-007 | 2026-10-23 (PRD) | Add Sanitize with Detect→Strip→Verify + explicit non-goals (no watermark-removal claims, no forgery/DRM) | Creator/privacy demand; differentiator = verified diff | Strip-only tool; watermark "removal" | Created wedge tension D1 + guardrail debt D2 | **Superseded by P-010** |
| P-008 | ≤2026-10-14 | Homepage `/` renders Sanitize (README still Detect-first) | *Undocumented at the time — recorded here retroactively* | Scan-first homepage | Top-of-funnel implies Sanitizer wedge; contradicts README | **Superseded by P-010** |
| P-012 | 2026-10-24 | **Mockup-first: complete end-to-end frontend locked before backend development** — Evolved Flat Forensic (light), **violet accent `#6D28D9` replaces blue** (incl. moderate grade), Inter + JetBrains Mono, 1180px wrap, radius 10/7px; 15-page clickable mockup in `mockup/` + `WIREFRAME.md` spec (sitemap, per-page sections/states, backend contract, conversion plan) | Founder decisions (direction/palette/scope/deliverable chosen 2026-10-24): backend must later only connect to finished pages | Build backend first; ad-hoc UI during development | Founder approval gate in WIREFRAME §10; production `style.css`/templates unchanged until conversion step | Accepted (approval pending) |
| P-009 | 2026-10-24 | Adopt this design doc + mandatory decision logging before further development | Founder directive (AGENTS.md §9) | Ad-hoc decisions in code | All future UX/product calls logged here | Accepted |
| P-011 | 2026-10-24 | **Philosophy clarified: detect AND remove C2PA/AI footprints in all formats (image/video/audio/doc/text), platform-ready for YouTube/LinkedIn/Instagram/TikTok/Pinterest/Reddit/X et al.** Recorded in `PHILOSOPHY.md` (Detect → Remove → Verify; honest Layer-1/Layer-2 boundary; R0–R4 roadmap) | Founder clarification, explicitly reversing P-010's "no sanitizers" | Detect-only product | Single north star; R0 restore + audio/video removal now the roadmap; engineering pending founder confirmation | Accepted |
| P-010 | 2026-10-24 | **Product wedge = DETECT. No sanitizers anywhere.** Remove Sanitizer UI/API/PRD; homepage + first nav item = Scan (file/text/URL); personas re-aimed at verification/compliance | Founder directive (verbatim: *"For the product wedge, make it detect, no sanitizers anywhere"*) | Sanitizer/creator wedge; keep both | D1/D2/D4 closed; single positioning + copy system; engineering in A-012 | **Superseded by P-011 (same day)** |

## 13. Document history

| Date | Change | Author |
|---|---|---|
| 2026-10-24 | Initial creation from full codebase/PRD audit (pages, flows, design tokens, copy rules, open decisions D1–D6). | Engineering (agent-assisted), pending founder review |
| 2026-10-24 | P-010 executed: wedge = Detect; Scan homepage/flows/personas/copy updated; D1/D2/D4 closed. | Founder + Engineering |
| 2026-10-24 | P-011: philosophy clarified (PHILOSOPHY.md created); D1 re-closed as Detect→Remove→Verify; P-010 superseded. | Founder + Engineering |
| 2026-10-24 | P-012: WIREFRAME.md + `mockup/` v1 built (15 pages, violet flat-forensic); current-state §§5–6 remain the *live app* design until mockup conversion is approved. | Founder + Engineering |
