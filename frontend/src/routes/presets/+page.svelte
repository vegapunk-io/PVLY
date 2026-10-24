<script lang="ts">
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import { replaceState } from '$app/navigation';
	import { getPlatforms } from '#lib/api.js';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import PlatformCard from '#lib/components/PlatformCard.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import {
		findPreset,
		genericPreset,
		presetDefinitions,
		type PresetDefinition
	} from '#lib/data/presets.js';
	import { confidenceTone, titleCaseToken } from '#lib/format.js';
	import { getPreferences, setPreferences } from '#lib/settings.js';
	import type { PlatformRule } from '#lib/types.js';

	let selectedSlug = $state('instagram');
	let platformRules = $state<PlatformRule[]>([]);
	let rulesError = $state('');
	let removeLayer1 = $state(true);
	let verifyAfterExport = $state(true);
	let keepGenericMaster = $state(true);

	const selectedPreset = $derived(findPreset(selectedSlug));
	const selectedRule = $derived(platformRules.find((platform) => platform.slug === selectedSlug));

	function persistPreset(slug: string): void {
		const preferences = getPreferences();
		setPreferences({ ...preferences, preferredPreset: slug });
	}

	function selectPreset(preset: PresetDefinition): void {
		selectedSlug = preset.slug;
		persistPreset(preset.slug);
		replaceState(resolve(`/presets?preset=${preset.slug}`), {});
	}

	onMount(() => {
		const queryPreset = new URLSearchParams(window.location.search).get('preset');
		const preferences = getPreferences();
		const candidate = queryPreset ?? preferences.preferredPreset;
		if (candidate && findPreset(candidate).slug === candidate) selectedSlug = candidate;

		const controller = new AbortController();
		void getPlatforms(controller.signal)
			.then((result) => {
				platformRules = result.platforms;
			})
			.catch((error: unknown) => {
				if (!(error instanceof DOMException && error.name === 'AbortError')) {
					rulesError =
						'Live platform-rule details are unavailable; the bundled preset definitions remain shown.';
				}
			});
		return () => controller.abort();
	});
</script>

<PageHead
	title="Platform presets — Export ready to publish"
	description="Choose YouTube, Instagram, TikTok, LinkedIn, Pinterest, Reddit, X, Facebook or a generic master and carry its output, footprint and disclosure policy into Remove."
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Platform-ready</p>
		<h1>Export for the destination, not just the file type.</h1>
		<p class="lede">
			A preset combines format and size targets, the Layer-1 removal policy, a verification pass and
			the platform’s current label context. Select a destination to inspect exactly what will be
			carried into Remove.
		</p>
	</header>

	{#if rulesError}
		<div class="notice-gap"><Notice tone="info"><p>{rulesError}</p></Notice></div>
	{/if}

	<section aria-labelledby="preset-grid-title">
		<h2 class="visually-hidden" id="preset-grid-title">Choose a platform preset</h2>
		<div class="grid grid--4">
			{#each presetDefinitions as preset (preset.slug)}
				<PlatformCard {preset} selected={selectedSlug === preset.slug} onselect={selectPreset} />
			{/each}
		</div>
	</section>

	<div class="grid grid--sidebar preset-layout">
		<section class="card card--canvas" aria-labelledby="export-title" aria-live="polite">
			<p class="eyebrow">Export configuration</p>
			<h2 id="export-title">{selectedPreset.name}</h2>
			<dl class="kv">
				<dt>Media</dt>
				<dd>{selectedPreset.media}</dd>
				<dt>Formats</dt>
				<dd>{selectedPreset.formats}</dd>
				<dt>Output</dt>
				<dd>{selectedPreset.output}</dd>
				<dt>Label note</dt>
				<dd>{selectedPreset.labelNote}</dd>
				<dt>Creator duty</dt>
				<dd>{selectedPreset.creatorDuty}</dd>
			</dl>

			<fieldset class="export-options">
				<legend>Carry this policy into Remove</legend>
				<label class="check"
					><input type="checkbox" bind:checked={removeLayer1} />
					<span>Remove Layer-1 footprints (C2PA and metadata)</span></label
				>
				<label class="check"
					><input type="checkbox" bind:checked={verifyAfterExport} />
					<span>Verify after export with a fresh Detect pass</span></label
				>
				<label class="check"
					><input type="checkbox" bind:checked={keepGenericMaster} />
					<span>Also keep a generic verified-clean master</span></label
				>
			</fieldset>

			<div class="actions">
				<a class="btn" href={resolve('/remove')} onclick={() => persistPreset(selectedSlug)}>
					Open in Remove <Icon name="arrow-right" size={18} />
				</a>
				<a class="btn btn--secondary" href={resolve('/rules')}>Review disclosure rules</a>
			</div>
			<p class="small muted">
				Policy selected: {removeLayer1 ? 'Layer-1 removal on' : 'Layer-1 removal off'} · {verifyAfterExport
					? 'verification on'
					: 'verification off'} · {keepGenericMaster
					? 'generic master retained'
					: 'platform output only'}.
			</p>
		</section>

		<aside class="stack" aria-label="What the selected platform can see">
			<section class="card">
				<h2>What this platform can still see</h2>
				<p>{selectedPreset.platformBehavior}</p>
				<div class="table-wrap compact">
					<table>
						<caption class="visually-hidden">Signals after a verified Layer-1 preset export</caption
						>
						<tbody>
							<tr
								><th scope="row">C2PA at upload</th><td
									>{removeLayer1 ? 'Removed by preset' : 'Retained by your policy'}</td
								></tr
							>
							<tr
								><th scope="row">EXIF / GPS</th><td
									>{removeLayer1 ? 'Removed by preset' : 'Retained by your policy'}</td
								></tr
							>
							<tr
								><th scope="row">Embedded watermark</th><td
									>Not removable by metadata editing—disclosed in the verification report</td
								></tr
							>
							<tr
								><th scope="row">Your disclosure duty</th><td
									>Unchanged; use the destination’s label controls and the jurisdiction checklist</td
								></tr
							>
						</tbody>
					</table>
				</div>
			</section>

			{#if selectedRule}
				<section class="card card--canvas">
					<div class="row row--between row--start">
						<h2>Live rule record</h2>
						<Tag tone={confidenceTone(selectedRule.confidence)}
							>{selectedRule.confidence} confidence</Tag
						>
					</div>
					<dl class="kv">
						<dt>Platform label</dt>
						<dd>{selectedRule.label_text}</dd>
						<dt>Auto-label triggers</dt>
						<dd>{selectedRule.auto_label_triggers.map(titleCaseToken).join(', ')}</dd>
						<dt>On edits</dt>
						<dd>{selectedRule.label_on_edit}</dd>
						<dt>Removal policy</dt>
						<dd>{selectedRule.removal_policy}</dd>
						<dt>Monetization</dt>
						<dd>{selectedRule.monetization_impact}</dd>
						<dt>Last verified</dt>
						<dd>{selectedRule.last_verified}</dd>
					</dl>
					{#if selectedRule.notes}<p class="small muted">{selectedRule.notes}</p>{/if}
				</section>
			{/if}
		</aside>
	</div>

	<section class="generic-master card card--dark" aria-labelledby="generic-title">
		<div>
			<p class="eyebrow">No platform?</p>
			<h2 id="generic-title">Keep a generic verified master.</h2>
			<p>
				{genericPreset.output}. Use it for your own site, email, client delivery or archive, then
				derive platform variants without repeatedly processing the camera or generator original.
			</p>
		</div>
		<button class="btn" type="button" onclick={() => selectPreset(genericPreset)}
			>Use generic master</button
		>
	</section>
</div>

<style>
	.notice-gap {
		margin-bottom: 1.5rem;
	}

	.preset-layout {
		align-items: start;
		margin-top: 2rem;
	}

	.export-options {
		border-top: 1px solid var(--line);
		margin-top: 1.4rem;
		padding-top: 1.2rem;
	}

	.compact {
		margin-top: 1rem;
	}

	.compact table {
		min-width: 0;
	}

	.generic-master {
		align-items: center;
		display: grid;
		gap: 1.5rem;
		grid-template-columns: minmax(0, 1fr) auto;
		margin-top: 2rem;
	}

	.generic-master .eyebrow {
		color: var(--on-primary);
	}

	@media (max-width: 760px) {
		.generic-master {
			grid-template-columns: 1fr;
		}
	}
</style>
