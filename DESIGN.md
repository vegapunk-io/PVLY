---
version: 2.1
name: Provenably-design-system
description: Provenably's complete design system, reverse-engineered from Zapier's design language (source `zapier/DESIGN.md`, fetched with `npx getdesign@latest add zapier`) and adapted to a forensic Detect → Remove → Verify product. Warm-cream canvas (`#fffefb`), deep coffee ink (`#201515`), one saturated orange CTA (`#ff4f00`), quiet-premium Hanken Grotesk typography, 12px middle radius, flat elevation. Product evidence grades are the only semantic colors.

colors:
  primary: "#ff4f00"        # CTA / conversion ONLY
  primary-hover: "#d94300"  # derived: hover/active
  primary-soft: "#ffeee3"   # derived: chips, dropzone drag fill
  on-primary: "#fffefb"
  ink: "#201515"
  ink-soft: "#2f2a26"
  ink-mid: "#36342e"
  body: "#605d52"
  body-mid: "#939084"
  mute: "#c5c0b1"
  canvas: "#fffefb"
  canvas-soft: "#f8f4f0"
  line: "#e6ded1"           # derived warm hairline
  grade-strong: "#136f3a"   # semantic only
  grade-moderate: "#201515" # = ink (deliberate: orange is never a grade)
  grade-weak: "#a65d00"     # semantic only
  grade-none: "#939084"     # = body-mid
  grade-tampered: "#b3261e" # semantic only

typography:
  display-xl:  { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 73.6px, fontWeight: 530, lineHeight: 73.6px, letterSpacing: -0.048em }
  display-lg:  { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 56.8px, fontWeight: 530, lineHeight: 58.5px, letterSpacing: -0.042em }
  display-md:  { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 37.6px, fontWeight: 540, lineHeight: 42.1px, letterSpacing: -0.034em }
  heading-sm:  { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 18.9px, fontWeight: 650, lineHeight: 24.9px, letterSpacing: -0.018em }
  body-lg:     { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 20.5px, fontWeight: 450, lineHeight: 31.8px, letterSpacing: -0.008em }
  body-md:     { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 17px, fontWeight: 400, lineHeight: 26.9px }
  body-sm:     { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 16px, fontWeight: 400, lineHeight: 24.8px }
  caption:     { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 12.8px, fontWeight: 500, lineHeight: 18.6px }
  eyebrow:     { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 12.8px, fontWeight: 700, lineHeight: 15.4px, letterSpacing: 0.11em, textTransform: uppercase }
  button-md:   { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 16px, fontWeight: 600, lineHeight: 19.2px }
  button-sm:   { fontFamily: "Hanken Grotesk Variable, Hanken Grotesk, Inter, system-ui, sans-serif", fontSize: 14.4px, fontWeight: 650, lineHeight: 1.2 }
  mono:        { fontFamily: "JetBrains Mono Variable, JetBrains Mono, ui-monospace, Menlo, monospace", fontSize: 0.86em }

rounded: { none: 0px, sm: 6px, md: 12px, pill: 9999px }
spacing: { xxs: 2px, xs: 4px, sm: 8px, md: 12px, lg: 16px, xl: 24px, 2xl: 32px, 3xl: 48px, 4xl: 64px }
---

# DESIGN.md — Provenably design system (complete)

> Status: **v2.1 founder-approved and implemented in the SvelteKit production frontend (`frontend/`)** · 2026-10-24 · Decisions **P-014/P-015/P-016/P-017/P-018/P-019/P-020**
> Source reverse-engineered: [`zapier/DESIGN.md`](zapier/DESIGN.md) (identical to the founder-supplied `DESIGN-zapier.md`; fetched via `npx getdesign@latest add zapier`).
> Companions: [`PHILOSOPHY.md`](PHILOSOPHY.md) · [`WIREFRAME.md`](WIREFRAME.md) · [`AGENTS.md`](AGENTS.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md).
> Implementation of record: `frontend/src/app.css` + Svelte components/routes. `mockup/` remains the approved visual archive. **No linear gradients in interface CSS. No decorative shadows. No side-stripe accent bars on cards, panels, notices, or conclusions (P-019). One Hanken Grotesk sans carries display/body/UI; JetBrains Mono is data-only (P-020).** Founder-supplied platform trademarks are never recolored or masked (P-016); Provenably's own primary mark is forced to the website `#ff4f00` palette exactly as specified in P-018.

---

## 1. How this was reverse-engineered (method, not vibes)

1. **Extracted the source system token-by-token** from `zapier/DESIGN.md`: colors, type scale,
   radii, spacing, 20 named components, bands, elevation, breakpoints, do/don't list.
2. **Separated brand from mechanism.** Copied *mechanisms* ( warm-neutral temperature, one
   CTA color, 12px radius, cream-card elevation, display/body two-voice type). Never copied
   Zapier's name, logo, copy, or illustrations. Provenably keeps its own check-mark logo,
   forensic components, and honesty copy.
3. **Resolved the one real conflict — semantics.** Zapier ships no semantic palette; a
   forensic product's evidence grades *are* content. §3.3 documents the bounded exception.
4. **Ran the skills protocol** (`AGENTS.md §12`) over the result — §10 is the audit trail.

| Zapier trait (source evidence) | Provenably application |
|---|---|
| Warm cream canvas `#fffefb`, soft `#f8f4f0` — "temperature IS the brand voice" | Page = canvas; cards/sections = canvas-soft; never pure white `#fff`/`#ffffff` surfaces |
| Coffee ink `#201515`, warm neutral ladder to `#c5c0b1` | Text ladder ink → ink-mid → body → body-mid → mute; no cool grays anywhere |
| Single orange `#ff4f00` = every primary CTA | `#ff4f00` = the Provenably brand mark, primary buttons, focus and active states; the founder-supplied brand source is palette-forced to this exact token |
| Degular Display 500 hero + Inter everything else; sentence-case headlines | The quiet display mechanism and sentence-case rule are retained, but P-020 supersedes the actual faces: self-hosted Hanken Grotesk Variable now carries display, body and UI; no proprietary Degular or bundled Inter webfont ships |
| Eyebrow: uppercase 14px, +1px tracking | Mechanism retained and recalibrated for Hanken Grotesk (12.8px/700/+0.11em), used sparingly, ink-colored |
| 12px radius on buttons **and** cards — deliberate middle | `--radius:12px` for buttons/cards/panels; 6px inputs & format chips; pill only for badges |
| Elevation: flat → 1px ink hairline → cream-fill contrast | Same 3 levels; zero box-shadows in the mockup stylesheet |
| Buttons ~48px (12px pad + 27px line) | `min-height:48px`, padding 10–12/24, `button-md` type |
| Pricing: white+ink-border default, **dark flipped featured** | `.pricecard` / `.pricecard.featured` exactly so |
| Footer: dark coffee, cream text | Footer = ink band, canvas-soft text |
| Container ~1280px, bands 64px, cards 24px | `.wrap:1280px`, `.section:64px`, `.box:24px` |
| Breakpoints <768 / 768–1023 / ≥1024 | Grids collapse 4→2 at 1023, →1 at 767; hero type steps down |

## 2. Brand translation

- **Voice:** confident-warm, plain-spoken. Warm neutrals say "approachable tool", forensic
  tables/tags say "evidence". The one loud thing per page is the orange primary action
  (frontend-design: *spend boldness in one place*).
- **Logo:** the founder-supplied 64×64 transparent check is Provenably's only primary mark.
  Its untouched source is retained at
  `frontend/src/lib/assets/brand/source/icons8-checkmark-64.png`; the canonical website
  asset at `frontend/src/lib/assets/brand/provenably-mark.png` copies that geometry and
  alpha pixel-for-pixel while forcing every RGB pixel to the Zapier-derived website
  primary `#ff4f00`. Render only the canonical file through `BrandMark`, pair it with the
  Hanken Grotesk 650 wordmark at tight display tracking, and never use the source's native `#fd7e14`, trace, crop,
  stretch, mask, outline, add a background, or revive the retired orange rounded-square
  treatment. Favicon: the same canonical palette-forced PNG.
- **Product loop as the signature motif:** `Detect → Remove → Verify → Platform-ready`
  pill sequence (cream pills, orange arrows) replaces any decorative hero art.

## 3. Color

### 3.1 Core (from source, unchanged values)
| Token | Hex | Role |
|---|---|---|
| `primary` | `#ff4f00` | Primary brand mark, CTA bg, focus ring, active indicators, progress fill |
| `on-primary` | `#fffefb` | Text on primary/ink surfaces |
| `ink / ink-soft / ink-mid` | `#201515 / #2f2a26 / #36342e` | Headings, dark buttons/cards/footer, emphasized text |
| `body / body-mid / mute` | `#605d52 / #939084 / #c5c0b1` | Body text, metadata, dividers/disabled |
| `canvas / canvas-soft` | `#fffefb / #f8f4f0` | Page, cards & bands (elevation by contrast) |

### 3.2 Derived (introduced here, each justified)
`primary-hover #d94300` (interactive state needs a step the source omits) ·
`primary-soft #ffeee3` (chip/drag-state tint of primary) ·
`line #e6ded1` (hairline between canvas-soft and mute for dense app tables) ·
orange text accent `#8f2d00` (small orange-tinted labels need ≥4.5:1 on cream — raw
`#ff4f00` at small sizes is ~3.3:1; see §9).

### 3.3 Semantic evidence grades — the bounded exception
Zapier: *"The brand doesn't surface a separate semantic palette."* Provenably must:
evidence grade is data, and color is never its only channel (grade word always rendered).
**strong `#136f3a` · moderate = ink `#201515` · weak `#a65d00` · none = body-mid · tampered `#b3261e`.**
Moderate deliberately takes *ink*, not orange: orange stays unambiguously "act here",
and close hues (orange vs weak-amber) can't be confused at a glance. Semantic hues appear
only in grade tags, contained status icons/dots, restrained notice surfaces, and verify
diffs — never as a vertical side stripe, marketing decoration, or a "second accent".

### 3.4 Color don'ts
No pure white/black surfaces · no cool-gray tokens · no gradients · no second brand hue ·
no thick colored side stripes on cards/panels/notices/conclusions in any hue ·
no orange body links at small size (links are ink + underline, hover orange) ·
no orange grade.

## 4. Typography (P-020)

One sans, strict roles. **Hanken Grotesk Variable** is the only shipped sans for display,
body, controls, tables and reports. Inter remains only as a locally installed fallback name
before `system-ui`; no Inter webfont is bundled, and proprietary Degular is never shipped.
The open-source Latin normal face is self-hosted through
`@fontsource-variable/hanken-grotesk`; the matching true italic is declared separately and
loads only when italic text renders. `font-synthesis: none` remains binding—never faux-bold
or faux-italic a missing style.

| Role | Production treatment |
|---|---|
| Hero display | Hanken Grotesk 530, up to 73.6px, line-height 1.0, tracking `-0.048em` |
| Page H1 | 530, up to 56.8px, line-height 1.03, tracking `-0.042em` |
| Section H2 | 540, up to 37.6px, line-height 1.12, tracking `-0.034em` |
| Card/section H3 | 650, 18.9px, line-height 1.32, tracking `-0.018em` |
| Lead | 450 book weight, 17.6–20.5px, line-height 1.55, tracking `-0.008em` |
| Body | 400, 17px marketing density and 16px app density, line-height 1.55–1.58 |
| Small / caption | 14.4px small text; captions and compact labels are 500 at a 12.8px floor |
| Controls | Buttons 600 at 16px; small buttons, tabs and segmented controls 600–650, sentence case |
| Eyebrows | 700, 12.8px, uppercase, `+0.11em`; page/major-section heads only |
| Tables | 15.2px/1.45 body; 13.8px/650 sentence-case headers; lining tabular figures in numeric cells |
| Wordmark | 650, tracking about `-0.04em`, always paired with the canonical P-018 mark |
| Data | JetBrains Mono Variable, route-split, only for hashes, IDs, filenames, code and format chips |

**Weight discipline:** use only the semantic tokens `--fw-regular 400`, `--fw-book 450`,
`--fw-medium 500`, `--fw-display 530`, `--fw-display-strong 540`, `--fw-semibold 600`,
`--fw-emphasis 650`, and `--fw-bold 700`. Ordinary UI never uses 750–900. Sentence-case
headlines and buttons, always. Font-file QA is part of the contract: the shipped Hanken
Grotesk **normal** face has one lining figure set whose digits share a 560-unit advance, so
figures align consistently in prose and data; `.num`, metrics and prices still declare
lining tabular figures for data intent and fallback consistency. The shipped normal face
does **not** expose separate proportional, slashed-zero, or `case` alternates, so CSS must
not claim them. Hash/identifier distinction is carried by JetBrains Mono, whose shipped zero
is center-dotted by default. Headings use balanced wrap, paragraphs use pretty wrap, ledes
stay ≤760px, and long prose stays ≤80ch.

## 5. Layout, spacing, responsive

4px base; tokens 2/4/8/12/16/24/32/48/64. Container 1280px + 24px gutters. Bands pad 64px
(`.section`, hero); cards pad 24px. Sticky nav (canvas, warm hairline, 64px min-height).
Grids: `.grid2/3/4` → 2-col ≤1023px → 1-col ≤767px; nav scrolls horizontally when tight;
signal rows stack ≤767px; production display type is fluid (hero up to 73.6px; page H1 up to
56.8px). Touch: buttons ≥48px, small buttons ≥42px in production,
tabs ≥44px (ui-ux-pro-max priority-2 rule).

## 6. Elevation & shape

Level 0 flat (bands) → Level 1 hairline (`1px solid ink` on pricing/conclusion/inputs;
`line` in dense tables) → Level 2 cream card on canvas (default). **Zero shadows.**
Borders are quiet complete hairlines or functional state outlines; never a thickened
single-side accent bar. Radius: 12px buttons/cards/panels/notices/pre · 6px
inputs/format chips · pill badges/tags/avatars · 0 bands.

## 7. Components (mockup class → spec)

| Component | Spec (all in `mockup/style.css`) |
|---|---|
| `button`/`.btn` | primary orange, on-primary text, 12px radius, 10–12×24 pad, ≥48px, Hanken Grotesk 16/600; hover `primary-hover` |
| `.btn.dark` | Zapier button-secondary: ink fill |
| `.btn.secondary` | Zapier button-tertiary: canvas fill, 1px ink border, ink text |
| `.btn.small` | Hanken Grotesk 14.4/650, ≥42px in production |
| `.box` (card-content) | canvas-soft, 12px, 24px pad — the default card everywhere |
| `.pricecard` / `.featured` | canvas + 1px ink border / flipped ink fill + orange plan tag |
| `.platcard` | canvas-soft selectable card; `.sel` = 2px primary outline on canvas. Founder-supplied platform mark is shown unmasked with `object-fit: contain`; exact viewer-label chip, researched placement subtext and documented signal summary sit above the action. Destinations without supplied artwork use a neutral monogram, never a recreated trademark |
| inputs/select/textarea | canvas, 1px ink border, 6px radius, 12×16 pad, 18px; focus border primary + 2px outline |
| `.check` | 17px checkbox, `accent-color: primary` |
| `.tag` (badge-pill) | pill, canvas-soft, mute border; semantic variants `.ok/.warn/.bad/.accent/.manual(dashed)` |
| `.dot` | 9px status dot, semantic fills |
| `.tabs` | ink text, 3px primary underline on active, ≥44px targets |
| `.drop` | 1.5px dashed body-mid on canvas-soft; drag-over → primary border + primary-soft fill; real `<input type=file>` inside, always |
| `.conclusion` | canvas, uniform 1px ink border, 12px radius; label in Hanken Grotesk display 530 with `-0.032em` tracking, header closed by a neutral hairline; grade/tamper state is carried only by mandatory worded tags, never a side rule |
| `.signal` | 190px name/meta rail + body; `.how` (manual step) in warn tone |
| `.notice` | 12px card with a uniform 1px `line` frame and restrained semantic surface; a contained 32px icon tile carries tone beside the title/copy—no side stripe in any variant |
| `.steps` | numbered circles: current=primary, done=ink ✓, pending=mute |
| `.progress` | 6px pill track (canvas-soft + line border), primary fill; indeterminate slide, reduced-motion off |
| `table` | Hanken Grotesk 15.2px/1.45; header canvas-soft 13.8px/650 sentence-case ink-mid; numeric cells use lining tabular figures; 12×16 cells; `line` row rules; warm hover `#fbf7f1` |
| `.loop .stepchip` | cream pill + orange arrow — the product-loop motif |
| `.fmt` | JetBrains Mono 12.8px/600 format chip, 6px radius, canvas-soft |
| `.empty` | canvas-soft 48px-pad empty-state card (ex-empty-state-card) |
| `pre` | ink surface, canvas-soft mono text, 12px radius |

## 8. Page patterns (15 mockup pages — bands & composition)

- **Landing** (`index`): canvas hero-band (display-xl, loop motif, 3 CTAs: primary/tertiary/dark) → canvas-soft "how it works" band (3 cream cards on cream get hairline via surface step) → canvas honesty section (2-layer cards + info notice) → canvas-soft platforms band (8 platcards) → canvas teasers + centered CTA → dark footer.
- **App pages** (`scan/remove/batch/presets/history/settings`): pagehead (sparse eyebrow + fluid Hanken Grotesk H1) → working grid (form/dropzone left, evidence panels right) → full-width tables. Canvas bg, cream cards.
- **Report** (`report`): conclusion block first (the product's hero moment), facts+coverage pair, signals, platform table, actions.
- **Reference** (`registry/rules/api`): tables-first on canvas, cream side panels, dark `pre`.
- **Pricing** (`pricing`): 4-up tier grid, featured = dark flip, FAQ as native `details`.
- **Auth** (`auth`): centered 430px card (ex-auth-form-card), tabs, tertiary social button.
- **Design system** (`design-system`): this file rendered — swatches use the exact tokens above.

## 9. Accessibility & motion (skills-enforced floor)

Contrast: ink on canvas ≈15.8:1, body on canvas ≈6.4:1, on-primary on primary ≈3.3:1
(large/semibold button text only — never small text), dark-orange `#8f2d00` for small
accent labels. Focus-visible: 2px primary outline + 2px offset on every interactive
element. Grade = word + color. Labels on all inputs (no placeholder-only). Errors render
next to the action (baseline-ui). Typography floor: essential captions/labels are at least
12.8px, text remains usable at browser zoom, numeric evidence uses tabular lining figures,
and uppercase is rationed so scanning and screen magnification stay comfortable. Motion:
only the progress indeterminate; no entrance animations, no hover transitions invented
per-card; `prefers-reduced-motion` kills it. Keyboard: native elements only in the mockup
(buttons, details, file inputs) — no hand-rolled focus behavior to break.

## 10. Skills application log (how each skill shaped v2 — AGENTS §12 order)

| Skill | Applied as |
|---|---|
| `grilling` | **Superseded for this pass by explicit founder brief** ("apply zapier design, show me everything") — frontend-design's own rule: where the brief pins direction, follow it exactly. Still the gate before v2 → production templates. |
| `ui-ux-pro-max` | Local searches (`style`: Minimalism & Swiss — clean/grid/high-contrast corroborates the flat choice; `typography`: Inter-led pairing). Priority rules enforced: 44px+ targets, semantic tokens (no raw hex in components — all via `:root`), no emoji icons, reduced-motion. |
| `frontend-design` | Two-pass method: token plan first (§§3–7), reviewed against brief, then code. Its "AI tell" list confronted honestly: v1's violet SaaS-card kit is gone; the ALL-CAPS eyebrow survives **only** because the Zapier spec itself mandates it (brief wins) and is rationed to page/section heads. Boldness spent in one place: orange CTA + loop motif; everything else quiet. |
| `baseline-ui` | Deslop constraints adapted (not its Tailwind mandate): consistent spacing scale, errors at the action, no placeholder-only labels, paste never blocked, skeletons→progress patterns. |
| `frontend-ui-engineering` | Token-driven global CSS plus small typed Svelte components; route-level CSS/JS splitting, responsive layouts, and explicit loading/empty/error/success states per surface. |
| `fixing-accessibility` | §9 checklist run: names/labels, focus visibility, contrast table, non-color cues. |
| `fixing-motion-performance` | Single compositor-friendly `transform` animation (progress); nothing animates layout/paint properties. |
| `improve-ui` / `ui-skills-root` | Smallest-context discipline: v1 re-skinned via one file instead of 15 rewrites; v1 structure/copy audited against the new system rather than discarded wholesale. |

## 11. Production implementation (completed 2026-10-24)

The approved mockup is implemented as a SvelteKit/Svelte 5 + TypeScript static frontend in
`frontend/`, served same-origin by FastAPI from `frontend/build` when built. Public pages are
prerendered; landing/pricing ship no client JS; interactive routes load only their own code.
FastAPI remains the JSON backend. Routes whose backends do not exist yet (Remove R0, native
Batch/Presets R3, Auth/billing) render explicit unavailable/local-only states and never fake a
successful server operation. Jinja remains only as a no-build fallback until deployment has
fully cut over.

**P-016 platform-mark and label pass (2026-10-24):** the founder's 512×512 YouTube,
Instagram, LinkedIn, Pinterest, Reddit and Facebook PNGs are preserved under
`frontend/src/lib/assets/platforms/source/`; the UI imports 144×144 lossless WebP derivatives
with no crop, recolor, mask or aspect change. `PlatformMark` keeps the mark decorative beside
the platform name and uses neutral monograms where no asset was supplied. Platform cards,
preset selectors, the report preview and the rules catalogue now separate (1) exact viewer
wording, (2) placement/duty subtext, and (3) documented C2PA/IPTC/SynthID/classifier/toggle
signals. Corrections encoded from the 2026-10-24 research: Meta uses **“AI info”** (not the
retired generic “Made with AI”); LinkedIn's Content Credentials mark is lower-case **“cr”**,
not “CC”, and denotes signed provenance rather than an AI verdict; Pinterest uses **“AI
modified”** with IPTC/classifiers documented, not C2PA as a guaranteed trigger; Reddit has
**no site-wide file label**; X's **“Made with AI”** automatic criteria remain only partly
published and are therefore confidence-graded medium.

**P-017 primary brand mark (2026-10-24):** the founder-supplied 64×64 transparent check
PNG replaces the generated orange rounded-square mark on every live product surface. The canonical file is
byte-for-byte preserved at `frontend/src/lib/assets/brand/provenably-mark.png`, rendered
through `BrandMark` in the Svelte header/footer/design-system reference, used directly as
the production favicon, and mirrored byte-for-byte to `app/static/provenably-mark.png` for
the legacy Jinja fallback. Its checksum and handling rules live beside the asset. The
native-color/byte-for-byte canonical clause was superseded the same day by P-018.

**P-018 palette-force correction (2026-10-24):** the founder rejected the supplied
file's native `#fd7e14`. The untouched source moved to
`frontend/src/lib/assets/brand/source/icons8-checkmark-64.png`; the canonical website
PNG was regenerated by copying its alpha channel pixel-for-pixel and setting every RGB
pixel to the Zapier-derived Provenably primary `#ff4f00`. The canonical palette version
is mirrored to the legacy fallback. The native-orange source must never ship in the UI.

**P-019 side-stripe removal (2026-10-24):** the founder rejected the thick colored
edge used by notices and conclusions as an AI-generated design tell. A full CSS audit
found the pattern in the production `.notice` variants, `.conclusion` grade variants,
and landing report preview, plus the legacy and mockup stylesheets. Every instance was
removed. Notices now use one quiet hairline frame, a restrained semantic surface, and a
contained icon tile; conclusions use one uniform ink frame, a neutral header hairline,
and their existing worded classification/evidence tags. No card, panel, notice, or
conclusion may use a thick `border-left`/`border-right` accent bar in any hue. Functional
full-perimeter borders, keyboard-focus outlines, active-tab underlines, table rules, tags,
and status dots remain because they communicate state or structure rather than decorate an
edge. The pass followed `baseline-ui` restraint, `frontend-design` anti-template review,
and `fixing-accessibility`'s rule that status never rely on color alone.

**P-020 Hanken Grotesk typography (2026-10-24):** after comparing Poppins, Raleway,
Hanken Grotesk, Pixelify Sans, Funnel Display and Zapier's Degular/Inter pairing, the
founder approved Hanken Grotesk as Provenably's one sans across display, body and UI.
Production now loads the Latin Hanken Grotesk Variable normal face (34,704 bytes) from
`frontend/src/lib/hanken-grotesk-font.css`; the 35,592-byte true italic is declared
separately and is fetched only when italic text renders. The bundled Inter webfont was
removed. Global and component CSS were recalibrated from scattered 460–800 weights to
semantic 400/450/500/530/540/600/650/700 tokens, quiet-premium display tracking, a 12.8px
caption floor and lining/tabular numeral intent. Direct WOFF2 inspection corrected the
feature specification: Hanken's shipped normal digits are already equal-width, while no
separate proportional/slashed-zero/`case` feature is exposed; JetBrains Mono's default
center-dotted zero carries hash distinction. Header/footer wordmarks, platform labels, buttons,
metrics, tables, reports and the live `/design-system` specimen use the new roles.
JetBrains Mono remains route-split and data-only. The no-build Jinja fallback mirrors the
same stack through `app/static/fonts/` with byte-identical Fontsource WOFF2 files and the
accompanying OFL-1.1 license text. Future non-Latin localization requires an explicit
subset/fallback decision; this English-first build intentionally ships Latin only.

## 12. Product design carried over (still binding)

Philosophy: **Detect → Remove → Verify → Platform-ready** (`PHILOSOPHY.md`). Sitemap,
flows, per-page sections/states and backend hooks: `WIREFRAME.md §§2–3` (unchanged by the
re-skin). Copy rules unchanged: reports describe signals & grades, never verdicts on
authorship; forbidden claims ("human-made", "watermark removed", "undetectable");
required honesty copy (coverage, Layer-2 disclaimer, attestation, "not legal advice",
TEST-signer labeling). Personas: newsroom/OSINT, creator, compliance/publisher,
platform/moderation, developer.

**Open decisions:** D3 pricing numbers (tiers are placeholders) · D4 batch-scan UX detail ·
D5 HEIC/AVIF/RAW coverage messaging. **D6 resolved (P-015, typefaces updated by P-020):**
self-host only the Latin variable subsets of Hanken Grotesk and JetBrains Mono via
Fontsource; Hanken italic is conditional on italic content, and mono is route-split.

## 13. Decision log (append-only)

| ID | Date | Decision | Status |
|---|---|---|---|
| P-001 | ≤2026-10-14 | One graded Provenance Report; "not a verdict on authorship" | Accepted |
| P-002 | ≤2026-10-14 | Evidence-grade color convention on conclusion block (+ grade word always) | Accepted (moderate color updated by P-014; conclusion side-rule removed by P-019) |
| P-003 | ≤2026-10-14 | Coverage/manual modules visible in-product | Accepted |
| P-004 | ≤2026-10-14 | Flat/minimal visual system v0 (superseded visually by P-012, then P-014) | Superseded |
| P-005 | ≤2026-10-14 | Public generator Registry with confidence/last-verified | Accepted |
| P-006 | ≤2026-10-14 | 17 demo fixtures as first-class product surface | Accepted |
| P-007→P-011 | 2026-10-23/24 | Sanitizer added → removed (P-010) → philosophy clarified Detect→Remove→Verify (`PHILOSOPHY.md`) | P-011 Accepted |
| P-009 | 2026-10-24 | Mandatory decision logging in these docs | Accepted |
| P-012 | 2026-10-24 | Mockup-first, full end-to-end; violet flat-forensic mockup v1 | Superseded by P-014 (visuals) |
| P-013 | 2026-10-24 | Mockup v1 **rejected** by founder ("AI-sloppy"); 10 skills installed; v2 gated on skills + founder guidance | Accepted |
| **P-014** | **2026-10-24** | **Adopt Zapier design language (reverse-engineered from `zapier/DESIGN.md`) as Provenably's complete design system** — warm cream/coffee/orange, display-Inter, 12px radius, flat elevation — applied to all 15 mockup pages via one stylesheet; bounded semantic-grade exception (§3.3); skills log §10 | **Accepted — founder-approved 2026-10-24; typefaces superseded by P-020** |
| **P-015** | **2026-10-24** | **Implement P-014 as SvelteKit/Svelte 5 + TypeScript static frontend with FastAPI retained as JSON backend** — prerendered public pages, selective hydration, self-hosted Latin font subsets, measured bundle budget | **Accepted — founder-approved implementation direction; font families updated by P-020** |
| **P-016** | **2026-10-24** | **Founder-supplied platform marks + evidence-backed AI-label subtext** — preserve six 512px source marks, ship lossless 144px WebP derivatives unmasked, use neutral monograms for unsupplied destinations, and show exact label wording plus documented provenance/detection signals across cards, selectors, rules and reports | **Accepted — founder-supplied assets and research direction** |
| **P-017** | **2026-10-24** | **Founder-supplied primary Provenably brand mark** — use the attached 64×64 transparent check as the only primary logo/brand icon and favicon; retire the generated orange rounded-square mark; preserve its geometry/padding and mirror the asset to the legacy fallback | **Accepted — native-color clause superseded by P-018** |
| **P-018** | **2026-10-24** | **Palette-force the primary Provenably mark to the Zapier-derived website primary `#ff4f00`** — retain the supplied native-`#fd7e14` file only as source provenance; ship a canonical PNG whose geometry/alpha are pixel-identical and whose RGB is uniformly `#ff4f00` | **Accepted — founder correction** |
| **P-019** | **2026-10-24** | **Ban side-stripe accent bars** — remove every thick colored `border-left`/`border-right` treatment from cards, panels, notices and conclusions; replace it with complete hairline frames, contained semantic icons, neutral structural dividers and mandatory worded tags | **Accepted — founder rejection of AI-template pattern** |
| **P-020** | **2026-10-24** | **Adopt Hanken Grotesk as the complete website sans** — one open-source, self-hosted Latin variable family for display/body/UI with quiet-premium 530–540 display, semantic weights capped at 700, sparse uppercase eyebrows, the shipped face's lining equal-width figures plus tabular data declarations, true conditional italic, and JetBrains Mono retained route-split for technical data | **Accepted — founder-approved after typography comparison** |

## 14. Document history

| Date | Change | Author |
|---|---|---|
| 2026-10-24 | v1: product/UX design from codebase audit (flat v0 tokens, pages, flows, copy rules). | Engineering |
| 2026-10-24 | P-010/P-011/P-012/P-013 sequence: Detect wedge → philosophy → mockup v1 (violet) → v1 rejected, skills installed. | Founder + Engineering |
| 2026-10-24 | **v2 complete rewrite (P-014):** full Zapier-derived token/component/pattern system above; product sections (§12) and decision history preserved. | Founder (direction + source file) + Engineering |
| 2026-10-24 | **P-015 implementation:** design approved and converted to the production SvelteKit frontend with performance budgets. | Founder + Engineering |
| 2026-10-24 | **P-016 implementation:** founder-supplied platform marks and the 2026-10-24 platform-label/detection research were integrated into the Svelte cards/selectors and FastAPI platform-rule contract. | Founder (assets + direction) + Engineering |
| 2026-10-24 | **P-017 implementation:** the founder-supplied check PNG became the canonical header/footer/favicon/design-system mark, with a byte-identical legacy-fallback mirror. | Founder (asset + direction) + Engineering |
| 2026-10-24 | **P-018 correction:** the canonical mark was palette-forced from native `#fd7e14` to `#ff4f00` while preserving its alpha channel pixel-for-pixel; the untouched supplied file was retained as source only. | Founder (correction) + Engineering |
| 2026-10-24 | **P-019 implementation:** all notice/conclusion/report-preview side stripes were removed from production, legacy and mockup CSS and replaced with hairline frames, contained icons, a conclusion header divider and worded tags. | Founder (rejection + direction) + Engineering |
| 2026-10-24 | **P-020 implementation:** Inter was replaced site-wide with self-hosted Latin Hanken Grotesk Variable, semantic weight/tracking/numeral tokens were applied across production components and the Jinja fallback, and the design-system typography specimen was rebuilt around real roles, figures, glyph distinction and true italic. | Founder (selection + approval) + Engineering |
