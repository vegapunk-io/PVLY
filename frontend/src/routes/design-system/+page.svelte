<script lang="ts">
	import { resolve } from '$app/paths';
	import '#lib/mono-font.css';
	import BrandMark from '#lib/components/BrandMark.svelte';
	import ConclusionCard from '#lib/components/ConclusionCard.svelte';
	import FileDrop from '#lib/components/FileDrop.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import PlatformCard from '#lib/components/PlatformCard.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import { findPreset } from '#lib/data/presets.js';
	import type { Conclusion } from '#lib/types.js';

	const colors = [
		['Ink / coffee', '#201515', 'Text, dark actions, moderate evidence'],
		['Primary / orange', '#FF4F00', 'Brand mark, CTA, focus, active state'],
		['Primary hover', '#D94300', 'Interactive emphasis'],
		['Canvas', '#FFFEFB', 'Page background'],
		['Canvas soft', '#F8F4F0', 'Cards and quiet bands'],
		['Primary soft', '#FFEEE3', 'Selected and drag states'],
		['Strong / OK', '#136F3A', 'Strong evidence only'],
		['Weak / warn', '#A65D00', 'Weak evidence and warnings'],
		['Tampered / bad', '#B3261E', 'Tamper and destructive error'],
		['Body', '#605D52', 'Secondary text and none grade']
	];

	const sampleConclusion: Conclusion = {
		provenance_class: 'tampered_after_signing',
		label: 'Signed content was modified after signing',
		evidence_grade: 'strong',
		decisive_signal: 'Content Credentials (C2PA)',
		notes: [
			'The embedded Content Credential’s hard binding no longer matches the bytes. This is not by itself evidence of AI; treat the manifest as stale.'
		]
	};

	let demoFiles = $state<File[]>([]);
</script>

<PageHead
	title="Design system"
	description="Internal live reference for Provenably’s founder-approved Zapier-adapted tokens, typography, accessibility and production Svelte components."
	noindex
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Internal reference</p>
		<h1>Design system</h1>
		<p class="lede">
			Reverse-engineered from <code>zapier/DESIGN.md</code>, adapted in <code>DESIGN.md</code>, and
			implemented as production Svelte components with custom CSS tokens. This page is the live
			contract—not a screenshot.
		</p>
	</header>

	<section class="brand-section" aria-labelledby="brand-title">
		<h2 id="brand-title">Primary brand mark</h2>
		<div class="grid grid--2">
			<div class="card card--canvas brand-lockup">
				<BrandMark size={64} />
				<div>
					<p class="brand-lockup__name">Provenably</p>
					<p class="small muted">
						Founder-supplied primary logo and brand icon. Its 64×64 geometry and alpha are preserved
						exactly, while its RGB color is palette-forced to the website primary for the header,
						footer and favicon.
					</p>
				</div>
			</div>
			<div class="card">
				<h3>Palette-forced, geometry preserved</h3>
				<div class="brand-sizes" aria-label="Provenably brand mark at interface sizes">
					<figure>
						<BrandMark size={16} decorative />
						<figcaption>16px</figcaption>
					</figure>
					<figure>
						<BrandMark size={24} decorative />
						<figcaption>24px</figcaption>
					</figure>
					<figure>
						<BrandMark size={32} decorative />
						<figcaption>32px</figcaption>
					</figure>
					<figure>
						<BrandMark size={48} decorative />
						<figcaption>48px</figcaption>
					</figure>
				</div>
				<ul>
					<li>
						Use the canonical <code>#FF4F00</code> palette version, never the native
						<code>#FD7E14</code> source.
					</li>
					<li>Preserve its transparent padding and pixel-identical alpha channel.</li>
					<li>Never trace, crop, stretch, mask, add a background or revive the old square.</li>
				</ul>
			</div>
		</div>
	</section>

	<section aria-labelledby="colors-title">
		<h2 id="colors-title">Colors</h2>
		<div class="grid grid--5 swatches">
			{#each colors as [name, hex, use] (hex)}
				<article class="swatch-card">
					<div class="swatch" style={`background:${hex}`} aria-hidden="true"></div>
					<h3>{name}</h3>
					<p class="mono">{hex}</p>
					<p class="small muted">{use}</p>
				</article>
			{/each}
		</div>
	</section>

	<section class="system-section" aria-labelledby="type-title">
		<h2 id="type-title">Typography</h2>
		<div class="grid grid--2">
			<div class="card card--canvas">
				<p class="eyebrow">Eyebrow · 14 uppercase</p>
				<p class="type-display">Display headlines use sentence case.</p>
				<p class="type-h2">Section headings stay compact and warm.</p>
				<h3>Card heading · Inter 700</h3>
				<p>
					Body copy is Inter Variable at 17–18px with a relaxed 1.58 line height for low-cost
					displays and long evidence reports.
				</p>
				<p class="small muted">
					Small support text is 14.4px. It never carries a grade by color alone.
				</p>
			</div>
			<div class="card">
				<h3>Data type</h3>
				<p>JetBrains Mono Variable is route-split and reserved for data:</p>
				<p class="mono data-sample">
					SHA-256 8aa1…f903<br />POST /v1/scans<br />ai_generated_declared
				</p>
				<p class="small muted">
					Degular’s role from the Zapier source is rendered with Inter 500–560; no licensed display
					font is bundled.
				</p>
			</div>
		</div>
	</section>

	<section class="system-section" aria-labelledby="controls-title">
		<h2 id="controls-title">Controls &amp; evidence states</h2>
		<div class="card card--canvas stack stack--large">
			<div class="actions" aria-label="Button examples">
				<button class="btn" type="button">Primary</button>
				<button class="btn btn--dark" type="button">Dark</button>
				<button class="btn btn--secondary" type="button">Secondary</button>
				<button class="btn btn--small" type="button">Small</button>
				<button class="btn" type="button" disabled>Disabled</button>
			</div>

			<div class="actions" aria-label="Evidence grade examples">
				<Tag tone="tag--strong">strong</Tag>
				<Tag tone="tag--moderate">moderate</Tag>
				<Tag tone="tag--weak">weak</Tag>
				<Tag>none</Tag>
				<Tag tone="tag--tampered">tampered</Tag>
				<Tag tone="tag--manual">not configured</Tag>
			</div>

			<p>
				Orange is reserved for actions and focus, never as an evidence grade. Moderate is coffee
				ink. The grade word is mandatory; status is never conveyed by color alone.
			</p>

			<div class="grid grid--3">
				<div class="field">
					<label for="ds-input">Text input</label><input
						id="ds-input"
						type="text"
						placeholder="Warm border, orange focus"
					/>
				</div>
				<div class="field">
					<label for="ds-select">Select</label>
					<select id="ds-select"
						><option>Generic master</option><option>Instagram</option><option>YouTube</option
						></select
					>
				</div>
				<div class="field">
					<span class="field-label">Progress</span>
					<div
						class="progress"
						role="progressbar"
						aria-label="Example progress"
						aria-valuenow="68"
						aria-valuemin="0"
						aria-valuemax="100"
					>
						<span style="transform:scaleX(.68)"></span>
					</div>
					<p class="field-hint">
						Transform-only motion; disabled under reduced-motion preferences.
					</p>
				</div>
			</div>
		</div>
	</section>

	<section class="system-section" aria-labelledby="components-title">
		<h2 id="components-title">Production components</h2>
		<div class="stack stack--large">
			<ConclusionCard
				conclusion={sampleConclusion}
				coverage={{ live: 9, manual: 5, errors: 0, manual_modules: [] }}
				durationMs={412}
			/>

			<div class="grid grid--2">
				<Notice title="Notice (warning)"
					><p>
						Honest-limits copy lives here. It explains what did not run and what a user must not
						infer.
					</p></Notice
				>
				<Notice tone="info" title="Notice (info)"
					><p>
						Jurisdiction and Layer-2 disclosures use the same quiet hairline frame; tone is carried
						by the icon and surface, never by a side stripe.
					</p></Notice
				>
			</div>

			<div class="grid grid--sidebar">
				<div>
					<h3>FileDrop</h3>
					<FileDrop
						id="design-file"
						label="Drop a file to inspect its provenance"
						description="Dashed warm gray on cream, orange drag-over, real keyboard-focusable input, paste support and size validation"
						bind:files={demoFiles}
					/>
					<p class="small muted">
						{demoFiles.length
							? `${demoFiles[0].name} selected locally. Nothing was uploaded.`
							: 'Nothing uploads from this reference example.'}
					</p>
				</div>
				<div>
					<h3>PlatformCard</h3>
					<PlatformCard
						preset={findPreset('instagram')}
						selected
						href={resolve('/presets?preset=instagram')}
					/>
				</div>
			</div>
		</div>
	</section>

	<section class="system-section" aria-labelledby="rules-title">
		<h2 id="rules-title">Layout, motion &amp; accessibility rules</h2>
		<div class="grid grid--3">
			<article class="card">
				<h3>Layout</h3>
				<ul>
					<li>1280px shell, 24px desktop gutters, 16px mobile gutters.</li>
					<li>Sections use a 48–80px responsive rhythm.</li>
					<li>Cards are flat cream or hairline outlined—no decorative shadows or side stripes.</li>
					<li>Buttons/cards use 12px radius; inputs/chips use 6px.</li>
				</ul>
			</article>
			<article class="card">
				<h3>Motion &amp; performance</h3>
				<ul>
					<li>Motion only communicates upload, scan or loading state.</li>
					<li>Animations use transform/opacity and respect reduced motion.</li>
					<li>Static pages ship no client router where interaction is unnecessary.</li>
					<li>Raw JSON renders only when a details section is opened.</li>
				</ul>
			</article>
			<article class="card">
				<h3>Accessibility</h3>
				<ul>
					<li>48px primary targets and a visible orange focus outline.</li>
					<li>Semantic landmarks, labels, table scopes and live regions.</li>
					<li>Grade and status always include words, not color alone.</li>
					<li>Forced-colors and print rules are part of the global CSS.</li>
				</ul>
			</article>
		</div>
	</section>
</div>

<style>
	.brand-section {
		margin-bottom: clamp(3rem, 7vw, 5rem);
	}

	.brand-lockup {
		align-items: center;
		display: flex;
		gap: 1.2rem;
	}

	.brand-lockup__name {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: clamp(2rem, 4vw, 2.7rem);
		font-weight: 650;
		letter-spacing: -0.04em;
		line-height: 1;
		margin-bottom: 0.55rem;
	}

	.brand-sizes {
		align-items: end;
		display: flex;
		flex-wrap: wrap;
		gap: 1.25rem;
		margin: 1.1rem 0 0.4rem;
	}

	.brand-sizes figure {
		align-items: center;
		display: grid;
		gap: 0.35rem;
		justify-items: center;
		margin: 0;
	}

	.brand-sizes figcaption {
		color: var(--body-mid);
		font-size: 0.78rem;
		line-height: 1;
	}

	.swatches {
		grid-template-columns: repeat(5, minmax(0, 1fr));
	}

	.swatch-card {
		background: var(--canvas);
		border: 1px solid var(--line);
		border-radius: var(--radius);
		padding: 0.8rem;
	}

	.swatch {
		border: 1px solid var(--line);
		border-radius: 9px;
		height: 64px;
		margin-bottom: 0.8rem;
	}

	.swatch-card h3,
	.swatch-card p {
		margin-bottom: 0.3rem;
	}

	.system-section {
		margin-top: clamp(3rem, 7vw, 5rem);
	}

	.type-display {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: clamp(2rem, 4vw, 3.2rem);
		font-weight: 540;
		letter-spacing: -0.04em;
		line-height: 1.03;
	}

	.type-h2 {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.9rem;
		font-weight: 540;
		letter-spacing: -0.03em;
		line-height: 1.12;
	}

	.data-sample {
		background: var(--canvas);
		border: 1px solid var(--line);
		border-radius: var(--radius);
		line-height: 1.7;
		padding: 1rem;
	}

	ul {
		margin: 0.6rem 0 0;
		padding-left: 1.2rem;
	}

	li + li {
		margin-top: 0.45rem;
	}

	@media (max-width: 980px) {
		.swatches {
			grid-template-columns: repeat(3, minmax(0, 1fr));
		}
	}

	@media (max-width: 620px) {
		.swatches {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
</style>
