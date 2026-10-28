<script lang="ts">
	import { resolve } from '$app/paths';
	import Icon from '#lib/components/Icon.svelte';
	import PageHead from '#lib/components/PageHead.svelte';

	const steps = [
		{
			n: '1',
			title: 'Scan your file',
			body: 'Upload a photo, video, audio file or document. We check its hidden info: AI labels, camera data, GPS, watermarks and more. Nothing is changed.'
		},
		{
			n: '2',
			title: 'Clean it (optional)',
			body: 'Remove the hidden info that platforms use to label content as AI-generated. Your actual image or video is never re-encoded. Only the hidden info is stripped.'
		},
		{
			n: '3',
			title: 'Get proof',
			body: 'Download the cleaned file plus a report showing exactly what was removed and what may still remain. Keep it for your records.'
		},
		{
			n: '4',
			title: 'Share',
			body: 'Share your file anywhere. Platforms may still detect AI in other ways, and we never claim a file is “human-made”.'
		}
	];

	const faq = [
		{
			q: 'What gets removed?',
			a: 'Hidden info only: camera data, AI source tags, GPS, device details, and AI labels stored in metadata. The actual pixels, audio or text are never touched.'
		},
		{
			q: 'What stays?',
			a: 'Invisible watermarks embedded inside the content (like SynthID or AudioSeal) may still be present and detectable. We never claim a file is AI-free or human-made.'
		},
		{
			q: 'Does this make my file undetectable?',
			a: 'No. This tool cleans hidden metadata. It does not remove content-embedded watermarks and does not make AI content pass as human-made.'
		},
		{
			q: 'Is my file safe?',
			a: 'Files are deleted automatically after 24 hours (or immediately if you choose “hash only”). File contents are never logged.'
		},
		{
			q: 'What platforms do?',
			a: 'Each platform (Meta, YouTube, TikTok, LinkedIn, Pinterest, X and others) has its own AI label. See the Platform rules page for what each one checks.'
		},
		{
			q: 'What formats are supported?',
			a: 'Photos (JPG, PNG, WebP, HEIC, AVIF, GIF, TIFF), video (MP4, MOV, WebM), PDF, DOCX and text can all be scanned and cleaned. Audio (MP3, WAV and others) can be scanned but not cleaned.'
		}
	];
</script>

<PageHead
	title="How it works: Provenably"
	description="A simple guide to scanning, cleaning and getting proof for your files."
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Guide</p>
		<h1>How Provenably works</h1>
		<p class="lede">Four simple steps. No jargon.</p>
	</header>

	<section class="card-grid">
		{#each steps as step (step.n)}
			<article class="card">
				<span class="step-num">{step.n}</span>
				<h2>{step.title}</h2>
				<p>{step.body}</p>
			</article>
		{/each}
	</section>

	<section class="faq">
		<h2>Frequently asked questions</h2>
		{#each faq as item (item.q)}
			<details class="faq-item">
				<summary>{item.q}</summary>
				<p>{item.a}</p>
			</details>
		{/each}
	</section>

	<div class="actions">
		<a class="btn" href={resolve('/scan')}>Scan a file <Icon name="arrow-right" size={18} /></a>
		<a class="btn btn--secondary" href={resolve('/rules')}>Platform rules</a>
	</div>
</div>

<style>
	.card-grid {
		display: grid;
		gap: 1rem;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		margin: 1.5rem 0 2.5rem;
	}
	.step-num {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		background: var(--primary);
		color: var(--on-primary);
		font-weight: var(--fw-bold);
		margin-bottom: 0.6rem;
	}
	.faq {
		margin: 2rem 0;
	}
	.faq-item {
		border-bottom: 1px solid var(--line);
		padding: 0.9rem 0;
	}
	.faq-item summary {
		cursor: pointer;
		font-weight: var(--fw-medium);
	}
	.faq-item p {
		margin-top: 0.6rem;
		color: var(--body-mid);
	}
</style>
