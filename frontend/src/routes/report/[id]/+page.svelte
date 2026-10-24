<script lang="ts">
	import { resolve } from '$app/paths';
	import '#lib/mono-font.css';
	import { page } from '$app/state';
	import { ApiError, errorMessage, getScan } from '#lib/api.js';
	import ConclusionCard from '#lib/components/ConclusionCard.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import PlatformMark from '#lib/components/PlatformMark.svelte';
	import SignalCard from '#lib/components/SignalCard.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import {
		formatBytes,
		formatDuration,
		formatTimestamp,
		isManualStatus,
		safeJson,
		titleCaseToken
	} from '#lib/format.js';
	import { platformLabel } from '#lib/data/platform-labels.js';
	import type { PlatformPreview, ScanDetail, Signal } from '#lib/types.js';

	const scanId = $derived(page.params.id ?? '');

	let scan = $state<ScanDetail | null>(null);
	let loading = $state(true);
	let loadError = $state('');
	let errorStatus = $state(0);
	let pollAttempts = $state(0);
	let lastChecked = $state('');
	let previewVisible = $state(true);
	let copyMessage = $state('');
	let showFullJson = $state(false);
	let signalQuery = $state('');
	let signalFilter = $state('all');

	let requestController: AbortController | undefined;
	let pollTimer: ReturnType<typeof setTimeout> | undefined;
	let runToken = 0;

	const report = $derived(scan?.report);
	const isPending = $derived(Boolean(scan && !report && scan.status !== 'error'));
	const liveSignals = $derived(
		(report?.signals ?? []).filter((signal) => !isManualStatus(signal.status))
	);
	const manualSignals = $derived(
		(report?.signals ?? []).filter((signal) => isManualStatus(signal.status))
	);

	function matchesSignal(signal: Signal): boolean {
		if (signalFilter === 'detected' && signal.status !== 'detected') return false;
		if (signalFilter === 'attention' && !['inconclusive', 'error'].includes(signal.status))
			return false;
		if (signalFilter === 'absent-info' && !['absent', 'info', 'skipped'].includes(signal.status))
			return false;
		const query = signalQuery.trim().toLowerCase();
		if (!query) return true;
		return `${signal.name} ${signal.kind} ${signal.summary}`.toLowerCase().includes(query);
	}

	const visibleLiveSignals = $derived(liveSignals.filter(matchesSignal));
	const visibleManualSignals = $derived(
		signalFilter === 'all' || signalFilter === 'manual' ? manualSignals.filter(matchesSignal) : []
	);
	const fullJson = $derived(showFullJson && report ? safeJson(report) : '');

	function clearPoll(): void {
		if (pollTimer) clearTimeout(pollTimer);
		pollTimer = undefined;
	}

	function schedulePoll(token: number, id: string): void {
		clearPoll();
		if (pollAttempts >= 90) return;
		const delay = document.hidden
			? 5_000
			: pollAttempts < 8
				? 800
				: pollAttempts < 25
					? 1_600
					: 2_500;
		pollTimer = setTimeout(() => {
			if (token === runToken) void loadScan(token, id, false);
		}, delay);
	}

	async function loadScan(token: number, id: string, initial = true): Promise<void> {
		requestController?.abort();
		requestController = new AbortController();
		if (initial) loading = true;

		try {
			const nextScan = await getScan(id, requestController.signal);
			if (token !== runToken) return;
			scan = nextScan;
			loadError = '';
			errorStatus = 0;
			lastChecked = new Intl.DateTimeFormat('en-GB', {
				hour: '2-digit',
				minute: '2-digit',
				second: '2-digit'
			}).format(new Date());

			if (!nextScan.report && nextScan.status !== 'error') {
				pollAttempts += 1;
				schedulePoll(token, id);
			} else {
				clearPoll();
			}
		} catch (error) {
			if (token !== runToken || (error instanceof DOMException && error.name === 'AbortError'))
				return;
			errorStatus = error instanceof ApiError ? error.status : 0;
			loadError =
				errorStatus === 404
					? 'This scan does not exist in the current deployment, or its ID is incorrect.'
					: errorMessage(error, 'The report could not be loaded.');
		} finally {
			if (token === runToken) loading = false;
		}
	}

	$effect(() => {
		const id = scanId;
		runToken += 1;
		const token = runToken;
		scan = null;
		loadError = '';
		errorStatus = 0;
		pollAttempts = 0;
		previewVisible = true;
		showFullJson = false;
		signalQuery = '';
		signalFilter = 'all';
		clearPoll();
		if (id) void loadScan(token, id, true);

		return () => {
			if (runToken === token) runToken += 1;
			clearPoll();
			requestController?.abort();
		};
	});

	async function refreshNow(): Promise<void> {
		clearPoll();
		pollAttempts = 0;
		await loadScan(runToken, scanId, false);
	}

	async function copyHash(): Promise<void> {
		const hash = report?.file.sha256 ?? scan?.sha256;
		if (!hash) return;
		try {
			await navigator.clipboard.writeText(hash);
			copyMessage = 'SHA-256 copied.';
		} catch {
			copyMessage = 'Clipboard access was unavailable; select the hash to copy it manually.';
		}
	}

	function downloadReportJson(): void {
		if (!report) return;
		const blob = new Blob([safeJson(report)], { type: 'application/json' });
		const objectUrl = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = objectUrl;
		link.download = `provenably-${scanId}.json`;
		document.body.append(link);
		link.click();
		link.remove();
		setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
	}

	function likelyTone(value: string): string {
		return value === 'yes' ? 'tag--ok' : value === 'unknown' ? 'tag--warn' : '';
	}

	function previewSourceName(preview: PlatformPreview, url: string): string {
		return platformLabel(preview.slug).sources.find((source) => source.url === url)?.label ?? url;
	}

	const rulesHref = $derived.by(() => {
		if (!report) return resolve('/rules');
		const aiClasses = [
			'ai_generated_declared',
			'ai_assisted_declared',
			'ai_generated_watermark',
			'ai_generated_metadata'
		];
		const params = new URLSearchParams({
			from: scanId,
			ct: ['image', 'video', 'audio', 'text'].includes(report.modality) ? report.modality : 'image',
			ai: String(aiClasses.includes(report.conclusion.provenance_class)),
			c2pa: String(report.facts.c2pa_any === true)
		});
		return resolve(`/rules?${params}`);
	});
</script>

<PageHead
	title={scan?.filename ? `Report — ${scan.filename}` : 'Provenance report'}
	description="A private, evidence-graded Provenably provenance report with coverage and platform label preview."
	noindex
/>

<div class="shell page report-page">
	<p class="no-print"><a href={resolve('/scan')}>← New scan</a></p>

	{#if loading && !scan}
		<StateBlock
			kind="loading"
			title="Loading provenance report…"
			description="Checking the FastAPI scan status."
		/>
	{:else if loadError}
		<StateBlock
			kind="error"
			title={errorStatus === 404 ? 'Report not found' : 'The report could not be loaded'}
			description={loadError}
		>
			<button class="btn" type="button" onclick={refreshNow}>Try again</button>
			<a class="btn btn--secondary" href={resolve('/history')}>Open history</a>
		</StateBlock>
	{:else if scan}
		<header class="report-head">
			<div>
				<p class="eyebrow">Provenance report</p>
				<h1>{scan.filename ?? 'Untitled scan'}</h1>
				<p class="small muted mono report-id">
					{scan.id} · {scan.modality ?? 'unknown type'} · {scan.mime ?? 'unknown MIME'} · {formatBytes(
						scan.size
					)}
				</p>
				<p class="small muted">
					Created {formatTimestamp(scan.created_at)}{#if lastChecked}
						· checked {lastChecked}{/if}
				</p>
			</div>
			<div class="actions no-print">
				<Tag
					tone={scan.status === 'done'
						? 'tag--ok'
						: scan.status === 'error'
							? 'tag--bad'
							: 'tag--accent'}
				>
					{titleCaseToken(scan.status)}
				</Tag>
				{#if report}
					<button class="btn btn--secondary btn--small" type="button" onclick={downloadReportJson}>
						<Icon name="download" size={17} /> JSON
					</button>
					<button class="btn btn--secondary btn--small" type="button" onclick={() => window.print()}
						>Print</button
					>
				{:else}
					<button class="btn btn--secondary btn--small" type="button" onclick={refreshNow}
						>Refresh now</button
					>
				{/if}
				<a class="btn btn--dark btn--small" href={resolve('/scan')}>New scan</a>
			</div>
		</header>

		{#if scan.status === 'error'}
			<StateBlock
				kind="error"
				title="This scan failed"
				description={scan.error ??
					'The analyzer pipeline reported an error without a detailed message.'}
			>
				<a class="btn" href={resolve('/scan')}>Start another scan</a>
				<a class="btn btn--secondary" href={resolve('/api')}>Check API status</a>
			</StateBlock>
		{:else if isPending}
			<section class="card pending" aria-live="polite">
				<div class="row">
					<span class="spinner" aria-hidden="true"></span>
					<div>
						<h2>Analyzers are running</h2>
						<p>
							Status: <strong>{titleCaseToken(scan.status)}</strong>. This page checks automatically
							and slows down while hidden to save battery and data.
						</p>
					</div>
				</div>
				<div
					class="progress progress--indeterminate"
					role="progressbar"
					aria-label="Scan in progress"
				>
					<span></span>
				</div>
				<p class="small muted">
					{pollAttempts >= 90
						? 'Automatic checking stopped after an extended wait. Refresh manually to check again.'
						: 'Most files finish in seconds; video and large images can take longer.'}
				</p>
				<button class="btn btn--secondary btn--small" type="button" onclick={refreshNow}
					>Check now</button
				>
			</section>
		{:else if report}
			<ConclusionCard
				conclusion={report.conclusion}
				coverage={report.coverage}
				durationMs={report.duration_ms}
			/>

			<div class="grid grid--2 report-grid">
				<section aria-labelledby="file-title">
					<h2 id="file-title">File facts</h2>
					<dl class="kv">
						<dt>Filename</dt>
						<dd>{report.file.filename}</dd>
						<dt>MIME · modality</dt>
						<dd>{report.file.mime} · {report.modality}</dd>
						<dt>Size</dt>
						<dd>{formatBytes(report.file.size)} ({report.file.size.toLocaleString()} bytes)</dd>
						<dt>Completed</dt>
						<dd>{formatTimestamp(report.completed_at)} · {formatDuration(report.duration_ms)}</dd>
						<dt>Retention</dt>
						<dd>
							{report.hash_only
								? 'Hash-only — bytes deleted after analysis'
								: 'Bytes retained for the deployment TTL, then deleted; reports remain'}
						</dd>
						<dt>Trust sources</dt>
						<dd>
							{report.trust_sources.length ? report.trust_sources.join(', ') : 'None configured'}
						</dd>
					</dl>

					<div class="hash-box">
						<div class="row row--between">
							<strong>SHA-256</strong>
							<button
								class="btn btn--secondary btn--small no-print"
								type="button"
								onclick={copyHash}>Copy hash</button
							>
						</div>
						<code>{report.file.sha256}</code>
						{#if copyMessage}<p class="small" aria-live="polite">{copyMessage}</p>{/if}
					</div>

					{#if report.modality === 'image' && !report.hash_only && previewVisible}
						<figure class="preview">
							<img
								src={`/v1/scans/${encodeURIComponent(scanId)}/preview.jpg`}
								alt={`Preview of ${report.file.filename}`}
								loading="lazy"
								decoding="async"
								onerror={() => (previewVisible = false)}
							/>
							<figcaption class="small muted">
								Preview rendered from retained bytes; unavailable for hash-only scans.
							</figcaption>
						</figure>
					{/if}
				</section>

				<section aria-labelledby="coverage-title">
					<h2 id="coverage-title">Coverage — what actually ran</h2>
					<div class="coverage-metrics" role="list" aria-label="Report coverage summary">
						<div role="listitem">
							<strong>{report.coverage.live}</strong><span>live checks</span>
						</div>
						<div role="listitem">
							<strong>{report.coverage.manual}</strong><span>manual modules</span>
						</div>
						<div role="listitem"><strong>{report.coverage.errors}</strong><span>errors</span></div>
					</div>

					{#if report.coverage.manual_modules?.length}
						<div class="table-wrap compact-table">
							<table>
								<caption class="visually-hidden"
									>Manual integration modules and enabling steps</caption
								>
								<thead
									><tr><th scope="col">Manual module</th><th scope="col">Enabling step</th></tr
									></thead
								>
								<tbody>
									{#each report.coverage.manual_modules as module (module.name)}
										<tr
											><th scope="row">{module.name}</th><td
												>{module.how ?? titleCaseToken(module.status)}</td
											></tr
										>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
					<p class="small muted">
						Coverage prevents a “no signal” result from being over-read as proof of human origin.
					</p>
				</section>
			</div>

			<section class="signals" aria-labelledby="signals-title">
				<div class="row row--between row--start signals__head">
					<div>
						<h2 id="signals-title">Signals</h2>
						<p class="muted">
							{visibleLiveSignals.length} of {liveSignals.length} live signals shown. Raw payloads render
							only when opened.
						</p>
					</div>
					<div class="signal-controls no-print">
						<div>
							<label for="signal-search">Search signals</label>
							<input
								id="signal-search"
								type="search"
								bind:value={signalQuery}
								placeholder="C2PA, EXIF, watermark…"
							/>
						</div>
						<div>
							<label for="signal-filter">Show</label>
							<select id="signal-filter" bind:value={signalFilter}>
								<option value="all">All signals</option>
								<option value="detected">Detected</option>
								<option value="attention">Inconclusive or error</option>
								<option value="absent-info">Absent, info or skipped</option>
								<option value="manual">Manual only</option>
							</select>
						</div>
					</div>
				</div>

				{#if visibleLiveSignals.length}
					{#each visibleLiveSignals as signal (`${signal.kind}-${signal.name}`)}
						<SignalCard {signal} />
					{/each}
				{:else if signalFilter !== 'manual'}
					<StateBlock
						title="No live signals match"
						description="Change the search or filter to inspect other analyzer results."
					/>
				{/if}
			</section>

			{#if visibleManualSignals.length}
				<section class="signals" aria-labelledby="manual-title">
					<h2 id="manual-title">Not run in this deployment</h2>
					<p class="muted">
						These modules are wired into the report contract and state exactly what they would add.
						“Not configured” is never presented as “no watermark.”
					</p>
					{#each visibleManualSignals as signal (`manual-${signal.kind}-${signal.name}`)}
						<SignalCard {signal} />
					{/each}
				</section>
			{/if}

			<section class="platforms" aria-labelledby="platform-preview-title">
				<h2 id="platform-preview-title">Platform label preview</h2>
				<p class="muted">
					Derived from this file’s signals and Provenably’s platform rules, rechecked on 24 October
					2026. The viewer wording is shown separately from the file evidence because a platform can
					still act on creator declarations, native tools, classifiers or watermarks outside this
					scan.
				</p>
				<div class="table-wrap">
					<table class="platform-preview-table">
						<caption class="visually-hidden">Likely platform labelling for this scan</caption>
						<thead>
							<tr>
								<th scope="col">Platform</th>
								<th scope="col">Label likely?</th>
								<th scope="col">Viewer label</th>
								<th scope="col">Why this file</th>
								<th scope="col">Documented signals</th>
								<th scope="col">Rule evidence</th>
							</tr>
						</thead>
						<tbody>
							{#each report.platform_preview as preview (preview.slug)}
								<tr>
									<th scope="row">
										<span class="platform-cell">
											<PlatformMark slug={preview.slug} name={preview.platform} size={34} />
											<span class="platform-cell__copy"><span>{preview.platform}</span></span>
										</span>
									</th>
									<td><Tag tone={likelyTone(preview.likely_label)}>{preview.likely_label}</Tag></td>
									<td>
										<span class="platform-cell__label">{preview.label_text}</span><br />
										<span class="small muted">{preview.label_subtext}</span>
									</td>
									<td>{preview.reasons.join('; ')}</td>
									<td>
										<strong>{preview.metadata_signals.join(' · ')}</strong><br />
										<span class="small muted"><strong>Duty:</strong> {preview.creator_duty}</span>
									</td>
									<td>
										{preview.confidence}<br />
										<span class="small muted">verified {preview.last_verified}</span>
										{#if preview.sources.length}
											<span class="source-links">
												{#each preview.sources as source, index (source)}
													<!-- eslint-disable svelte/no-navigation-without-resolve -- External research source. -->
													<a
														href={source}
														target="_blank"
														rel="noreferrer"
														aria-label={previewSourceName(preview, source)}
														title={previewSourceName(preview, source)}
													>
														Source {index + 1}
														<Icon name="external" size={13} />
													</a>
													<!-- eslint-enable svelte/no-navigation-without-resolve -->
												{/each}
											</span>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				<p class="small muted trademark-note">
					Platform marks identify destinations only and belong to their owners. “No” means no
					documented file trigger was found in this scan—not that publication is risk-free.
				</p>
			</section>

			<section class="next-steps" aria-labelledby="next-title">
				<h2 id="next-title">Next step</h2>
				<div class="grid grid--3">
					<article class="card">
						<h3>Remove Layer-1 footprints</h3>
						<p>
							Carry this scan into the R0–R2 Detect → Remove → Verify workflow and review the
							eligible footprint policy.
						</p>
						<a
							class="btn btn--secondary"
							href={resolve(`/remove?scan=${encodeURIComponent(scanId)}`)}>Open removal flow</a
						>
					</article>
					<article class="card">
						<h3>Check disclosure</h3>
						<p>
							Run the jurisdiction checklist using this report’s content type and AI/C2PA facts as
							starting answers.
						</p>
						<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- rulesHref is constructed with resolve(). -->
						<a class="btn btn--secondary" href={rulesHref}>Run disclosure checklist</a>
					</article>
					<article class="card">
						<h3>Use the API record</h3>
						<p>
							Download the exact JSON report or open the FastAPI resource for automation and audit
							trails.
						</p>
						<div class="actions">
							<button class="btn btn--dark btn--small" type="button" onclick={downloadReportJson}
								>Download JSON</button
							>
							<!-- eslint-disable svelte/no-navigation-without-resolve -- FastAPI path outside the Svelte route manifest. -->
							<a
								class="text-link"
								href={`/v1/scans/${encodeURIComponent(scanId)}`}
								data-sveltekit-reload>API view <Icon name="external" size={16} /></a
							>
							<!-- eslint-enable svelte/no-navigation-without-resolve -->
						</div>
					</article>
				</div>
			</section>

			<details
				class="raw-report no-print"
				ontoggle={(event) => (showFullJson = (event.currentTarget as HTMLDetailsElement).open)}
			>
				<summary>Full report JSON</summary>
				<p class="small muted">
					The payload is serialized only when this section is opened, keeping large reports
					responsive on low-end devices.
				</p>
				{#if showFullJson}<pre>{fullJson}</pre>{/if}
			</details>
		{/if}
	{/if}
</div>

<style>
	.report-head {
		align-items: flex-start;
		display: flex;
		gap: 1.5rem;
		justify-content: space-between;
		margin-bottom: 1.6rem;
	}

	.report-head h1 {
		font-family: var(--font-mono);
		font-size: clamp(1.55rem, 4vw, 2.55rem);
		letter-spacing: -0.04em;
		overflow-wrap: anywhere;
	}

	.report-id {
		overflow-wrap: anywhere;
	}

	.pending h2 {
		font-size: 1.6rem;
	}

	.pending .progress {
		margin: 1.2rem 0;
	}

	.pending .spinner {
		height: 1.6rem;
		width: 1.6rem;
	}

	.report-grid {
		margin-top: 2rem;
	}

	.hash-box {
		background: var(--canvas-soft);
		border-radius: var(--radius);
		margin-top: 1.2rem;
		padding: 1rem;
	}

	.hash-box code {
		display: block;
		margin-top: 0.7rem;
	}

	.hash-box p {
		margin: 0.6rem 0 0;
	}

	.preview {
		margin: 1.2rem 0 0;
	}

	.preview img {
		border: 1px solid var(--line);
		border-radius: var(--radius);
		display: block;
		max-height: 360px;
		object-fit: contain;
		width: 100%;
	}

	.preview figcaption {
		margin-top: 0.5rem;
	}

	.coverage-metrics {
		display: grid;
		gap: 0.75rem;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		margin-bottom: 1rem;
	}

	.coverage-metrics > div {
		background: var(--canvas-soft);
		border-radius: var(--radius);
		padding: 1rem;
		text-align: center;
	}

	.coverage-metrics strong {
		display: block;
		font-family: var(--font-display);
		font-size: 2rem;
		line-height: 1;
	}

	.coverage-metrics span {
		color: var(--body-mid);
		font-size: 0.86rem;
	}

	.compact-table table {
		min-width: 0;
	}

	.signals,
	.platforms,
	.next-steps {
		margin-top: clamp(2.5rem, 6vw, 4rem);
	}

	.platform-preview-table {
		min-width: 1080px;
	}

	.trademark-note {
		margin-top: 0.8rem;
	}

	.signals__head {
		margin-bottom: 0.5rem;
	}

	.signal-controls {
		display: grid;
		gap: 0.8rem;
		grid-template-columns: minmax(220px, 1fr) minmax(190px, 0.7fr);
		min-width: min(560px, 100%);
	}

	.raw-report {
		margin-top: 2.5rem;
	}

	@media (max-width: 760px) {
		.report-head,
		.signals__head {
			display: grid;
		}

		.signal-controls {
			grid-template-columns: 1fr;
			min-width: 0;
		}
	}
</style>
