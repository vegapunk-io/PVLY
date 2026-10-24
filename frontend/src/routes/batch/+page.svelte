<script lang="ts">
	import { resolve } from '$app/paths';
	import '#lib/mono-font.css';
	import { onMount } from 'svelte';
	import { createFileScanWithProgress, errorMessage, getScan } from '#lib/api.js';
	import FileDrop from '#lib/components/FileDrop.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import { genericPreset, presetDefinitions } from '#lib/data/presets.js';
	import { formatBytes, gradeTone, titleCaseToken } from '#lib/format.js';
	import type { EvidenceGrade } from '#lib/types.js';

	type QueueStatus = 'queued' | 'uploading' | 'running' | 'done' | 'error' | 'cancelled';

	interface QueueItem {
		key: string;
		file: File;
		status: QueueStatus;
		progress: number | null;
		scanId?: string;
		conclusion?: string;
		evidenceGrade?: EvidenceGrade;
		modality?: string;
		sha256?: string;
		error?: string;
	}

	const maxBatchFiles = 50;
	const allPresets = [genericPreset, ...presetDefinitions];

	let files = $state<File[]>([]);
	let queue = $state<QueueItem[]>([]);
	let selectedPreset = $state('generic');
	let runningBatch = $state(false);
	let statusMessage = $state('');

	let batchController: AbortController | undefined;

	const doneCount = $derived(queue.filter((item) => item.status === 'done').length);
	const errorCount = $derived(queue.filter((item) => item.status === 'error').length);
	const cancelledCount = $derived(queue.filter((item) => item.status === 'cancelled').length);
	const settledCount = $derived(doneCount + errorCount + cancelledCount);
	const totalBytes = $derived(queue.reduce((sum, item) => sum + item.file.size, 0));
	const currentItem = $derived(
		queue.find((item) => item.status === 'uploading' || item.status === 'running')
	);
	const overallFraction = $derived.by(() => {
		if (!queue.length) return 0;
		const currentFraction =
			currentItem?.status === 'uploading'
				? (currentItem.progress ?? 0) * 0.5
				: currentItem
					? 0.5
					: 0;
		return Math.min(1, (settledCount + currentFraction) / queue.length);
	});
	const canRetry = $derived(
		!runningBatch && queue.some((item) => ['error', 'cancelled', 'queued'].includes(item.status))
	);

	function rebuildQueue(nextFiles: File[]): void {
		if (runningBatch) return;
		queue = nextFiles.map((file) => ({
			key: `${file.name}-${file.size}-${file.lastModified}`,
			file,
			status: 'queued',
			progress: null
		}));
		statusMessage = nextFiles.length
			? `${nextFiles.length} file${nextFiles.length === 1 ? '' : 's'} queued for sequential Detect.`
			: '';
	}

	async function wait(delay: number, signal: AbortSignal): Promise<void> {
		await new Promise<void>((resolve, reject) => {
			const timeout = setTimeout(resolve, delay);
			signal.addEventListener(
				'abort',
				() => {
					clearTimeout(timeout);
					reject(new DOMException('The request was cancelled.', 'AbortError'));
				},
				{ once: true }
			);
		});
	}

	async function processItem(item: QueueItem, signal: AbortSignal): Promise<void> {
		item.status = 'uploading';
		item.progress = 0;
		item.error = undefined;
		statusMessage = `Uploading ${item.file.name} for Detect.`;

		const created = await createFileScanWithProgress(
			{ file: item.file, hashOnly: false },
			(fraction) => (item.progress = fraction),
			signal
		);
		item.scanId = created.id;
		item.status = 'running';
		item.progress = 1;
		statusMessage = `Analyzing ${item.file.name}.`;

		for (let attempt = 0; attempt < 90; attempt += 1) {
			const scan = await getScan(created.id, signal);
			item.modality = scan.modality ?? undefined;
			item.sha256 = scan.sha256 ?? undefined;
			if (scan.report) {
				item.status = 'done';
				item.conclusion = scan.report.conclusion.provenance_class;
				item.evidenceGrade = scan.report.conclusion.evidence_grade;
				item.modality = scan.report.modality;
				item.sha256 = scan.report.file.sha256;
				statusMessage = `${item.file.name} completed: ${scan.report.conclusion.label}.`;
				return;
			}
			if (scan.status === 'error') {
				throw new Error(scan.error ?? 'The analyzer pipeline failed for this file.');
			}
			await wait(attempt < 8 ? 800 : attempt < 25 ? 1_600 : 2_500, signal);
		}

		throw new Error(
			'Analysis exceeded the batch wait limit. Open the individual report to continue checking.'
		);
	}

	async function runBatch(retryOnly = false): Promise<void> {
		if (runningBatch || !queue.length) return;
		batchController = new AbortController();
		runningBatch = true;
		statusMessage = retryOnly
			? 'Retrying unfinished files one at a time…'
			: 'Running batch Detect one file at a time…';

		try {
			for (const item of queue) {
				if (batchController.signal.aborted) break;
				if (item.status === 'done') continue;
				if (retryOnly && item.status === 'queued') {
					// A first run and a retry intentionally share the same safe path.
				}
				try {
					await processItem(item, batchController.signal);
				} catch (error) {
					if (error instanceof DOMException && error.name === 'AbortError') {
						if (item.status === 'uploading' || item.status === 'running') item.status = 'cancelled';
						break;
					}
					item.status = 'error';
					item.error = errorMessage(error, 'This file could not be scanned.');
					statusMessage = `${item.file.name} failed. The batch will continue with the next file.`;
				}
			}
		} finally {
			runningBatch = false;
			batchController = undefined;
			if (queue.length && settledCount === queue.length) {
				statusMessage = `Batch finished: ${doneCount} done, ${errorCount} errors, ${cancelledCount} cancelled.`;
			}
		}
	}

	function cancelBatch(): void {
		batchController?.abort();
		statusMessage = 'Cancelling the current file. Completed reports remain available.';
	}

	function clearQueue(): void {
		if (runningBatch) return;
		files = [];
		queue = [];
		statusMessage = '';
	}

	function statusTone(status: QueueStatus): string {
		return status === 'done'
			? 'tag--ok'
			: status === 'error'
				? 'tag--bad'
				: status === 'uploading' || status === 'running'
					? 'tag--accent'
					: '';
	}

	function itemProgress(item: QueueItem): number {
		if (item.status === 'done') return 1;
		if (item.status === 'uploading') return (item.progress ?? 0) * 0.5;
		if (item.status === 'running') return 0.55;
		return 0;
	}

	function downloadManifest(): void {
		const manifest = {
			product: 'Provenably',
			mode: 'detect-only-client-orchestrated',
			preset_requested: selectedPreset,
			generated_at: new Date().toISOString(),
			files: queue.map((item) => ({
				filename: item.file.name,
				size: item.file.size,
				browser_mime: item.file.type || null,
				status: item.status,
				scan_id: item.scanId ?? null,
				report_path: item.scanId ? `/report/${item.scanId}` : null,
				modality: item.modality ?? null,
				sha256: item.sha256 ?? null,
				conclusion: item.conclusion ?? null,
				evidence_grade: item.evidenceGrade ?? null,
				error: item.error ?? null
			}))
		};
		const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
		const objectUrl = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = objectUrl;
		link.download = 'provenably-batch-manifest.json';
		document.body.append(link);
		link.click();
		link.remove();
		setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
	}

	onMount(() => () => batchController?.abort());
</script>

<PageHead
	title="Batch — Many files, one evidence pass"
	description="Queue up to 50 files for sequential, per-file Provenably Detect reports with isolated errors and a downloadable JSON manifest."
	noindex
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Batch Detect</p>
		<h1>Many files. One evidence pass.</h1>
		<p class="lede">
			Queue mixed media and documents for the same graded Detect report. Files run sequentially to
			protect low-end devices and the API; one file’s failure never fails the batch.
		</p>
	</header>

	<Notice tone="info" title="What is live in batch today">
		<p>
			This page orchestrates the existing live <code>POST /v1/scans</code> API in your browser. The
			native
			<code>/v1/batch</code> job, removal application and cleaned-file ZIP arrive in R3; the manifest
			below is a real client-generated index of the Detect reports created here.
		</p>
	</Notice>

	<div class="grid grid--sidebar batch-layout">
		<section aria-labelledby="batch-files-title">
			<h2 id="batch-files-title">Files</h2>
			<FileDrop
				id="batch-files"
				label="Drop up to 50 files"
				description="Images, video, audio, documents and text can be mixed · 200 MB per file · uploads run one at a time"
				bind:files
				onchange={rebuildQueue}
				multiple
				maxFiles={maxBatchFiles}
				disabled={runningBatch}
			/>

			{#if queue.length}
				<div class="batch-summary" aria-live="polite">
					<div class="row row--between">
						<strong>{settledCount} of {queue.length} settled</strong>
						<span class="small muted"
							>{formatBytes(totalBytes)} total · {doneCount} done · {errorCount} errors</span
						>
					</div>
					<div
						class="progress"
						role="progressbar"
						aria-label="Overall batch progress"
						aria-valuemin="0"
						aria-valuemax="100"
						aria-valuenow={Math.round(overallFraction * 100)}
					>
						<span style={`transform:scaleX(${overallFraction})`}></span>
					</div>
					{#if currentItem}<p class="small">
							Now: <strong>{currentItem.file.name}</strong> — {titleCaseToken(currentItem.status)}
						</p>{/if}
				</div>

				<div class="table-wrap queue-table">
					<table>
						<caption class="visually-hidden">Batch Detect queue and per-file results</caption>
						<thead
							><tr
								><th scope="col">File</th><th scope="col">Status</th><th scope="col"
									>Conclusion / evidence</th
								><th scope="col">Report</th></tr
							></thead
						>
						<tbody>
							{#each queue as item (item.key)}
								<tr>
									<th scope="row">
										<span class="mono">{item.file.name}</span><br />
										<span class="small muted"
											>{item.modality ?? item.file.type ?? 'unknown type'} · {formatBytes(
												item.file.size
											)}</span
										>
										{#if item.status === 'uploading' || item.status === 'running'}
											<div class="progress item-progress" aria-hidden="true">
												<span style={`transform:scaleX(${itemProgress(item)})`}></span>
											</div>
										{/if}
									</th>
									<td><Tag tone={statusTone(item.status)}>{titleCaseToken(item.status)}</Tag></td>
									<td>
										{#if item.error}<span class="error-copy">{item.error}</span>
										{:else if item.conclusion}<span class="mono small">{item.conclusion}</span
											>{#if item.evidenceGrade}<br /><Tag tone={gradeTone(item.evidenceGrade)}
													>{item.evidenceGrade}</Tag
												>{/if}
										{:else}<span class="muted">—</span>{/if}
									</td>
									<td
										>{#if item.scanId}<a href={resolve('/report/[id]', { id: item.scanId })}
												>report</a
											>{:else}<span class="muted">—</span>{/if}</td
									>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<div class="top-gap">
					<StateBlock
						title="No files yet"
						description="Drop files here to build a Detect queue. Nothing uploads until you choose Run batch."
					/>
				</div>
			{/if}
		</section>

		<aside class="batch-aside" aria-labelledby="batch-controls-title">
			<div class="card">
				<h2 id="batch-controls-title">Batch controls</h2>
				<div class="field">
					<label for="batch-mode">Mode</label>
					<select id="batch-mode" aria-describedby="batch-mode-hint">
						<option value="detect">Detect only — live</option>
						<option value="remove" disabled>Detect → Remove → Verify — R3</option>
					</select>
					<p class="field-hint" id="batch-mode-hint">
						Removal stays disabled until the native batch endpoint and formats are deployed.
					</p>
				</div>

				<div class="field">
					<label for="batch-preset">Requested platform preset</label>
					<select
						id="batch-preset"
						bind:value={selectedPreset}
						aria-describedby="batch-preset-hint"
					>
						{#each allPresets as preset (preset.slug)}<option value={preset.slug}
								>{preset.name}</option
							>{/each}
					</select>
					<p class="field-hint" id="batch-preset-hint">
						Stored in the Detect manifest now; applied to outputs when R3 lands.
					</p>
				</div>

				<div class="stack">
					<button
						class="btn btn--block"
						type="button"
						disabled={!queue.length || runningBatch}
						onclick={() => runBatch(false)}
					>
						{runningBatch ? 'Batch running…' : 'Run batch Detect'}
						<Icon name="arrow-right" size={18} />
					</button>
					{#if runningBatch}
						<button class="btn btn--secondary btn--block" type="button" onclick={cancelBatch}
							>Cancel current batch</button
						>
					{:else if canRetry && settledCount > 0}
						<button
							class="btn btn--secondary btn--block"
							type="button"
							onclick={() => runBatch(true)}>Retry unfinished files</button
						>
					{/if}
					{#if queue.length}
						<button
							class="btn btn--ghost btn--block"
							type="button"
							disabled={runningBatch}
							onclick={clearQueue}>Clear queue</button
						>
					{/if}
				</div>

				<p class="small" aria-live="polite">{statusMessage}</p>
				<p class="small muted">
					Sequential processing uses more wall-clock time but avoids saturating a phone, metered
					connection or single-process API.
				</p>
			</div>

			<div class="card card--canvas">
				<h2>Batch outputs</h2>
				<p>
					Each completed file links to its full graded report. Download a JSON manifest containing
					file sizes, scan IDs, hashes, conclusions, evidence grades and errors.
				</p>
				<button
					class="btn btn--dark btn--block"
					type="button"
					disabled={!queue.length || runningBatch}
					onclick={downloadManifest}
				>
					<Icon name="download" size={18} /> Download manifest.json
				</button>
				<p class="small muted">
					A ZIP is meaningful only when R3 produces cleaned outputs; Detect does not alter your
					originals.
				</p>
			</div>

			<Notice title="Failure isolation">
				<p>
					Unsupported and failed files are marked inline with the API reason. Completed files before
					and after that row remain usable.
				</p>
			</Notice>
		</aside>
	</div>
</div>

<style>
	.batch-layout {
		align-items: start;
		margin-top: 2rem;
	}

	.batch-aside {
		display: grid;
		gap: 1rem;
		position: sticky;
		top: calc(var(--header-height) + 1rem);
	}

	.batch-summary {
		background: var(--canvas-soft);
		border-radius: var(--radius);
		margin-top: 1.2rem;
		padding: 1rem;
	}

	.batch-summary .progress {
		margin-top: 0.75rem;
	}

	.batch-summary p {
		margin: 0.75rem 0 0;
	}

	.queue-table,
	.top-gap {
		margin-top: 1.2rem;
	}

	.item-progress {
		margin-top: 0.6rem;
		max-width: 240px;
	}

	.error-copy {
		color: var(--bad);
	}

	@media (max-width: 1023px) {
		.batch-aside {
			position: static;
		}
	}
</style>
