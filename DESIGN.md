# DESIGN.md — Provenably (PVLY)

> Product & UX/UI design as it **currently exists** (`0.1.0-prototype`, verified 2026-10-24).
> Companion docs: [`AGENTS.md`](AGENTS.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md) ·
> [`docs/PRD.md`](docs/PRD.md) (Sanitizer PRD — personas §4, requirements §6, acceptance §14).
> **Every product/UX decision must be logged in §12.** Open decisions live in §11.

---

## 1. Product definition (current)

**Provenably — AI content provenance & compliance.** One-liners in force today:

- Detect: *"One graded Provenance Report per file"* (README).
- Sanitize: *"Check a file for AI provenance, strip the metadata that identifies it, then
  prove what was removed — in one pass"* (PRD §1).

**Two surfaces, one unresolved wedge** (see §11-D1): the app homepage `/` is **Sanitize**;
brand statement, nav and README lead with provenance/compliance. Until D1 is decided, do
not introduce copy that assumes either wedge exclusively.

## 2. Target personas (from PRD §4 — current, unvalidated)

| Persona | Need | Primary surface |
|---|---|---|
| Creator / influencer | Publish without leaking GPS/device; pass platform checks | Sanitize + Rules |
| Privacy-conscious user | Strip metadata before sharing | Sanitize |
| Newsroom / OSINT | Verify provenance; sanitize sources with audit trail | Detect + Sanitize |
| Platform / moderation | Understand what metadata arrives | Detect + Registry |
| Developer | Programmatic scan/strip + report via API | `/v1` API + `/api/docs` |
| Compliance / publisher (implied by Rules) | EU/CA/India/China/Korea disclosure readiness | Detect + Rules |

## 3. Design principles (binding)

1. **Show evidence, not verdicts on authorship.** Footer on every page: *"Reports describe
   signals and their evidence grade; they are not a verdict on authorship… not legal advice."*
2. **Grade everything.** Conclusion always pairs a human label with its evidence grade and
   the decisive signal; weak evidence is visually weaker (§7 conclusion block).
3. **Coverage is part of the result.** what ran vs. what's `not_configured` (dashed "manual"
   tags) appears on the report and on *API & status* — a clean result must show its limits.
4. **Honest limits up front.** Sanitizer states before use: metadata/C2PA removable;
   statistical watermarks are NOT (§8 required copy). Fragility is demonstrated, not hidden
   (the q75-JPEG watermark-loss demo fixture).
5. **Flat, minimal, fast.** No gradients, no decorative shadows, system fonts, no build
   step, no tracking/analytics (current state), tables over cards for data density.
6. **Prototype is labelled.** The `prototype` chip in the nav and TEST-signer labelling stay
   until trust list + production signing are real.

## 4. Information architecture (current pages)

Nav (`app/templates/base.html`): **Provenably** *"AI content provenance & compliance"* ·
Sanitize · Demo files · Registry · Rules · Text tools · Lab · API & status · `prototype` chip.

| Route | Template | Purpose (H1) |
|---|---|---|
| `/` = `/sanitize` | `sanitize.html` | "Remove metadata & Content Credentials" — dropzone, policy checks (Keep ICC, Re-encode), before/after result, recent jobs |
| `/demo` | `demo.html` | "Demo files" — 17 fixtures, one-click scan (primary demo entry) |
| `/report/{id}` | `report.html` | Provenance Report: conclusion block, signals, coverage, platform preview, raw JSON |
| `/registry`, `/registry/{slug}` | `registry*.html` | "AI watermark & provenance registry" (25) · "Does {tool} watermark or sign its output?" |
| `/laws` | `laws.html` | "Disclosure checklist & platform rules" (6 jurisdictions, 10 platforms) |
| `/tools` | `tools.html` | "Hidden-character scanner & cleaner" (unicode hygiene) |
| `/lab` | `lab.html` | "Lab: how a statistical text watermark works" (green-list generate/detect) |
| `/docs-guide` | `docs.html` | "API & deployment status" — live vs manual capabilities, curl examples |

## 5. Core user flows (current)

**F1 Scan:** Demo files (or API upload/URL/text) → queued → report page polls/renders →
conclusion (label + grade + decisive signal) → signals (expandable raw data) → coverage →
platform-label preview → download `report.json`.
**F2 Sanitize:** pick file (JPEG/PNG/WebP/PDF/DOCX ≤200 MB) → options (Keep ICC ✓ default;
Re-encode ☐) → "Remove metadata" → result: removed/kept lists, verify before/after,
verdict tag (`clean` green / residual amber), size in→out, download `<name>.sanitized<ext>`
→ appears in "Recent sanitize jobs".
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
per-page initializers (`sanitizePage()` etc.), `fetch` to `/v1`, `esc()` HTML-escaping helper
— **always** escape interpolated values; the few `innerHTML` sinks rely on it.

## 8. Copy & voice rules (binding)

- Tone: precise, forensic, understated. State method + grade + limits in the same breath.
- **Forbidden claims:** "human-made", "100% AI/human", "no watermark", "watermark removed",
  "undetectable", any legal-advice phrasing. Use: "No provenance signal found **by the
  checks that ran**", "Absence of provenance is not evidence of human origin".
- **Required sanitizer copy** (every entry point): *"Metadata removed. Embedded watermarks,
  if present, are not removed."* + what-was-removed list. Never market as evading
  disclosure laws or platform labels (PRD §13).
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
| D1 | **Wedge: Detect (compliance) vs Sanitize (creator/privacy)?** Homepage, tagline, README lead and nav order depend on it; the two currently contradict (README: "No removal/evasion anywhere"). | Positioning, pricing, legal posture, first customer segment | Before any public launch/marketing |
| D2 | Sanitizer legal UX: attestation checkbox + jurisdiction-aware warning (PRD §13) — specified, **not implemented**. | Legal exposure if marketed publicly (K7) | With D1 |
| D3 | Monetization UX: per-file vs per-GB vs subscription; where paywall appears (blueprint only: $0.02 img / $0.03 text / $0.08 audio-min / $0.15 video-min). | Auth/billing scope (PRD Phase 5) | Before Phase 5 |
| D4 | Batch + platform-preset UX (PRD Phase 4: 10 presets, ZIP+manifest). | The monetizable creator workflow | Phase 4 planning |
| D5 | HEIC/AVIF/RAW support messaging (mobile photos) — PRD Open Q1. | Creator persona coverage | v2 scoping |
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
| P-007 | 2026-10-23 (PRD) | Add Sanitize with Detect→Strip→Verify + explicit non-goals (no watermark-removal claims, no forgery/DRM) | Creator/privacy demand; differentiator = verified diff | Strip-only tool; watermark "removal" | Created wedge tension D1 + guardrail debt D2 | Accepted; D1/D2 open |
| P-008 | ≤2026-10-14 | Homepage `/` renders Sanitize (README still Detect-first) | *Undocumented at the time — recorded here retroactively* | Scan-first homepage | Top-of-funnel implies Sanitizer wedge; contradicts README | **Open — resolve via D1** |
| P-009 | 2026-10-24 | Adopt this design doc + mandatory decision logging before further development | Founder directive (AGENTS.md §9) | Ad-hoc decisions in code | All future UX/product calls logged here | Accepted |

## 13. Document history

| Date | Change | Author |
|---|---|---|
| 2026-10-24 | Initial creation from full codebase/PRD audit (pages, flows, design tokens, copy rules, open decisions D1–D6). | Engineering (agent-assisted), pending founder review |
