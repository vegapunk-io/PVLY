<script lang="ts">
	import { resolve } from '$app/paths';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import PlatformCard from '#lib/components/PlatformCard.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import { presetDefinitions } from '#lib/data/presets.js';

	const formats = [
		'JPG',
		'PNG',
		'WebP',
		'MP4',
		'MOV',
		'WebM',
		'WAV',
		'MP3',
		'M4A',
		'FLAC',
		'OGG',
		'PDF',
		'DOCX',
		'TXT',
		'HEIC*',
		'AVIF*'
	];

	const checks = [
		[
			'Content Credentials',
			'C2PA signing state, trust, digital source type, actions, ingredients and hard-binding tamper checks.'
		],
		[
			'Metadata forensics',
			'EXIF, XMP/IPTC source types, PNG text, document properties, ID3 and container generator strings.'
		],
		[
			'Open watermarks',
			'DWT-DCT decoding for the Stable Diffusion pipeline family, reported with match strength rather than a binary guess.'
		],
		[
			'Forensic context',
			'JPEG, spectral, frame and container observations that support interpretation—but never become the verdict alone.'
		],
		[
			'Text signals',
			'Hidden Unicode characters, typography statistics and an optional keyed green-list watermark test.'
		],
		[
			'Platform consequences',
			'Likely label triggers for Meta, YouTube, TikTok, LinkedIn, Pinterest, X and the rest of the rules catalogue.'
		]
	];
</script>

<PageHead
	title="Provenably"
	description="See what a file says about its origin. Detect C2PA, AI metadata and provenance signals, then follow an honest Detect → Remove → Verify → Platform-ready workflow."
/>

<section class="hero shell">
	<div class="hero__grid">
		<div>
			<p class="eyebrow">AI content provenance &amp; metadata control</p>
			<h1>See what your file says about you. Then decide what stays.</h1>
			<p class="lede">
				Every photo, video, audio file and document can carry hidden cargo—Content Credentials, AI
				source tags, GPS, device details and generator fingerprints. Provenably detects those
				signals and is built around a lossless remove-and-verify workflow before you publish
				anywhere.
			</p>

			<ol class="loop" aria-label="Provenably workflow">
				<li>
					<span class="loop__step">1 · Detect</span><span class="loop__arrow" aria-hidden="true"
						>→</span
					>
				</li>
				<li>
					<span class="loop__step">2 · Remove</span><span class="loop__arrow" aria-hidden="true"
						>→</span
					>
				</li>
				<li>
					<span class="loop__step">3 · Verify</span><span class="loop__arrow" aria-hidden="true"
						>→</span
					>
				</li>
				<li><span class="loop__step">4 · Platform-ready</span></li>
			</ol>

			<div class="actions">
				<a class="btn" href={resolve('/scan')}
					>Scan a file — free <Icon name="arrow-right" size={19} /></a
				>
				<a class="btn btn--secondary" href={resolve('/remove')}>Remove metadata</a>
				<a class="text-link" href={resolve('/scan?tab=demo')}
					>Try a signed demo <Icon name="arrow-right" size={17} /></a
				>
			</div>

			<ul class="format-strip hero__formats" aria-label="Supported and roadmap formats">
				{#each formats as format (format)}<li class="format-chip">{format}</li>{/each}
			</ul>
			<p class="tiny muted">
				* HEIC and AVIF complete the format roadmap in R4; detection coverage is shown on every
				report.
			</p>
		</div>

		<aside class="report-preview" aria-label="Illustrative Provenably report preview">
			<div class="report-preview__head">
				<div>
					<p class="eyebrow">Provenance report</p>
					<p class="report-preview__file">ai_generated_signed.jpg</p>
				</div>
				<Tag tone="tag--accent">illustrative</Tag>
			</div>

			<div class="report-preview__conclusion">
				<p>AI-generated, declared in a Content Credential</p>
				<div class="row">
					<Tag tone="tag--strong">evidence: strong</Tag>
					<Tag>ai_generated_declared</Tag>
				</div>
			</div>

			<dl class="report-preview__signals">
				<div>
					<dt>Content Credentials</dt>
					<dd><Tag tone="tag--ok">detected</Tag></dd>
				</div>
				<div>
					<dt>EXIF / XMP / IPTC</dt>
					<dd><Tag tone="tag--accent">present</Tag></dd>
				</div>
				<div>
					<dt>Open watermark</dt>
					<dd><Tag>absent</Tag></dd>
				</div>
				<div>
					<dt>Vendor watermark</dt>
					<dd><Tag tone="tag--manual">not configured</Tag></dd>
				</div>
			</dl>

			<div class="report-preview__coverage">
				<div class="row row--between">
					<strong>Coverage shown, never hidden</strong>
					<span class="small muted">9 live · 5 manual · 0 errors</span>
				</div>
				<div class="progress" aria-hidden="true"><span style="transform:scaleX(.68)"></span></div>
				<p class="small muted">
					A clean-looking result is only as strong as the checks that actually ran.
				</p>
			</div>
		</aside>
	</div>
</section>

<section class="section section--soft" aria-labelledby="how-title">
	<div class="shell">
		<div class="section-head">
			<p class="eyebrow">How it works</p>
			<h2 id="how-title">One pass. Fully evidenced.</h2>
			<p class="lede">
				Provenably never removes blind, and it never asks you to trust a colored dot. Every claim
				keeps the signal, method, evidence grade and coverage beside it.
			</p>
		</div>

		<div class="grid grid--3">
			<article class="card card--canvas feature-card">
				<span class="feature-icon"><Icon name="scan" size={25} /></span>
				<p class="feature-step">Detect</p>
				<h3>A provenance report first</h3>
				<p>
					C2PA trust and tamper state, metadata, AI source types, generator strings and open
					watermarks—each with an evidence grade and raw data when you need to inspect it.
				</p>
				<a class="text-link" href={resolve('/scan')}
					>Run a scan <Icon name="arrow-right" size={17} /></a
				>
			</article>

			<article class="card card--canvas feature-card">
				<span class="feature-icon"><Icon name="layers" size={25} /></span>
				<p class="feature-step">Remove</p>
				<h3>Lossless footprint removal</h3>
				<p>
					The production workflow targets container footprints first—C2PA manifests, metadata tags
					and document properties—without touching pixels or samples by default.
				</p>
				<a class="text-link" href={resolve('/remove')}
					>See the removal flow <Icon name="arrow-right" size={17} /></a
				>
			</article>

			<article class="card card--canvas feature-card">
				<span class="feature-icon"><Icon name="shield" size={25} /></span>
				<p class="feature-step">Verify</p>
				<h3>Proof, not promises</h3>
				<p>
					The cleaned output is designed to be re-scanned by the same detectors, producing a
					before/after diff, input/output hashes and a precise statement of anything embedded that
					remains.
				</p>
				<a class="text-link" href={resolve('/presets')}
					>Prepare a platform export <Icon name="arrow-right" size={17} /></a
				>
			</article>
		</div>
	</div>
</section>

<section class="section shell" aria-labelledby="layers-title">
	<div class="section-head">
		<p class="eyebrow">Honest by design</p>
		<h2 id="layers-title">Two layers. One promise we can keep.</h2>
	</div>

	<div class="grid grid--2">
		<article class="card layer-card">
			<div class="row row--between">
				<h3>Layer 1 · Removable</h3>
				<Tag tone="tag--ok">container footprints</Tag>
			</div>
			<p>
				C2PA manifests, EXIF/XMP/IPTC, PNG text, ID3/RIFF/MP4 tags, document authors and revision
				history live in the file container. These can be removed and then verified absent.
			</p>
			<ul class="check-list">
				<li><Icon name="check" size={18} /> Lossless-first, per-format policy</li>
				<li><Icon name="check" size={18} /> Before and after SHA-256 hashes</li>
				<li><Icon name="check" size={18} /> Re-scan instead of a success toast</li>
			</ul>
		</article>

		<article class="card layer-card layer-card--reported">
			<div class="row row--between">
				<h3>Layer 2 · Reported</h3>
				<Tag tone="tag--manual">never faked</Tag>
			</div>
			<p>
				SynthID, AudioSeal, VideoSeal and similar marks are embedded in pixels or samples. Metadata
				removal does not touch them, and Provenably will never claim that it did.
			</p>
			<ul class="check-list">
				<li><Icon name="check" size={18} /> Detected where a live or vendor connector exists</li>
				<li><Icon name="check" size={18} /> “Not configured” is shown when a check did not run</li>
				<li><Icon name="check" size={18} /> Residual risk stated in the final report</li>
			</ul>
		</article>
	</div>

	<div class="layer-note">
		<Notice tone="info" title="Privacy and disclosure stay separate.">
			<p>
				Removing GPS, device or author metadata from your own file is a normal privacy action. It
				does not remove a legal or platform duty to disclose synthetic content. Provenably pairs
				technical findings with dated, confidence-graded rules—but it is not legal advice.
			</p>
		</Notice>
	</div>
</section>

<section class="section section--soft" aria-labelledby="platforms-title">
	<div class="shell">
		<div class="section-head row--between section-head--wide">
			<div>
				<p class="eyebrow">Platform presets</p>
				<h2 id="platforms-title">Export for where the file is going.</h2>
				<p class="lede">
					A preset combines the output target, Layer-1 footprint policy, verification step and the
					exact label that destination can show—plus the provenance signals it is documented to
					read. The generic verified master remains available for your own channels.
				</p>
			</div>
			<a class="btn btn--secondary" href={resolve('/presets')}>Compare presets</a>
		</div>

		<div class="grid grid--4">
			{#each presetDefinitions as preset (preset.slug)}
				<PlatformCard {preset} href={resolve(`/presets?preset=${preset.slug}`)} />
			{/each}
		</div>
		<p class="small muted trademark-note">
			Marks belong to their owners and identify destinations only. Label research checked 24 October
			2026.
		</p>
	</div>
</section>

<section class="section shell" aria-labelledby="checks-title">
	<div class="grid grid--sidebar">
		<div>
			<p class="eyebrow">What a Detect run checks today</p>
			<h2 id="checks-title">Signals with receipts—not a black-box “AI score.”</h2>
			<p class="lede">
				Passive forensic observations add context, but a conclusion is anchored to
				provenance-bearing signals. Absence is reported as absence, never as proof of human
				authorship.
			</p>
			<div class="actions">
				<a class="btn btn--dark" href={resolve('/api')}>See live deployment coverage</a>
				<a class="text-link" href={resolve('/registry')}
					>Browse generator registry <Icon name="arrow-right" size={17} /></a
				>
			</div>
		</div>

		<div class="table-wrap">
			<table>
				<caption class="visually-hidden">Provenably detection checks</caption>
				<thead
					><tr><th scope="col">Signal family</th><th scope="col">What is reported</th></tr></thead
				>
				<tbody>
					{#each checks as [name, description] (name)}
						<tr><th scope="row">{name}</th><td>{description}</td></tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
</section>

<section class="section section--soft" aria-labelledby="roadmap-title">
	<div class="shell">
		<div class="section-head">
			<p class="eyebrow">Deployment truth</p>
			<h2 id="roadmap-title">What is live, and what ships next.</h2>
			<p>
				The approved end-to-end interface is now in place. Backend capabilities are labelled by
				milestone so a roadmap workflow can never masquerade as a completed removal.
			</p>
		</div>

		<div class="grid grid--3">
			<article class="card card--canvas">
				<Tag tone="tag--ok">live now</Tag>
				<h3>Detect</h3>
				<p>
					File, text, URL and demo scans; graded reports; registry; disclosure rules; text tools;
					and API status.
				</p>
				<a class="text-link" href={resolve('/scan')}
					>Use Detect <Icon name="arrow-right" size={17} /></a
				>
			</article>
			<article class="card card--canvas">
				<Tag tone="tag--accent">R0–R2</Tag>
				<h3>Remove + Verify</h3>
				<p>
					Images, PDF and DOCX first, then audio and video. The Svelte workflow, attestation and
					verification contract are ready.
				</p>
				<a class="text-link" href={resolve('/remove')}
					>Review the workflow <Icon name="arrow-right" size={17} /></a
				>
			</article>
			<article class="card card--canvas">
				<Tag tone="tag--accent">R3–R4</Tag>
				<h3>Batch, presets, more formats</h3>
				<p>
					Multi-file exports with ZIP manifests, platform transformations, then HEIC, AVIF, GIF and
					TIFF coverage.
				</p>
				<a class="text-link" href={resolve('/batch')}
					>See batch Detect <Icon name="arrow-right" size={17} /></a
				>
			</article>
		</div>
	</div>
</section>

<section class="section shell cta" aria-labelledby="cta-title">
	<div class="card card--dark cta__card">
		<div>
			<p class="eyebrow cta__eyebrow">Start with evidence</p>
			<h2 id="cta-title">Know what your next upload is carrying.</h2>
			<p>
				Run a free Detect scan or inspect one of the signed, tampered, watermarked and stripped demo
				fixtures. Hash-only mode deletes uploaded bytes immediately after analysis.
			</p>
		</div>
		<div class="actions cta__actions">
			<a class="btn" href={resolve('/scan')}>Scan a file</a>
			<a class="btn btn--secondary" href={resolve('/pricing')}>View plans</a>
		</div>
	</div>
</section>

<style>
	.hero {
		padding: clamp(3rem, 7vw, 5.5rem) 0 clamp(3.2rem, 7vw, 5rem);
	}

	.hero__grid {
		align-items: center;
		display: grid;
		gap: clamp(2rem, 5vw, 4.5rem);
		grid-template-columns: minmax(0, 1.08fr) minmax(340px, 0.72fr);
	}

	.hero h1 {
		font-size: clamp(2.8rem, 6vw, 4.6rem);
		max-width: 820px;
	}

	.hero__formats {
		margin-top: 2rem;
	}

	.report-preview {
		background: var(--canvas-soft);
		border: 1px solid var(--line);
		border-radius: 16px;
		padding: clamp(1.2rem, 3vw, 1.6rem);
	}

	.report-preview__head {
		align-items: flex-start;
		display: flex;
		gap: 1rem;
		justify-content: space-between;
	}

	.report-preview__head .eyebrow {
		margin-bottom: 0.35rem;
	}

	.report-preview__file {
		color: var(--ink);
		font-family: var(--font-mono);
		font-size: 0.92rem;
		margin: 0;
		overflow-wrap: anywhere;
	}

	.report-preview__conclusion {
		background: var(--canvas);
		border: 1px solid var(--ink);
		border-radius: var(--radius);
		margin-top: 1.2rem;
		padding: 1.1rem;
	}

	.report-preview__conclusion p {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.35rem;
		font-weight: 560;
		line-height: 1.2;
	}

	.report-preview__signals {
		display: grid;
		gap: 0;
		margin: 1.1rem 0;
	}

	.report-preview__signals > div {
		align-items: center;
		border-bottom: 1px solid var(--line);
		display: flex;
		gap: 1rem;
		justify-content: space-between;
		padding: 0.72rem 0;
	}

	.report-preview__signals dt {
		color: var(--ink-mid);
		font-weight: 620;
	}

	.report-preview__signals dd {
		margin: 0;
	}

	.report-preview__coverage {
		background: var(--canvas);
		border-radius: var(--radius);
		padding: 1rem;
	}

	.report-preview__coverage .progress {
		margin: 0.8rem 0;
	}

	.report-preview__coverage p {
		margin: 0;
	}

	.feature-card {
		display: flex;
		flex-direction: column;
		min-height: 100%;
	}

	.feature-card .text-link {
		margin-top: auto;
	}

	.feature-icon {
		align-items: center;
		background: var(--primary-soft);
		border-radius: 50%;
		color: var(--primary-hover);
		display: inline-flex;
		height: 3.2rem;
		justify-content: center;
		margin-bottom: 1rem;
		width: 3.2rem;
	}

	.feature-step {
		color: var(--accent-ink);
		font-size: 0.82rem;
		font-weight: 800;
		letter-spacing: 0.09em;
		margin-bottom: 0.4rem;
		text-transform: uppercase;
	}

	.layer-card {
		min-height: 100%;
	}

	.layer-card--reported {
		background: var(--canvas);
		border: 1px solid var(--line);
	}

	.check-list {
		display: grid;
		gap: 0.55rem;
		list-style: none;
		margin: 1.1rem 0 0;
		padding: 0;
	}

	.check-list li {
		align-items: flex-start;
		color: var(--ink-mid);
		display: flex;
		gap: 0.55rem;
	}

	.check-list :global(svg) {
		color: var(--primary-hover);
		margin-top: 0.18rem;
	}

	.layer-note {
		margin-top: 1rem;
	}

	.section-head--wide {
		align-items: end;
		display: flex;
		gap: 2rem;
		justify-content: space-between;
		max-width: none;
	}

	.trademark-note {
		margin-top: 0.8rem;
	}

	.cta {
		padding-top: 1rem;
	}

	.cta__card {
		align-items: center;
		display: grid;
		gap: 2rem;
		grid-template-columns: minmax(0, 1fr) auto;
		padding: clamp(1.6rem, 4vw, 2.6rem);
	}

	.cta__eyebrow {
		color: var(--on-primary);
	}

	.cta__actions {
		flex-direction: column;
		align-items: stretch;
		min-width: 210px;
	}

	@media (max-width: 980px) {
		.hero__grid,
		.cta__card {
			grid-template-columns: 1fr;
		}

		.cta__actions {
			flex-direction: row;
		}
	}

	@media (max-width: 680px) {
		.section-head--wide {
			align-items: start;
			flex-direction: column;
		}

		.report-preview__signals > div {
			align-items: flex-start;
			flex-direction: column;
			gap: 0.35rem;
		}

		.cta__actions {
			flex-direction: column;
		}
	}
</style>
