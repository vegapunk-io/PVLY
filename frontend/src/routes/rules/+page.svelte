<script lang="ts">
	import { resolve } from '$app/paths';
	import '#lib/mono-font.css';
	import { onMount, tick } from 'svelte';
	import { checkDisclosure, errorMessage, getJurisdictions, getPlatforms } from '#lib/api.js';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import { confidenceTone, titleCaseToken } from '#lib/format.js';
	import type {
		DisclosureInput,
		DisclosureResult,
		JurisdictionRule,
		PlatformRule
	} from '#lib/types.js';

	let jurisdictions = $state<JurisdictionRule[]>([]);
	let platforms = $state<PlatformRule[]>([]);
	let loadingData = $state(true);
	let dataError = $state('');
	let checking = $state(false);
	let checkError = $state('');
	let result = $state<DisclosureResult | null>(null);
	let sourceScan = $state('');
	let resultRegion: HTMLDivElement | undefined = $state();

	let form = $state<DisclosureInput>({
		content_type: 'image',
		is_ai_generated: true,
		is_ai_edited: false,
		depicts_real_person: false,
		public_interest_text: false,
		human_reviewed: false,
		artistic: false,
		has_c2pa: false,
		has_visible_label: false,
		has_metadata_id: false,
		jurisdictions: []
	});

	let checkController: AbortController | undefined;

	const selectedCount = $derived(form.jurisdictions.length);

	async function runCheck(): Promise<void> {
		if (jurisdictions.length && !form.jurisdictions.length) {
			checkError = 'Select at least one jurisdiction.';
			return;
		}
		checkController?.abort();
		checkController = new AbortController();
		checking = true;
		checkError = '';

		try {
			result = await checkDisclosure(
				{ ...form, jurisdictions: [...form.jurisdictions] },
				checkController.signal
			);
			await tick();
			resultRegion?.focus();
		} catch (error) {
			if (!(error instanceof DOMException && error.name === 'AbortError')) {
				checkError = errorMessage(error, 'The disclosure check could not be completed.');
			}
		} finally {
			if (!checkController.signal.aborted) checking = false;
		}
	}

	async function loadData(signal: AbortSignal): Promise<void> {
		loadingData = true;
		const [jurisdictionsResult, platformsResult] = await Promise.allSettled([
			getJurisdictions(signal),
			getPlatforms(signal)
		]);
		if (signal.aborted) return;

		if (jurisdictionsResult.status === 'fulfilled') {
			jurisdictions = jurisdictionsResult.value.jurisdictions;
			if (!form.jurisdictions.length) {
				form.jurisdictions = jurisdictions.map((jurisdiction) => jurisdiction.slug);
			}
		}
		if (platformsResult.status === 'fulfilled') platforms = platformsResult.value.platforms;
		if (jurisdictionsResult.status === 'rejected' || platformsResult.status === 'rejected') {
			dataError =
				'Some rule reference data could not be loaded. The checklist endpoint can still be tried.';
		}
		loadingData = false;

		if (sourceScan) void runCheck();
	}

	onMount(() => {
		const params = new URLSearchParams(window.location.search);
		sourceScan = params.get('from') ?? '';
		const contentType = params.get('ct');
		if (contentType && ['image', 'video', 'audio', 'text'].includes(contentType)) {
			form.content_type = contentType as DisclosureInput['content_type'];
		}
		if (params.has('ai')) form.is_ai_generated = params.get('ai') === 'true';
		if (params.has('c2pa')) form.has_c2pa = params.get('c2pa') === 'true';

		const controller = new AbortController();
		void loadData(controller.signal);
		return () => {
			controller.abort();
			checkController?.abort();
		};
	});

	function selectAllJurisdictions(): void {
		form.jurisdictions = jurisdictions.map((jurisdiction) => jurisdiction.slug);
	}

	function clearJurisdictions(): void {
		form.jurisdictions = [];
	}

	function statusTone(status: string): string {
		return status === 'todo'
			? 'tag--warn'
			: status === 'done'
				? 'tag--ok'
				: status === 'exempt'
					? 'tag--accent'
					: '';
	}

	function statusLabel(status: string): string {
		return status === 'done' ? 'satisfied' : titleCaseToken(status);
	}
</script>

<PageHead
	title="Disclosure checklist & platform rules"
	description="Answer facts about content you plan to publish and receive dated, confidence-graded disclosure items by jurisdiction plus platform labelling rules."
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Rules</p>
		<h1>Disclosure checklist &amp; platform rules</h1>
		<p class="lede">
			Tell Provenably what the content is and what provenance it already carries. The rules engine
			returns open, satisfied, exempt and optional items per jurisdiction—dated and
			confidence-graded, never as legal advice.
		</p>
		{#if sourceScan}
			<p><Tag tone="tag--accent">started from scan {sourceScan}</Tag></p>
		{/if}
	</header>

	{#if dataError}
		<div class="notice-gap"><Notice tone="info"><p>{dataError}</p></Notice></div>
	{/if}

	<div class="grid grid--sidebar rules-layout">
		<form
			class="card rules-form"
			aria-labelledby="facts-title"
			onsubmit={(event) => {
				event.preventDefault();
				void runCheck();
			}}
		>
			<h2 id="facts-title">Your content</h2>

			<div class="field">
				<label for="rules-content-type">Content type</label>
				<select id="rules-content-type" bind:value={form.content_type} disabled={checking}>
					<option value="image">Image</option>
					<option value="video">Video</option>
					<option value="audio">Audio</option>
					<option value="text">Text</option>
				</select>
			</div>

			<fieldset>
				<legend>How it was made</legend>
				<label class="check"
					><input type="checkbox" bind:checked={form.is_ai_generated} disabled={checking} />
					<span>Fully AI-generated</span></label
				>
				<label class="check"
					><input type="checkbox" bind:checked={form.is_ai_edited} disabled={checking} />
					<span>AI-edited or composite (generative fill, face swap, voice conversion)</span></label
				>
				<label class="check"
					><input type="checkbox" bind:checked={form.depicts_real_person} disabled={checking} />
					<span>Depicts a real, identifiable person, place or event</span></label
				>
				<label class="check"
					><input type="checkbox" bind:checked={form.public_interest_text} disabled={checking} />
					<span>Text informs the public on a matter of public interest</span></label
				>
				<label class="check"
					><input type="checkbox" bind:checked={form.human_reviewed} disabled={checking} />
					<span>Human editorial review with responsibility</span></label
				>
				<label class="check"
					><input type="checkbox" bind:checked={form.artistic} disabled={checking} />
					<span>Evidently artistic or satirical work</span></label
				>
			</fieldset>

			<fieldset>
				<legend>What you already have</legend>
				<label class="check"
					><input type="checkbox" bind:checked={form.has_c2pa} disabled={checking} />
					<span>Content Credential (C2PA) attached</span></label
				>
				<label class="check"
					><input type="checkbox" bind:checked={form.has_visible_label} disabled={checking} />
					<span>Visible or audible label</span></label
				>
				<label class="check"
					><input type="checkbox" bind:checked={form.has_metadata_id} disabled={checking} />
					<span>Metadata identifier (IPTC DigitalSourceType or provider ID)</span></label
				>
			</fieldset>

			<fieldset>
				<legend>Jurisdictions <span class="muted">({selectedCount} selected)</span></legend>
				{#if loadingData && !jurisdictions.length}
					<p class="muted">
						<span class="spinner" aria-hidden="true"></span> Loading jurisdictions…
					</p>
				{:else if jurisdictions.length}
					<div class="row jurisdiction-actions">
						<button
							class="btn btn--secondary btn--small"
							type="button"
							onclick={selectAllJurisdictions}>Select all</button
						>
						<button class="btn btn--ghost btn--small" type="button" onclick={clearJurisdictions}
							>Clear</button
						>
					</div>
					<div class="jurisdiction-grid">
						{#each jurisdictions as jurisdiction (jurisdiction.slug)}
							<label class="check">
								<input
									type="checkbox"
									bind:group={form.jurisdictions}
									value={jurisdiction.slug}
									disabled={checking}
								/>
								<span>{jurisdiction.name}</span>
							</label>
						{/each}
					</div>
				{:else}
					<p class="muted">
						The jurisdiction catalogue is unavailable; the API will use its default set.
					</p>
				{/if}
			</fieldset>

			{#if checkError}<p class="field-error" role="alert">{checkError}</p>{/if}

			<button class="btn btn--block" type="submit" disabled={checking}>
				{checking ? 'Checking obligations…' : 'Check obligations'}
				<Icon name="arrow-right" size={18} />
			</button>
			<p class="field-hint">
				Uses <code>POST /v1/disclosure/check</code>. Facts are sent only to this deployment’s
				FastAPI service.
			</p>
		</form>

		<section class="results" aria-labelledby="results-title">
			<div bind:this={resultRegion} tabindex="-1" class="result-focus">
				<h2 id="results-title">Checklist result</h2>
			</div>

			{#if checking}
				<StateBlock
					kind="loading"
					title="Checking obligations…"
					description="Applying your facts to the selected jurisdiction rules."
				/>
			{:else if result}
				<div class="card card--canvas result-summary" aria-live="polite">
					<div class="row row--between row--start">
						<div>
							<p class="summary-count">
								{result.open_items} open item{result.open_items === 1 ? '' : 's'}
							</p>
							<p>
								For {result.content_type} · {result.synthetic
									? 'declared synthetic/AI-edited'
									: 'not declared synthetic'}
							</p>
						</div>
						<Tag tone={result.open_items ? 'tag--warn' : 'tag--ok'}
							>{result.open_items ? 'action needed' : 'no open items'}</Tag
						>
					</div>
					{#if result.recommendations.length}
						<h3>Recommended next steps</h3>
						<ul class="recommendations">
							{#each result.recommendations as recommendation (recommendation)}<li>
									{recommendation}
								</li>{/each}
						</ul>
					{/if}
				</div>

				<div class="stack result-list">
					{#each result.jurisdictions as jurisdiction (jurisdiction.slug)}
						<article class="card">
							<div class="row row--between row--start">
								<div>
									<h3>{jurisdiction.jurisdiction}</h3>
									<p class="small muted">
										Effective {jurisdiction.effective} · {jurisdiction.penalty}
									</p>
								</div>
								<Tag tone={confidenceTone(jurisdiction.confidence)}>{jurisdiction.confidence}</Tag>
							</div>

							{#if jurisdiction.items.length}
								<div class="table-wrap compact">
									<table>
										<caption class="visually-hidden"
											>Disclosure items for {jurisdiction.jurisdiction}</caption
										>
										<thead
											><tr><th scope="col">Status</th><th scope="col">Requirement</th></tr></thead
										>
										<tbody>
											{#each jurisdiction.items as item (item.key)}
												<tr>
													<td
														><Tag tone={statusTone(item.status)}>{statusLabel(item.status)}</Tag
														></td
													>
													<td>
														<code>{item.key}</code><br />
														{item.requirement}
														{#if item.note}<br /><span class="muted">{item.note}</span>{/if}
													</td>
												</tr>
											{/each}
										</tbody>
									</table>
								</div>
							{:else}
								<p class="muted">No obligation is triggered by these facts.</p>
							{/if}
							<p class="small muted">
								Verified {jurisdiction.last_verified} · status: {jurisdiction.status_note}
							</p>
						</article>
					{/each}
				</div>
				<p class="small muted disclaimer">{result.disclaimer}</p>
			{:else}
				<StateBlock
					title="Results will appear here"
					description="The checklist separates machine-readable marking, visible labels, metadata identifiers and exemptions instead of collapsing them into one legal-looking score."
				>
					<a class="btn btn--secondary" href={resolve('/scan?tab=demo')}>Start from a demo scan</a>
				</StateBlock>
			{/if}
		</section>
	</div>

	<section class="reference-section" aria-labelledby="jurisdictions-title">
		<div class="section-head">
			<p class="eyebrow">Reference</p>
			<h2 id="jurisdictions-title">Jurisdiction summaries</h2>
			<p>Open a jurisdiction to inspect the obligation catalogue behind the checklist.</p>
		</div>

		{#if loadingData && !jurisdictions.length}
			<div class="skeleton" aria-label="Loading jurisdiction summaries"></div>
		{:else}
			{#each jurisdictions as jurisdiction (jurisdiction.slug)}
				<details>
					<summary>
						<span><strong>{jurisdiction.name}</strong> · effective {jurisdiction.effective}</span>
						<Tag tone={confidenceTone(jurisdiction.confidence)}>{jurisdiction.confidence}</Tag>
					</summary>
					<p><strong>Status:</strong> {jurisdiction.status}</p>
					<p><strong>Penalty:</strong> {jurisdiction.penalty}</p>
					<div class="table-wrap compact">
						<table>
							<caption class="visually-hidden"
								>Obligations catalogued for {jurisdiction.name}</caption
							>
							<tbody>
								{#each Object.entries(jurisdiction.obligations) as [key, value] (key)}
									<tr><th scope="row" class="mono">{key}</th><td>{value}</td></tr>
								{/each}
							</tbody>
						</table>
					</div>
					{#if jurisdiction.notes}<p class="notice">{jurisdiction.notes}</p>{/if}
					<p class="small muted">
						Sources: {jurisdiction.sources.join('; ')} · verified {jurisdiction.last_verified}
					</p>
				</details>
			{/each}
		{/if}
	</section>

	<section class="reference-section" id="platforms" aria-labelledby="platform-rules-title">
		<div class="section-head">
			<p class="eyebrow">Platforms</p>
			<h2 id="platform-rules-title">Platform labelling at a glance</h2>
		</div>

		{#if loadingData && !platforms.length}
			<div class="skeleton" aria-label="Loading platform rules"></div>
		{:else if platforms.length}
			<div class="table-wrap">
				<table>
					<caption class="visually-hidden">Platform AI labelling rules</caption>
					<thead
						><tr
							><th scope="col">Platform</th><th scope="col">Label</th><th scope="col"
								>Auto-label triggers</th
							><th scope="col">On edits</th><th scope="col">Removal</th><th scope="col"
								>Monetization</th
							><th scope="col">Confidence</th></tr
						></thead
					>
					<tbody>
						{#each platforms as platform (platform.slug)}
							<tr>
								<th scope="row">{platform.name}</th>
								<td>{platform.label_text}</td>
								<td class="mono small">{platform.auto_label_triggers.join(', ')}</td>
								<td>{platform.label_on_edit}</td>
								<td>{platform.removal_policy}</td>
								<td>{platform.monetization_impact}</td>
								<td
									><Tag tone={confidenceTone(platform.confidence)}>{platform.confidence}</Tag><br
									/><span class="small muted">{platform.last_verified}</span></td
								>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<Notice tone="info"><p>Platform rules are unavailable from the API right now.</p></Notice>
		{/if}
	</section>
</div>

<style>
	.notice-gap {
		margin-bottom: 1.5rem;
	}

	.rules-layout {
		align-items: start;
	}

	.rules-form {
		position: sticky;
		top: calc(var(--header-height) + 1rem);
	}

	.rules-form fieldset {
		border-top: 1px solid var(--line);
		margin-top: 1.3rem;
		padding-top: 1.1rem;
	}

	.jurisdiction-actions {
		margin-bottom: 0.4rem;
	}

	.jurisdiction-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.results {
		min-width: 0;
	}

	.result-focus {
		outline-offset: 4px;
	}

	.result-summary {
		margin-bottom: 1rem;
	}

	.summary-count {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.8rem;
		font-weight: 560;
		letter-spacing: -0.03em;
		line-height: 1.1;
		margin-bottom: 0.35rem;
	}

	.recommendations {
		margin: 0.5rem 0 0;
		padding-left: 1.25rem;
	}

	.result-list {
		margin-top: 1rem;
	}

	.disclaimer {
		margin-top: 1rem;
	}

	.compact {
		margin: 1rem 0;
	}

	.compact table {
		min-width: 0;
	}

	.reference-section {
		margin-top: clamp(3rem, 7vw, 5rem);
	}

	.reference-section details summary {
		justify-content: space-between;
	}

	@media (max-width: 1023px) {
		.rules-form {
			position: static;
		}
	}

	@media (max-width: 620px) {
		.jurisdiction-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
