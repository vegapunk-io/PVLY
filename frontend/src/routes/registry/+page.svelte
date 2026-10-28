<script lang="ts">
	import { resolve } from '$app/paths';
	import '#lib/mono-font.css';
	import { onMount } from 'svelte';
	import { replaceState } from '$app/navigation';
	import { errorMessage, getRegistry } from '#lib/api.js';
	import Icon from '#lib/components/Icon.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import { confidenceTone, titleCaseToken } from '#lib/format.js';
	import type { RegistryEntry } from '#lib/types.js';

	const modalities = ['all', 'image', 'video', 'audio', 'text'];

	let entries = $state<RegistryEntry[]>([]);
	let registryNote = $state('');
	let lastReviewed = $state('');
	let loading = $state(true);
	let loadError = $state('');
	let query = $state('');
	let modality = $state('all');

	let loadController: AbortController | undefined;

	const filteredEntries = $derived(
		entries.filter((entry) => {
			if (modality !== 'all' && entry.modality !== modality) return false;
			const needle = query.trim().toLowerCase();
			if (!needle) return true;
			return [
				entry.slug,
				entry.vendor,
				entry.tool,
				entry.modality,
				entry.visible_mark,
				entry.invisible_watermark,
				entry.c2pa,
				entry.iptc,
				entry.public_detector
			]
				.join(' ')
				.toLowerCase()
				.includes(needle);
		})
	);

	async function loadRegistry(signal?: AbortSignal): Promise<void> {
		loading = true;
		try {
			const result = await getRegistry('', signal);
			entries = result.entries;
			registryNote = result.meta.note;
			lastReviewed = result.meta.last_reviewed;
			loadError = '';
		} catch (error) {
			if (!(error instanceof DOMException && error.name === 'AbortError')) {
				loadError = errorMessage(
					error,
					'We could not load the AI generator list. Please try again.'
				);
			}
		} finally {
			if (!signal?.aborted) loading = false;
		}
	}

	onMount(() => {
		const requested = new URLSearchParams(window.location.search).get('modality');
		if (requested && modalities.includes(requested)) modality = requested;
		loadController = new AbortController();
		void loadRegistry(loadController.signal);
		return () => loadController?.abort();
	});

	function selectModality(next: string): void {
		modality = next;
		replaceState(resolve(next === 'all' ? '/registry' : `/registry?modality=${next}`), {});
	}

	async function refresh(): Promise<void> {
		loadController?.abort();
		loadController = new AbortController();
		await loadRegistry(loadController.signal);
	}
</script>

<PageHead
	title="AI watermark & provenance registry"
	description="What image, video, audio and text generators embed: visible marks, invisible watermarks, Content Credentials, IPTC and public detectors, with confidence and verification dates."
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Generator registry</p>
		<h1>What does each generator actually leave behind?</h1>
		<p class="lede">
			Researched, confidence-graded and dated records for visible marks, invisible watermarks,
			Content Credentials, IPTC and public detectors. Public behavior only: this registry never
			documents evasion techniques.
		</p>
	</header>

	<section class="registry-controls" aria-label="Registry filters">
		<div class="field search-field">
			<label for="registry-search">Search generators and signals</label>
			<input
				id="registry-search"
				type="search"
				bind:value={query}
				placeholder="OpenAI, SynthID, C2PA, AudioSeal…"
			/>
		</div>

		<div>
			<span class="field-label" id="modality-label">Modality</span>
			<div class="segmented" role="group" aria-labelledby="modality-label">
				{#each modalities as item (item)}
					<button
						type="button"
						aria-pressed={modality === item}
						onclick={() => selectModality(item)}
					>
						{item === 'all' ? 'All' : titleCaseToken(item)}
					</button>
				{/each}
			</div>
		</div>

		<button class="btn btn--secondary" type="button" onclick={refresh} disabled={loading}>
			{loading ? 'Refreshing…' : 'Refresh'}
		</button>
	</section>

	<p class="small muted" aria-live="polite">
		{#if loading && !entries.length}
			Loading registry…
		{:else}
			{filteredEntries.length} of {entries.length} entries shown
			{#if lastReviewed}· last reviewed {lastReviewed}{/if}
			<!-- eslint-disable svelte/no-navigation-without-resolve -- FastAPI path outside the Svelte route manifest. -->
			·
			<a
				href={`/v1/registry${modality === 'all' ? '' : `?modality=${modality}`}`}
				data-sveltekit-reload>JSON API</a
			>
			<!-- eslint-enable svelte/no-navigation-without-resolve -->
		{/if}
	</p>

	{#if loadError}
		<StateBlock kind="error" title="Registry unavailable" description={loadError}>
			<button class="btn" type="button" onclick={refresh}>Retry</button>
			<a class="btn btn--secondary" href={resolve('/api')}>Check API status</a>
		</StateBlock>
	{:else if loading && !entries.length}
		<div class="skeleton-grid" aria-label="Loading registry entries">
			<div class="skeleton"></div>
			<div class="skeleton"></div>
			<div class="skeleton"></div>
		</div>
	{:else if filteredEntries.length}
		<div class="table-wrap">
			<table>
				<caption class="visually-hidden">AI generators and their provenance signals</caption>
				<thead>
					<tr>
						<th scope="col">Vendor / tool</th>
						<th scope="col">Type</th>
						<th scope="col">Visible mark</th>
						<th scope="col">Invisible watermark</th>
						<th scope="col">C2PA</th>
						<th scope="col">Public detector</th>
						<th scope="col">Confidence</th>
					</tr>
				</thead>
				<tbody>
					{#each filteredEntries as entry (entry.slug)}
						<tr>
							<th scope="row">
								<a href={resolve('/registry/[slug]', { slug: entry.slug })}
									><strong>{entry.vendor}</strong><br />{entry.tool}</a
								>
							</th>
							<td>{titleCaseToken(entry.modality)}</td>
							<td>{entry.visible_mark}</td>
							<td>{entry.invisible_watermark}</td>
							<td>{entry.c2pa}</td>
							<td>{entry.public_detector}</td>
							<td>
								<Tag tone={confidenceTone(entry.confidence)}>{entry.confidence}</Tag><br />
								<span class="small muted">verified {entry.last_verified}</span>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<StateBlock
			title="No registry entries match"
			description="Try a vendor, tool, watermark family or provenance technology."
		>
			<button
				class="btn btn--secondary"
				type="button"
				onclick={() => {
					query = '';
					selectModality('all');
				}}
			>
				Clear filters
			</button>
		</StateBlock>
	{/if}

	{#if registryNote}
		<p class="small muted registry-note">{registryNote}</p>
	{/if}

	<section class="card registry-cta">
		<div>
			<h2>Have a file from one of these tools?</h2>
			<p>
				Run Detect to see which of its documented signals are actually present in your copy after
				exports, edits and platform processing.
			</p>
		</div>
		<a class="btn" href={resolve('/scan')}>Scan a file <Icon name="arrow-right" size={18} /></a>
	</section>
</div>

<style>
	.registry-controls {
		align-items: end;
		display: grid;
		gap: 1rem;
		grid-template-columns: minmax(260px, 1fr) auto auto;
		margin-bottom: 0.8rem;
	}

	.registry-controls .field {
		margin: 0;
	}

	.segmented {
		background: var(--canvas-soft);
		border: 1px solid var(--line);
		border-radius: 12px;
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
		padding: 0.25rem;
	}

	.segmented button {
		background: transparent;
		border: 0;
		border-radius: 9px;
		color: var(--body);
		cursor: pointer;
		font-weight: var(--fw-semibold);
		min-height: 44px;
		padding: 0.55rem 0.85rem;
	}

	.segmented button:hover {
		background: var(--canvas);
		color: var(--ink);
	}

	.segmented button[aria-pressed='true'] {
		background: var(--ink);
		color: var(--on-primary);
	}

	.skeleton-grid {
		display: grid;
		gap: 0.8rem;
	}

	.registry-note {
		margin-top: 1rem;
	}

	.registry-cta {
		align-items: center;
		display: flex;
		gap: 1.5rem;
		justify-content: space-between;
		margin-top: 2rem;
	}

	.registry-cta h2 {
		font-size: 1.5rem;
	}

	@media (max-width: 900px) {
		.registry-controls {
			grid-template-columns: minmax(0, 1fr);
		}

		.registry-cta {
			align-items: stretch;
			flex-direction: column;
		}
	}
</style>
