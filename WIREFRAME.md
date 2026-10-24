# WIREFRAME.md — Provenably complete mockup & frontend structure

> **Purpose:** lock the complete frontend *before* backend development. When this file and
> `mockup/` are approved, backend work is only "connect endpoints to finished pages" — no
> further frontend invention. Companion docs: [`PHILOSOPHY.md`](PHILOSOPHY.md) ·
> [`DESIGN.md`](DESIGN.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md) · [`AGENTS.md`](AGENTS.md).
>
> Status: **Mockup v2 built 2026-10-24 (DESIGN P-014) — Zapier design language applied to all 15 pages, pending founder approval.** v1 was rejected by founder ("AI-sloppy").
> v2 will be produced under the installed skills (AGENTS §12) after a `grilling` session and
> founder guidance; this spec's sitemap/backend-contract sections remain useful inputs,
> its visual execution does not. Decisions: DESIGN P-012 → P-013.

---

## 1. Founder decisions locked for this mockup (2026-10-24)

| Decision | Selected | Consequence |
|---|---|---|
| Design direction | **Evolved Flat Forensic (light)** | Keep DESIGN.md's flat system (no gradients, no decorative shadows, tables/tags/grades), modernized spacing/radius |
| Brand accent | **Violet AI** — `#6D28D9` (replaces blue `#1A4FD6`) | All accents, focus, primary buttons, "moderate" evidence grade become violet; grade set otherwise fixed (§4) |
| Scope | **Full end-to-end** | Marketing + app + reference + account, incl. empty/loading/error states (§2) |
| Deliverable | **This spec + clickable HTML** in `mockup/` | HTML converts 1:1 to Jinja templates later (§8) |

## 2. Sitemap (15 pages, all in `mockup/`)

```
MARKETING            APP (core loop)            REFERENCE              ACCOUNT
index.html  Landing  scan.html    Scan/Detect  registry.html          auth.html      Sign in/up
pricing.html Pricing remove.html  Remove       registry-item.html     history.html   Scans/removals/batches
                     report.html  Report       rules.html  Disclosure settings.html  Account/keys/billing
                     batch.html   Batch        api.html    API+status
                     presets.html Presets      design-system.html (internal)
```
Global chrome (every page): sticky nav (brand mark + Scan/Remove/Batch/Presets ·
Registry/Rules/Pricing/API · MOCKUP chip · History · Settings · Sign in) + 4-column
footer with legal disclaimer. The MOCKUP chip is removed at conversion time.

## 3. Page-by-page wireframe (sections · components · states · backend hook)

### 3.1 `index.html` — Landing
Sections: hero (claim + Detect→Remove→Verify loop chips + 3 CTAs + format strip) ·
How-it-works (3 cards) · Two-layers honesty (removable vs reported) + jurisdiction notice ·
Platforms grid (8 preset cards) · Registry/Compliance/API teasers · demo CTA + pricing CTA.
States: none (static). Backend: none (later: live stats/logo wall optional).

### 3.2 `scan.html` — Detect *(exists in app today as `app/templates/scan.html`; mockup adds Demo tab)*
Sections: tabs **File** (dropzone, hash-only, green-list key) / **Text** / **URL** / **Demo files** ·
"What gets checked" table · "Honest limits" box · result slot · Recent scans table.
States: idle, file-selected, working (progress), done/error (mock-action demo).
Backend hook: `POST /v1/scans` (exists) → 303 `/report/{id}`; demo `POST /v1/scans/demo/{name}`.

### 3.3 `remove.html` — Remove *(roadmap R0–R2)*
Sections: loop notice · 3-step tracker (Detect ✓ / Choose / Verify) · dropzone ·
**Detected panel** (per-footprint Found + Layer 1/2 tags) · options (keep-ICC, bake
orientation, re-encode, preset select) · **attestation (required)** · **Verify panel**
(before/after diff table, verdict tag, sizes, sha256 in/out, Layer-2 disclaimer, downloads) ·
per-format removal table + format strip.
States: no-file, detected-not-removed, removing, verified-clean, residual, error-per-format.
Backend hook: `POST /v1/remove` (to build) → RemoveReport; detect part reuses `/v1/scans` logic.

### 3.4 `report.html` — Provenance Report *(exists today; mockup is the target skin)*
Sections: back/CTAs · conclusion block (grade left-rule, label, evidence tag, decisive signal,
notes) · File facts (`kv`) + preview placeholder · **Coverage** (live/manual/errors +
enabling steps) · Signals list (status/grade tags, raw-JSON `details`, manual `.how`) ·
Platform label preview table · actions (Remove / Rules / JSON) · full-JSON details.
Backend hook: `GET /v1/scans/{id}` + `/report.json` + preview (exist); polling until done.

### 3.5 `batch.html` — Batch *(roadmap R3)*
Sections: multi-dropzone (≤50) · mode + preset controls · per-file queue table
(status/progress/verdict/in→out) · outputs box (ZIP + `manifest.json`) · explicit
Empty/Loading/Error state examples (design contract).
Backend hook: `POST /v1/batch` → job; `GET /v1/batch/{id}`; ZIP download. Per-file errors never fail the batch.

### 3.6 `presets.html` — Platform presets *(roadmap R3)*
Sections: 8 selectable platform cards (YouTube, Instagram, TikTok, LinkedIn, Pinterest,
Reddit, X, Facebook; each: formats, output spec, label note) · export config (source,
remove ✓, verify ✓, keep master) · "what this platform sees" table · generic-master box.
Backend hook: `GET /v1/presets`; export = `/v1/remove` with `preset=` (or `/v1/presets/{slug}/export`).

### 3.7 `registry.html` / `registry-item.html` — Generator registry *(exists today)*
List: search + modality filter + table (watermark/C2PA/public detector/confidence).
Item: fact `kv` (visible/invisible/C2PA/IPTC/detector/survives/confidence/last-verified) +
"what Provenably does" box linking Scan/Remove. Backend: `GET /v1/registry[/{slug}]` (exists).

### 3.8 `rules.html` — Disclosure & platform rules *(exists today as /laws)*
Sections: content-facts form → open-items summary per jurisdiction (EU/IN/CA/CN/KR…) ·
platform-labelling table · entry from a scan. Backend: `POST /v1/disclosure/check`,
`POST /v1/platforms/preview` (exist). Copy: dated, confidence-graded, "not legal advice".

### 3.9 `pricing.html` — Pricing *(mock numbers — DESIGN open decision D3)*
4 tiers (Free / Creator $9 / Pro $29 / API usage) · "every plan includes" strip · FAQ
(watermark honesty, legality, retention). Backend: Stripe checkout later (billing milestone).

### 3.10 `api.html` — API & status *(exists today as /docs-guide; target skin)*
Live/manual capability tables · quickstart code blocks (dark pre) · endpoint contract table
with Exists/R0–R3 status tags. Backend: `GET /v1/capabilities`, OpenAPI `/api/docs` (exist).

### 3.11 `history.html` — History *(new; needs auth to be per-user)*
Tabs: Scans / Removals / Batches&exports (retention countdown, verdicts, downloads;
empty state shown). Backend: `GET /v1/scans`, `GET /v1/remove`, `GET /v1/batch` lists (+ ownership).

### 3.12 `settings.html` — Settings *(new)*
Account/plan · privacy & retention defaults · API keys (create/revoke, `X-API-Key`) ·
billing placeholder + usage meter · danger zone (delete files/account).
Backend: account/keys/billing endpoints (auth milestone).

### 3.13 `auth.html` — Sign in / Create account *(new)*
Tabs in/out, Google button (mock), "anonymous free scans stay available" note.
Backend: IdP/JWT (replaces static key hook — ARCHITECTURE manual item).

### 3.14 `design-system.html` — Internal reference
Swatches, type, buttons/tags/conclusion/dropzone/notices, layout & graphics rules (§§4–6 live).

**Carried over unchanged in spirit (exist in app, re-skin at conversion):** Text tools
(`/tools`, unicode hygiene) and Lab (`/lab`, green-list) — not re-mocked; they adopt the
new tokens via the shared stylesheet.

## 4. Design tokens (final for mockup — `mockup/style.css :root`)

| Token | Value | Use |
|---|---|---|
| `--ink` | `#141414` | Text, dark buttons, conclusion border |
| `--accent` | **`#6D28D9`** violet | Primary actions, links, focus, active nav, **evidence grade "moderate"** |
| `--accent-ink / -soft / -line` | `#4C1D95 / #F1EBFD / #D9CFFB` | Hover, chip/card fills, dropzone |
| `--ok / --warn / --bad` | `#136F3A / #A65D00 / #B3261E` | Grades strong / weak / tampered (+ soft bg variants) |
| `--muted / --line / --soft` | `#5F6368 / #E3E3E3 / #F7F7F5` | Secondary text (also grade "none"), borders, surfaces |
| Radius | `10px` cards, `7px` controls | Evolved from v0 sharp corners |
| Evidence-grade convention (unchanged semantics) | strong=green · **moderate=violet accent** · weak=amber · none=gray · tampered=red | Always grade **word + color** (never color-only) |

## 5. Typography & graphics

- **Fonts:** `Inter` (UI/headings, 400–800) with system fallback stack; `JetBrains Mono`
  (hashes, IDs, code, format chips) with ui-monospace fallback. Loaded via Google Fonts
  `@import` in the mockup; self-host or keep import at conversion (founder/infra choice).
- **Scale:** base 16px/1.55 · hero H1 3rem · page H1 2.1/1.9rem · H2 1.35rem · H3 1.02rem ·
  small .86rem · eyebrow .72rem uppercase violet.
- **Graphics:** inline SVG check-mark logo (violet rounded square) + single-letter platform
  tiles + data visuals only (tables, tags, progress, before/after diffs). **No gradients,
  no stock photos, no decorative shadows** (flat rule). Code blocks: solid dark `#171321`.
- **Motion:** indeterminate progress slide only; `prefers-reduced-motion` disables it.

## 6. Layout, responsiveness, accessibility

1180px wrap / 20px gutters (widened from 1040 for app density) · sticky 58px nav with
horizontal scroll on small screens · grids collapse 4→2 (≤900px) →1 (≤680px) · signal rows
stack ≤680px. A11y contract: semantic landmarks, 2px violet focus outlines, labels on all
controls, dropzone always contains a real file input, status never by color alone.
Known gaps to close at conversion: ARIA live regions for async results, muted-text contrast audit.

## 7. Backend contract summary (what "just connect the backend" means)

| Frontend need | Endpoint | Status |
|---|---|---|
| Detect (scan/report/demo/preview/JSON) | `/v1/scans…` (ARCHITECTURE §7) | ✅ exists |
| Registry, rules, disclosure, platform preview, text unicode, lab, capabilities, health | existing `/v1/…` | ✅ exists |
| Remove+Verify (remove.html, report CTA, history) | `POST /v1/remove`, `GET /v1/remove/{id}[/file]` | 🔨 R0 images/PDF/DOCX → R1 audio → R2 video |
| Presets | `GET /v1/presets`, remove with `preset=` | 🔨 R3 |
| Batch | `POST/GET /v1/batch[/{id}]`, ZIP+manifest | 🔨 R3 |
| Auth, per-user history, API keys, billing | IdP/JWT + account endpoints + Stripe | 🔨 auth/billing milestone |

Every mocked field (verdicts, diffs, hashes, coverage, preset specs) maps to the report
schemas in ARCHITECTURE §8 (RemoveReport schema returns with R0).

## 8. Conversion plan (mockup → production frontend, later)

1. `mockup/style.css` → `app/static/style.css` (tokens overwrite; blue→violet is the only
   breaking visual change; class names were intentionally kept compatible with current CSS).
2. Each `mockup/*.html` → `app/templates/*.html`: extract shared nav/footer into
   `base.html`, replace mock data with Jinja variables, replace `data-mock-action` with
   real fetches/forms (patterns already in `app/static/app.js`: tabs/dropzone/polling).
3. New templates (`remove/batch/presets/history/settings/auth/pricing`) ship only with
   their backend milestones (R0–R3/auth) — never as dead pages in production.
4. Delete `mockup/` after conversion is verified page-by-page (or keep as design archive).

## 9. Applying DESIGN.md — evaluation (what changed, what deliberately didn't)

- **Kept (proven in the live app):** flat/no-gradient language, token names, type scale
  ratios, conclusion/signal/tag/kv/notices/dropzone components, footer disclaimer, copy rules.
  → Conversion is a re-skin, not a rewrite; existing templates mostly need the new stylesheet.
- **Changed by founder decision:** accent blue→violet (incl. "moderate" grade + focus),
  wrap 1040→1180, radius 0→10/7px, Inter/JetBrains Mono named (was system-only), sticky nav,
  pill tags, platform/preset & pricing card components, dark code blocks.
- **Risk noted:** violet must not dilute grade semantics — mitigated by keeping
  green/amber/red exclusive to grades and always pairing color with the grade word.

## 10. Review checklist — founder approval gate

- [ ] Palette: violet accent + grade colors (§4) — approve / adjust
- [ ] Fonts: Inter + JetBrains Mono (§5) — approve / change
- [ ] Sitemap & nav (§2) + per-page sections (§3) — approve / add / remove pages
- [ ] Landing claim & two-layer honesty (§3.1) — approve wording
- [ ] Remove flow: attestation + verify panel (§3.3) — approve
- [ ] Pricing tiers as *placeholders* (§3.9, final = D3) — approve structure
- [ ] "Skills" founder wants applied — **to be provided by founder**; will be evaluated
      against §§4–6 and either adopted via a Decision Log row or rejected with reasons

## 11. Document history

| Date | Change | Author |
|---|---|---|
| 2026-10-24 | Created with mockup v1 (15 pages) from founder decisions: flat-forensic direction, violet accent, full end-to-end scope, spec+HTML deliverable. | Founder (decisions) + Engineering (build) |
