# PHILOSOPHY.md — Provenably (PVLY)

> The north star. Every product, design, and engineering decision is judged against this
> document. Companion docs: [`AGENTS.md`](AGENTS.md) · [`ARCHITECTURE.md`](ARCHITECTURE.md) ·
> [`DESIGN.md`](DESIGN.md).
>
> Status: **Accepted — founder clarification, 2026-10-24** (DESIGN P-011 / ARCHITECTURE A-013).
> This supersedes the earlier same-day "Detect-only, no sanitizers" decision (P-010/A-012).
> **Engineering status:** current code is Detect-only (sanitizer removed under P-010);
> restoring + expanding removal is the roadmap in §8 — not yet built.

---

## 1. Mission (founder's objective, clarified verbatim in intent)

> **Detect and remove C2PA metadata and AI footprints from any media format — image,
> video, audio, document, text — and make the file ready for every platform where people
> publish: YouTube, LinkedIn, Instagram, TikTok, Pinterest, Reddit, X/Twitter, and beyond.**

One-line product truth: **Detect → Remove → Verify → Platform-ready.** Detection is how the
user learns the truth about a file; removal is the action they came for; verification is the
proof; platform readiness is the reason it matters. "Detect" is the wedge/front door —
removal completes the job in the same pass.

## 2. Why this exists

Every file a creator exports now carries an invisible cargo: Content Credentials (C2PA)
manifests, EXIF camera/GPS data, XMP/IPTC source-type tags, generator and encoder strings,
document authors and revision histories, audio/video container tags. Most people have no
idea their file says all of this, no way to see it, and no clean way to take it off before
the file leaves their control. Existing answers are fragmented expert tools (ExifTool CLI,
mat2, hand re-encoding) that neither show you what was there nor prove what is gone.
**Provenably is the single place a person controls what their own file says about them —
before they publish it anywhere.**

## 3. The core loop (non-negotiable product shape)

1. **DETECT** — full provenance report first: C2PA trust/source-type/tamper, metadata,
   open-watermark and vendor signals, each with an evidence grade and coverage.
   *Never remove blind.*
2. **REMOVE** — strip the removable footprints (§5, Layer 1), **lossless-first**: pixels and
   samples byte-identical unless the user explicitly chooses re-encode/preset conversion.
3. **VERIFY** — re-scan the output with the same detectors and show the before/after diff
   with a verdict. *The verify step is the differentiator; a strip you cannot prove is a claim.*
4. **PLATFORM-READY** — per-platform export (§7): right format/size/quality, footprints
   removed, plus that platform's labelling reality and the user's disclosure obligations.

## 4. Format scope — "any type of format"

| Family | Formats (target) | AI footprints we detect | Footprints we remove (Layer 1) | Status today |
|---|---|---|---|---|
| **Image** | JPG/JPEG, PNG, WebP → next: HEIC/AVIF, GIF, TIFF | C2PA/JUMBF, EXIF, XMP/IPTC `DigitalSourceType`, PNG text (A1111 `parameters`), generator strings, DWT-DCT watermark | APP1/APP11/APP13 segments, `caBX`, tEXt/zTXt/iTXt, eXIf, EXIF/XMP chunks, comments, thumbnails | Detect ✅ live · Remove: **built before, recoverable from git `beb4143`** |
| **Video** | MP4, MOV, WebM → next: MKV | C2PA (BMFF `uuid`/manifest boxes), `udta`/`meta`/encoder (`©too`) tags, per-frame watermarks | Container-level C2PA boxes and metadata tags via stream-copy remux (streams/duration unchanged) | Detect ✅ live (BMFF walk + frame sampling) · Remove: **to build — recommended, §6** |
| **Audio** | WAV, MP3, M4A/AAC, FLAC, OGG | C2PA RIFF/MP4 chunks, ID3v1/v2, RIFF INFO/`bext`, Vorbis comments, encoder strings | All container tags/chunks (samples untouched) | Detect ✅ live (WAV/ID3 + C2PA) · Remove: **to build — recommended, §6** |
| **Document** | PDF, DOCX | PDF `/Info`+XMP, attachments (C2PA carriers); DOCX core/app/custom props, comments, tracked changes | All of the detected properties + metadata inside embedded media | Detect ✅ (via scan) · Remove: built before, recoverable |
| **Text** | TXT/any pasted text | Hidden characters (zero-width, bidi, homoglyphs), keyed green-list marks | Hidden characters (unicode hygiene; does not touch statistical marks) | ✅ Live (Text tools + Lab) |

## 5. The two layers — what "completely remove" can honestly mean

This distinction protects the product's credibility and is **binding on all copy and code**:

| | **Layer 1 — Container footprints** | **Layer 2 — Content-embedded watermarks** |
|---|---|---|
| What | C2PA manifests, EXIF/XMP/IPTC, PNG text, ID3/RIFF/MP4 tags, doc properties, encoder strings | SynthID, AudioSeal, VideoSeal, TrustMark, DWT-DCT and similar signals woven into pixels/samples/tokens themselves |
| Removable? | **Yes — completely, losslessly, verifiably.** This is our promise. | **No honest guarantee.** Metadata removal does not touch them; re-encoding degrades some fragile schemes, robust ones (e.g. SynthID) are designed to survive. |
| Our stance | Detect → remove → **prove** gone (Verify verdict). | Detect where we can, **report honestly** ("an embedded watermark may still be present"), never claim removal. |
| Copy rule | "C2PA and metadata removed — verified." | "Embedded watermarks, if present, are not removed." (required wherever removal is offered) |

We will never sell "make AI content undetectable." A product caught promising that loses
trust with users, platforms, and regulators at once — and trust is the asset (§9).

## 6. Recommendation: YES — add audio & video removal (founder asked; engineering answer)

**Why yes:** (1) The named platforms are video-first (YouTube, TikTok, Instagram Reels) —
an image-only remover misses the main job. (2) Our detectors for audio/video already exist
(WAV spectral + ID3, BMFF box walker, C2PA for WAV/MP4, per-frame watermark scan), so the
Verify half of the loop — the hard, differentiating half — is already built; removal is the
smaller half. (3) Container metadata is the honest, fully-soluble layer (§5).

**How (planned, see A-013):**
- **Audio:** `mutagen` (pure-Python) for ID3/MP4/Vorbis tag removal; a RIFF chunk walker
  (mirroring the existing JUMBF/BMFF walkers) for WAV INFO/`bext`/C2PA chunks. Samples untouched.
- **Video:** ffmpeg sidecar, **stream-copy** (`-c copy`, no re-encode by default) with
  metadata mapping cleared, plus a custom BMFF pass for C2PA boxes ffmpeg would carry over.
  Duration/streams/codecs must be unchanged; Verify re-runs C2PA + box walk + frame scan.
- **Order:** restore Images/PDF/DOCX (§8-R0) → Audio (R1, smaller, pure-Python) →
  Video (R2, needs ffmpeg + size/async care) → Platform presets (R3).

## 7. Platform strategy — "ready for every platform"

Core insight: **platforms strip most metadata on upload anyway — but several read C2PA/IPTC
first and label from it, and all of them can read Layer-2 watermarks we cannot remove.**
Our value is therefore (a) knowing exactly what your file carries *before* upload, (b) you —
not the platform — deciding what leaves your device, (c) a verified-clean master file for
your own site/email/direct distribution, and (d) knowing each platform's labelling rules
(already modelled in `app/rules/platforms.json`, 10 platforms).

| Platform | Main formats | Preset must handle (R3) |
|---|---|---|
| YouTube | MP4/MOV video, audio | Video container clean + size/quality; altered-content disclosure reminder |
| Instagram / Facebook / Threads | JPG/PNG, MP4 (Reels) | Image+video clean; Meta "AI info" reads C2PA/IPTC — explain what removal changes |
| TikTok | MP4 video | Video clean; AI-label rules reminder |
| LinkedIn | JPG/PNG, MP4, PDF/DOCX | Image/doc clean (author/GPS hygiene is the pro use-case) |
| Pinterest | JPG/PNG/WebP | Image clean + dimensions |
| Reddit | JPG/PNG, MP4/GIF | Image/video clean |
| X (Twitter) | JPG/PNG/WebP, MP4 | Image/video clean (platform recompresses regardless) |
| + already modelled | Google "About this image", Amazon KDP | Registry/rules coverage exists today |

Every preset output ships with its Detect report, removal diff, and a **disclosure note**:
removing metadata does not remove the user's legal duty to label synthetic content where
the law requires it (EU AI Act Art. 50, California SB 942/AB 853, India SGI Rules 2026,
China GB 45438-2025 — all already in `app/rules/jurisdictions.json`).

## 8. Roadmap to the philosophy (from today's Detect-only code)

| Phase | Deliverable | Acceptance test |
|---|---|---|
| **R0 Restore** | Bring back image (JPG/PNG/WebP) + PDF + DOCX removal from git history as a first-class **Remove** flow beside Scan (one report page: Detected → Removed → Verified); re-add pikepdf/lxml; fix old gaps: sanitized-blob expiry + user attestation | Old golden tests green (strip + verify + idempotent); new surface test replaces `test_detect_only_surface` |
| **R1 Audio** | WAV/MP3/M4A/FLAC/OGG tag & C2PA-chunk removal (`mutagen` + RIFF walker) + Verify via existing audio/C2PA analyzers | No ID3/RIFF/Vorbis tags remain; samples/duration identical |
| **R2 Video** | MP4/MOV/WebM container + C2PA-box removal, ffmpeg stream-copy; async for large files | No `udta`/C2PA boxes remain; streams/duration identical |
| **R3 Platforms** | 8 platform presets (§7) + batch (ZIP of outputs + JSON manifest) | Each preset: valid output, expected dims/format, verified clean |
| **R4 Reach** | HEIC/AVIF/GIF/TIFF detection+removal; batch scan+remove API polish | Fixtures per format, golden tests |

## 9. Principles & guardrails (binding)

1. **User control & privacy first** — people may remove metadata from *their own files*
   (GPS, device, author, edit history leak real-world safety/privacy). Require attestation
   ("this is my content / I have the right to modify it") in the removal UI.
2. **Verify, don't claim** — no removal ships without the re-scan diff (§3).
3. **Honesty about Layer 2** (§5) — in UI, API, and marketing, always.
4. **Lossless-first** — never degrade pixels/samples by default; re-encode only on explicit
   user choice or platform-preset conversion, always labelled.
5. **Detect stays first-class** — the report/audit trail (hashes in/out, fields removed)
   is retained per retention policy; we are a transparency tool that also removes, not an
   eraser that hides its own work.
6. **Law-aware** — jurisdiction nudges beside every removal (§7); never market evasion of
   disclosure laws or platform AI labels; not legal advice.
7. **Non-goals** — guaranteed watermark removal; forgery/impersonation aids; DRM
   circumvention; defeating forensic investigation.

## 10. Decision record & open confirmation

- **Conflict noted:** on 2026-10-24 the founder first directed *"wedge = Detect, no
  sanitizers anywhere"* (implemented fully: commit `f03d0af`, P-010/A-012), then clarified
  the philosophy recorded here: **detect AND remove, all formats, platform-ready**.
  This document (P-011/A-013) supersedes P-010/A-012 as product direction.
- **Current gap (honest):** shipped code today = Detect-only. Philosophy ≠ code until §8 runs.
- **Awaiting founder confirmation to proceed with R0** (restore) — after which AGENTS/
  ARCHITECTURE/DESIGN current-state sections are updated to the restored reality.

## 11. Document history

| Date | Change | Author |
|---|---|---|
| 2026-10-24 | Created from founder's philosophy clarification (detect + remove all formats, platform-ready); includes audio/video recommendation and R0–R4 roadmap. Supersedes P-010/A-012 as direction. | Founder (philosophy) + Engineering (structure/boundaries) |
