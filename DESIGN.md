---
version: 2.0
name: Provenably-design-system
description: Provenably's complete design system, reverse-engineered from Zapier's design language (source `zapier/DESIGN.md`, fetched with `npx getdesign@latest add zapier`) and adapted to a forensic Detect → Remove → Verify product. Warm-cream canvas (`#fffefb`), deep coffee ink (`#201515`), one saturated orange CTA (`#ff4f00`), Degular-style display type rendered in Inter 500, 12px middle radius, flat elevation. Product evidence grades are the only semantic colors.

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
  display-xl:  { fontFamily: "Degular Display, Inter, system-ui, sans-serif", fontSize: 56px, fontWeight: 500, lineHeight: 56px }
  display-lg:  { fontFamily: "Degular Display, Inter, system-ui, sans-serif", fontSize: 48px, fontWeight: 500, lineHeight: 48px }
  display-md:  { fontFamily: "Degular Display, Inter, system-ui, sans-serif", fontSize: 32px, fontWeight: 500, lineHeight: 36px }
  heading-sm:  { fontFamily: "Inter, system-ui, sans-serif", fontSize: 20px, fontWeight: 700, lineHeight: 25px, letterSpacing: -0.5px }
  body-lg:     { fontFamily: "Inter, system-ui, sans-serif", fontSize: 20px, fontWeight: 400, lineHeight: 30px, letterSpacing: -0.2px }
  body-md:     { fontFamily: "Inter, system-ui, sans-serif", fontSize: 18px, fontWeight: 400, lineHeight: 27px }
  body-sm:     { fontFamily: "Inter, system-ui, sans-serif", fontSize: 16px, fontWeight: 400, lineHeight: 24px }
  caption:     { fontFamily: "Inter, system-ui, sans-serif", fontSize: 14px, fontWeight: 400, lineHeight: 21px }
  eyebrow:     { fontFamily: "Degular Display, Inter, system-ui, sans-serif", fontSize: 14px, fontWeight: 500, lineHeight: 14px, letterSpacing: 1px, textTransform: uppercase }
  button-md:   { fontFamily: "Inter, system-ui, sans-serif", fontSize: 18px, fontWeight: 600, lineHeight: 27px }
  button-sm:   { fontFamily: "Inter, system-ui, sans-serif", fontSize: 14.4px, fontWeight: 700, lineHeight: 1.2 }
  mono:        { fontFamily: "JetBrains Mono, ui-monospace, Menlo, monospace", fontSize: 0.86em }

rounded: { none: 0px, sm: 6px, md: 12px, pill: 9999px }
spacing: { xxs: 2px, xs: 4px, sm: 8px, md: 12px, lg: 16px, xl: 24px, 2xl: 32px, 3xl: 48px, 4xl: 64px }
---

# DESIGN.md — Provenably design system (complete)

> Status: **v2 founder-approved and implemented in the SvelteKit production frontend (`frontend/`)** · 2026-10-24 · Decisions **P-014/P-015**
> Source reverse-engineered: [`zapier/DESIGN.md`](zapier/DESIGN.md) (identical to the founder-supplied `DESIGN-zapier.md`; fetched via `npx getdesign@latest add zapier`).
> Companions: [`PHILOSOPHY.md`](PHILOSOPHY.md) · [`WIREFRAME.md`](WIREFRAME.md) · [`AGENTS.md`](AGENTS.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md).
> Implementation of record: `frontend/src/app.css` + Svelte components/routes. `mockup/` remains the approved visual archive. **No linear gradients anywhere. No decorative shadows.**

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
| Single orange `#ff4f00` = every primary CTA | Orange = primary buttons, focus, active states, brand mark — and nothing else decorative |
| Degular Display 500 hero + Inter everything else; sentence-case headlines | Display stack names Degular then Inter (renders Inter 500 — the source file's own named substitute); all headlines sentence-case |
| Eyebrow: uppercase 14px, +1px tracking | Kept (brief/spec wins — see §10 deviation note), used sparingly, ink-colored |
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
- **Logo:** Provenably check in an orange rounded square (8px radius at 30px), wordmark in
  display face 600. Favicon: same mark, `#ff4f00` field.
- **Product loop as the signature motif:** `Detect → Remove → Verify → Platform-ready`
  pill sequence (cream pills, orange arrows) replaces any decorative hero art.

## 3. Color

### 3.1 Core (from source, unchanged values)
| Token | Hex | Role |
|---|---|---|
| `primary` | `#ff4f00` | Primary CTA bg, brand mark, focus ring, active indicators, progress fill |
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
only in grade tags, conclusion left-rules, status dots, and verify diffs — never as
decoration, backgrounds of marketing sections, or a "second accent".

### 3.4 Color don'ts
No pure white/black surfaces · no cool-gray tokens · no gradients · no second brand hue ·
no orange body links at small size (links are ink + underline, hover orange) ·
no orange grade.

## 4. Typography

Two voices, strict roles. **Display** (`Degular Display, Inter, …` — proprietary face
unavailableweights rendered as Inter 500 per the source's substitute note): hero 56/56,
page H1 48/48 (app pages 40/42), section H2 32/36. **Inter**: body-md 18/27 default page
text, body-sm 16/24 in app density, caption 14/21, heading-sm 20/700/-0.5px for card titles,
button-md 18/600, button-sm 14.4/700. **JetBrains Mono**: hashes, IDs, filenames, code,
format chips only. Sentence-case headlines, always. Line-length: lede ≤720px, prose ≤80ch.

## 5. Layout, spacing, responsive

4px base; tokens 2/4/8/12/16/24/32/48/64. Container 1280px + 24px gutters. Bands pad 64px
(`.section`, hero); cards pad 24px. Sticky nav (canvas, warm hairline, 64px min-height).
Grids: `.grid2/3/4` → 2-col ≤1023px → 1-col ≤767px; nav scrolls horizontally when tight;
signal rows stack ≤767px; hero 56→40px. Touch: buttons ≥48px, small buttons ≥38px,
tabs ≥44px (ui-ux-pro-max priority-2 rule).

## 6. Elevation & shape

Level 0 flat (bands) → Level 1 hairline (`1px solid ink` on pricing/conclusion/inputs;
`line` in dense tables) → Level 2 cream card on canvas (default). **Zero shadows.**
Radius: 12px buttons/cards/panels/notices/pre · 6px inputs/format chips · pill badges/tags/avatars · 0 bands.

## 7. Components (mockup class → spec)

| Component | Spec (all in `mockup/style.css`) |
|---|---|
| `button`/`.btn` | primary orange, on-primary text, 12px radius, 10–12×24 pad, ≥48px, button-md; hover `primary-hover` |
| `.btn.dark` | Zapier button-secondary: ink fill |
| `.btn.secondary` | Zapier button-tertiary: canvas fill, 1px ink border, ink text |
| `.btn.small` | button-sm 14.4/700, ≥38px |
| `.box` (card-content) | canvas-soft, 12px, 24px pad — the default card everywhere |
| `.pricecard` / `.featured` | canvas + 1px ink border / flipped ink fill + orange plan tag |
| `.platcard` | canvas-soft selectable card; `.sel` = 2px primary outline on canvas (app-shell active-indicator rule) |
| inputs/select/textarea | canvas, 1px ink border, 6px radius, 12×16 pad, 18px; focus border primary + 2px outline |
| `.check` | 17px checkbox, `accent-color: primary` |
| `.tag` (badge-pill) | pill, canvas-soft, mute border; semantic variants `.ok/.warn/.bad/.accent/.manual(dashed)` |
| `.dot` | 9px status dot, semantic fills |
| `.tabs` | ink text, 3px primary underline on active, ≥44px targets |
| `.drop` | 1.5px dashed body-mid on canvas-soft; drag-over → primary border + primary-soft fill; real `<input type=file>` inside, always |
| `.conclusion` | canvas, 1px ink border, 12px radius, **7px grade left-rule**; label in display 26/500 |
| `.signal` | 190px name/meta rail + body; `.how` (manual step) in warn tone |
| `.notice` | 12px card, mute border + 5px semantic left bar; `.info` uses primary bar on canvas-soft |
| `.steps` | numbered circles: current=primary, done=ink ✓, pending=mute |
| `.progress` | 6px pill track (canvas-soft + line border), primary fill; indeterminate slide, reduced-motion off |
| `table` | header canvas-soft 14px semibold ink-mid; 12×16 cells; `line` row rules; warm hover `#fbf7f1` |
| `.loop .stepchip` | cream pill + orange arrow — the product-loop motif |
| `.fmt` | mono 13px format chip, 6px radius, canvas-soft |
| `.empty` | canvas-soft 48px-pad empty-state card (ex-empty-state-card) |
| `pre` | ink surface, canvas-soft mono text, 12px radius |

## 8. Page patterns (15 mockup pages — bands & composition)

- **Landing** (`index`): canvas hero-band (display-xl, loop motif, 3 CTAs: primary/tertiary/dark) → canvas-soft "how it works" band (3 cream cards on cream get hairline via surface step) → canvas honesty section (2-layer cards + info notice) → canvas-soft platforms band (8 platcards) → canvas teasers + centered CTA → dark footer.
- **App pages** (`scan/remove/batch/presets/history/settings`): pagehead (eyebrow + 40px display H1) → working grid (form/dropzone left, evidence panels right) → full-width tables. Canvas bg, cream cards.
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
next to the action (baseline-ui). Motion: only the progress indeterminate; no entrance
animations, no hover transitions invented per-card; `prefers-reduced-motion` kills it.
Keyboard: native elements only in the mockup (buttons, details, file inputs) — no
hand-rolled focus behavior to break.

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

## 12. Product design carried over (still binding)

Philosophy: **Detect → Remove → Verify → Platform-ready** (`PHILOSOPHY.md`). Sitemap,
flows, per-page sections/states and backend hooks: `WIREFRAME.md §§2–3` (unchanged by the
re-skin). Copy rules unchanged: reports describe signals & grades, never verdicts on
authorship; forbidden claims ("human-made", "watermark removed", "undetectable");
required honesty copy (coverage, Layer-2 disclaimer, attestation, "not legal advice",
TEST-signer labeling). Personas: newsroom/OSINT, creator, compliance/publisher,
platform/moderation, developer.

**Open decisions:** D3 pricing numbers (tiers are placeholders) · D4 batch-scan UX detail ·
D5 HEIC/AVIF/RAW coverage messaging. **D6 resolved (P-015):** self-host only the Latin
variable subsets of Inter and JetBrains Mono via Fontsource; mono is route-split.

## 13. Decision log (append-only)

| ID | Date | Decision | Status |
|---|---|---|---|
| P-001 | ≤2026-10-14 | One graded Provenance Report; "not a verdict on authorship" | Accepted |
| P-002 | ≤2026-10-14 | Evidence-grade color convention on conclusion block (+ grade word always) | Accepted (moderate color updated by P-014) |
| P-003 | ≤2026-10-14 | Coverage/manual modules visible in-product | Accepted |
| P-004 | ≤2026-10-14 | Flat/minimal visual system v0 (superseded visually by P-012, then P-014) | Superseded |
| P-005 | ≤2026-10-14 | Public generator Registry with confidence/last-verified | Accepted |
| P-006 | ≤2026-10-14 | 17 demo fixtures as first-class product surface | Accepted |
| P-007→P-011 | 2026-10-23/24 | Sanitizer added → removed (P-010) → philosophy clarified Detect→Remove→Verify (`PHILOSOPHY.md`) | P-011 Accepted |
| P-009 | 2026-10-24 | Mandatory decision logging in these docs | Accepted |
| P-012 | 2026-10-24 | Mockup-first, full end-to-end; violet flat-forensic mockup v1 | Superseded by P-014 (visuals) |
| P-013 | 2026-10-24 | Mockup v1 **rejected** by founder ("AI-sloppy"); 10 skills installed; v2 gated on skills + founder guidance | Accepted |
| **P-014** | **2026-10-24** | **Adopt Zapier design language (reverse-engineered from `zapier/DESIGN.md`) as Provenably's complete design system** — warm cream/coffee/orange, display-Inter, 12px radius, flat elevation — applied to all 15 mockup pages via one stylesheet; bounded semantic-grade exception (§3.3); skills log §10 | **Accepted — founder-approved 2026-10-24** |
| **P-015** | **2026-10-24** | **Implement P-014 as SvelteKit/Svelte 5 + TypeScript static frontend with FastAPI retained as JSON backend** — prerendered public pages, selective hydration, self-hosted Latin font subsets, measured bundle budget | **Accepted — founder-approved implementation direction** |

## 14. Document history

| Date | Change | Author |
|---|---|---|
| 2026-10-24 | v1: product/UX design from codebase audit (flat v0 tokens, pages, flows, copy rules). | Engineering |
| 2026-10-24 | P-010/P-011/P-012/P-013 sequence: Detect wedge → philosophy → mockup v1 (violet) → v1 rejected, skills installed. | Founder + Engineering |
| 2026-10-24 | **v2 complete rewrite (P-014):** full Zapier-derived token/component/pattern system above; product sections (§12) and decision history preserved. | Founder (direction + source file) + Engineering |
| 2026-10-24 | **P-015 implementation:** design approved and converted to the production SvelteKit frontend with performance budgets. | Founder + Engineering |
