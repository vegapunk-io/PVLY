<script lang="ts">
	import { resolve } from '$app/paths';
	import '#lib/mono-font.css';
	import { onMount } from 'svelte';
	import { errorMessage, listScans } from '#lib/api.js';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';
	import Tabs, { type TabItem } from '#lib/components/Tabs.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import {
		formatBytes,
		formatTimestamp,
		gradeTone,
		shortenHash,
		titleCaseToken
	} from '#lib/format.js';
	import type { ScanSummary } from '#lib/types.js';

	const tabs: TabItem[] = [
		{ id: 'scans', label: 'Scans' },
		{ id: 'removals', label: 'Removals' },
		{ id: 'batches', label: 'Batches & exports' }
	];

	let activeTab = $state('scans');
	let scans = $state<ScanSummary[]>([]);
	let loading = $state(true);
	let loadError = $state('');
	let query = $state('');
	let modalityFilter = $state('all');
	let statusFilter = $state('all');
	let gradeFilter = $state('all');

	let loadController: AbortController | undefined;

	const modalities = $derived([
		'all',
		...new Set(scans.map((scan) => scan.modality).filter(Boolean) as string[])
	]);
	const filteredScans = $derived(
		scans.filter((scan) => {
			if (modalityFilter !== 'all' && scan.modality !== modalityFilter) return false;
			if (statusFilter !== 'all' && scan.status !== statusFilter) return false;
			if (gradeFilter !== 'all' && scan.evidence_grade !== gradeFilter) return false;
			const needle = query.trim().toLowerCase();
			if (!needle) return true;
			return `${scan.filename ?? ''} ${scan.id} ${scan.conclusion ?? ''} ${scan.sha256 ?? ''}`
				.toLowerCase()
				.includes(needle);
		})
	);
	const doneCount = $derived(scans.filter((scan) => scan.status === 'done').length);
	const runningCount = $derived(
		scans.filter((scan) => scan.status === 'queued' || scan.status === 'running').length
	);
	const errorCount = $derived(scans.filter((scan) => scan.status === 'error').length);

	async function loadHistory(signal?: AbortSignal): Promise<void> {
		loading = true;
		try {
			const result = await listScans(100, signal);
			scans = result.scans;
			loadError = '';
		} catch (error) {
			if (!(error instanceof DOMException && error.name === 'AbortError')) {
				loadError = errorMessage(error, 'We could not load your history. Please try again.');
			}
		} finally {
			if (!signal?.aborted) loading = false;
		}
	}

	onMount(() => {
		loadController = new AbortController();
		void loadHistory(loadController.signal);
		return () => loadController?.abort();
	});

	async function refresh(): Promise<void> {
		loadController?.abort();
		loadController = new AbortController();
		await loadHistory(loadController.signal);
	}

	function resetFilters(): void {
		query = '';
		modalityFilter = 'all';
		statusFilter = 'all';
		gradeFilter = 'all';
	}
</script>

<PageHead
	title="History: Scans, removals and exports"
	description="Review recent Provenably Detect scans in this deployment, reopen reports, and track where removal and batch records will appear."
	noindex
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">History</p>
		<h1>Scans, removals, exports.</h1>
		<p class="lede">
			Reopen evidence instead of re-uploading. Reports retain findings and hashes after source bytes
			expire.
		</p>
	</header>

	<Notice tone="info" title="Deployment history until accounts ship">
		<p>
			History is not private to you yet. This page shows every scan on this site (or those visible
			to the API key in Settings). Accounts are coming; until then, do not scan private files on a
			shared demo site.
		</p>
	</Notice>

	<div class="history-tabs">
		<Tabs idPrefix="history" items={tabs} bind:active={activeTab} label="History record type" />
	</div>

	<div
		id="history-panel-scans"
		role="tabpanel"
		aria-labelledby="history-tab-scans"
		tabindex="0"
		hidden={activeTab !== 'scans'}
	>
		<section class="metrics" aria-label="Scan history summary">
			<div><strong>{scans.length}</strong><span>loaded scans</span></div>
			<div><strong>{doneCount}</strong><span>completed</span></div>
			<div><strong>{runningCount}</strong><span>queued / running</span></div>
			<div><strong>{errorCount}</strong><span>errors</span></div>
		</section>

		<form class="filters" aria-label="Filter scans" onsubmit={(event) => event.preventDefault()}>
			<div class="field search-field">
				<label for="history-search">Search</label>
				<input
					id="history-search"
					type="search"
					bind:value={query}
					placeholder="Filename, hash, conclusion or scan ID"
				/>
			</div>
			<div class="field">
				<label for="history-modality">Type</label>
				<select id="history-modality" bind:value={modalityFilter}>
					{#each modalities as modality (modality)}<option value={modality}
							>{modality === 'all' ? 'All types' : titleCaseToken(modality)}</option
						>{/each}
				</select>
			</div>
			<div class="field">
				<label for="history-status">Status</label>
				<select id="history-status" bind:value={statusFilter}>
					<option value="all">All statuses</option>
					<option value="done">Done</option>
					<option value="queued">Queued</option>
					<option value="running">Running</option>
					<option value="error">Error</option>
				</select>
			</div>
			<div class="field">
				<label for="history-grade">Evidence</label>
				<select id="history-grade" bind:value={gradeFilter}>
					<option value="all">All grades</option>
					<option value="strong">Strong</option>
					<option value="moderate">Moderate</option>
					<option value="weak">Weak</option>
					<option value="none">None</option>
				</select>
			</div>
			<div class="filter-actions">
				<button class="btn btn--secondary" type="button" onclick={refresh} disabled={loading}
					>{loading ? 'Refreshing…' : 'Refresh'}</button
				>
				<button class="btn btn--ghost" type="button" onclick={resetFilters}>Reset</button>
			</div>
		</form>

		<p class="small muted" aria-live="polite">
			{#if loading}Loading the latest history…{:else}{filteredScans.length} of {scans.length} scans shown.{/if}
		</p>

		{#if loadError}
			<StateBlock kind="error" title="We could not load your history" description={loadError}>
				<button class="btn" type="button" onclick={refresh}>Retry</button>
				<a class="btn btn--secondary" href={resolve('/api')}>Check deployment status</a>
			</StateBlock>
		{:else if loading && !scans.length}
			<StateBlock kind="loading" title="Loading scans…" description="Loading your recent scans." />
		{:else if filteredScans.length}
			<div class="table-wrap">
				<table>
					<caption class="visually-hidden">Filtered scan history</caption>
					<thead
						><tr
							><th scope="col">When</th><th scope="col">File</th><th scope="col">Conclusion</th><th
								scope="col">Evidence</th
							><th scope="col">Hash</th><th scope="col">Actions</th></tr
						></thead
					>
					<tbody>
						{#each filteredScans as scan (scan.id)}
							<tr>
								<td class="muted">{formatTimestamp(scan.created_at)}</td>
								<th scope="row">
									<span class="mono">{scan.filename ?? scan.id}</span><br />
									<span class="small muted"
										>{scan.modality ?? 'unknown'} · {formatBytes(scan.size)} · {titleCaseToken(
											scan.status
										)}</span
									>
								</th>
								<td class="mono small">{scan.conclusion ?? '–'}</td>
								<td
									>{#if scan.evidence_grade}<Tag tone={gradeTone(scan.evidence_grade)}
											>{scan.evidence_grade}</Tag
										>{:else}<span class="muted">–</span>{/if}</td
								>
								<td class="mono small">{shortenHash(scan.sha256, 7)}</td>
								<td>
									<div class="row compact-actions">
										<a
											class="btn btn--secondary btn--small"
											href={resolve('/report/[id]', { id: scan.id })}>Report</a
										>
										<a
											class="btn btn--ghost btn--small"
											href={`${resolve('/remove')}?scan=${encodeURIComponent(scan.id)}`}>Clean</a
										>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else if scans.length}
			<StateBlock
				title="No scans match these filters"
				description="Reset the filters or search by filename, scan ID, hash or conclusion."
			>
				<button class="btn btn--secondary" type="button" onclick={resetFilters}
					>Reset filters</button
				>
			</StateBlock>
		{:else}
			<StateBlock
				title="No scans in this deployment yet"
				description="Run a file, text, URL or demo scan and its report will appear here."
			>
				<a class="btn" href={resolve('/scan')}
					>Run your first scan <Icon name="arrow-right" size={18} /></a
				>
			</StateBlock>
		{/if}
	</div>

	<div
		id="history-panel-removals"
		role="tabpanel"
		aria-labelledby="history-tab-removals"
		tabindex="0"
		hidden={activeTab !== 'removals'}
	>
		<StateBlock
			title="Cleaning history is not listed here yet"
			description="Cleaning works now: open a scan and choose Clean, or start from the Remove page. Each result shows what was removed, the before and after scan, and a download link. A list of past cleanings will appear here in a later update."
		>
			<a class="btn" href={resolve('/remove')}>Clean a file</a>
		</StateBlock>
	</div>

	<div
		id="history-panel-batches"
		role="tabpanel"
		aria-labelledby="history-tab-batches"
		tabindex="0"
		hidden={activeTab !== 'batches'}
	>
		<StateBlock
			title="Batch records are session-local today"
			description="The Batch page scans many files and gives you a downloadable list of results. Each file also appears under Scans. A list of past batches will appear here in a later update."
		>
			<a class="btn" href={resolve('/batch')}>Start a batch</a>
			<a
				class="btn btn--secondary"
				href="#history-panel-scans"
				onclick={() => (activeTab = 'scans')}>View individual scans</a
			>
		</StateBlock>
	</div>
</div>

<style>
	.history-tabs {
		margin-top: 2rem;
	}

	.metrics {
		display: grid;
		gap: 0.8rem;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		margin-bottom: 1.2rem;
	}

	.metrics > div {
		background: var(--canvas-soft);
		border-radius: var(--radius);
		padding: 1rem;
	}

	.metrics strong {
		display: block;
		font-family: var(--font-display);
		font-size: 1.95rem;
		font-variant-numeric: lining-nums tabular-nums;
		font-weight: var(--fw-display-strong);
		letter-spacing: -0.034em;
		line-height: 1;
	}

	.metrics span {
		color: var(--body-mid);
		font-size: 0.88rem;
	}

	.filters {
		align-items: end;
		display: grid;
		gap: 0.8rem;
		grid-template-columns: minmax(240px, 1.4fr) repeat(3, minmax(150px, 0.7fr)) auto;
		margin-bottom: 0.7rem;
	}

	.filters .field {
		margin: 0;
	}

	.filter-actions {
		display: flex;
		gap: 0.35rem;
	}

	.compact-actions {
		flex-wrap: nowrap;
	}

	[role='tabpanel'][hidden] {
		display: none;
	}

	@media (max-width: 980px) {
		.filters {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.search-field {
			grid-column: 1 / -1;
		}
	}

	@media (max-width: 640px) {
		.metrics,
		.filters {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.filter-actions {
			grid-column: 1 / -1;
		}
	}
</style>
