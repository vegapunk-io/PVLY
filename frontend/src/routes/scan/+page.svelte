<script lang="ts">
	import { resolve } from '$app/paths';
	import '#lib/mono-font.css';
	import { onMount, tick } from 'svelte';
	import { goto, replaceState } from '$app/navigation';
	import {
		createDemoScan,
		createFileScanWithProgress,
		createTextScan,
		createUrlScan,
		errorMessage,
		getDemoFiles,
		listScans,
		MAX_UPLOAD_BYTES
	} from '#lib/api.js';
	import FileDrop from '#lib/components/FileDrop.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';
	import Tabs, { type TabItem } from '#lib/components/Tabs.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import { formatBytes, formatTimestamp, gradeTone, titleCaseToken } from '#lib/format.js';
	import { getPreferences } from '#lib/settings.js';
	import type { DemoFile, ScanSummary } from '#lib/types.js';

	const tabs: TabItem[] = [
		{ id: 'file', label: 'File' },
		{ id: 'text', label: 'Text' },
		{ id: 'url', label: 'URL' },
		{ id: 'demo', label: 'Demo files' }
	];

	let activeTab = $state('file');
	let files = $state<File[]>([]);
	let fileHashOnly = $state(false);
	let urlHashOnly = $state(false);
	let greenlistKey = $state('');
	let textValue = $state('');
	let urlValue = $state('');
	let busyAction = $state('');
	let uploadProgress = $state<number | null>(null);
	let formError = $state('');
	let statusMessage = $state('');
	let recentScans = $state<ScanSummary[]>([]);
	let recentError = $state('');
	let demoFiles = $state<DemoFile[]>([]);
	let demoError = $state('');
	let loadingSupportData = $state(true);
	let errorRegion: HTMLDivElement | undefined = $state();

	let submitController: AbortController | undefined;

	const selectedFile = $derived(files[0]);
	const isBusy = $derived(Boolean(busyAction));
	const progressPercent = $derived(
		uploadProgress === null ? null : Math.round(uploadProgress * 100)
	);

	async function showError(message: string): Promise<void> {
		formError = message;
		await tick();
		errorRegion?.focus();
	}

	function onTabChange(id: string): void {
		formError = '';
		statusMessage = '';
		replaceState(resolve(id === 'file' ? '/scan' : `/scan?tab=${id}`), {});
	}

	async function loadSupportData(signal: AbortSignal): Promise<void> {
		loadingSupportData = true;
		const [recentResult, demoResult] = await Promise.allSettled([
			listScans(8, signal),
			getDemoFiles(signal)
		]);
		if (signal.aborted) return;

		if (recentResult.status === 'fulfilled') {
			recentScans = recentResult.value.scans;
			recentError = '';
		} else {
			recentError = 'Recent scans are unavailable while the API cannot be reached.';
		}

		if (demoResult.status === 'fulfilled') {
			demoFiles = demoResult.value.files;
			demoError = '';
		} else {
			demoError =
				'The demo catalogue is unavailable. Generate the demo assets or check the API, then retry.';
		}
		loadingSupportData = false;
	}

	onMount(() => {
		const preferences = getPreferences();
		fileHashOnly = preferences.hashOnlyDefault;
		urlHashOnly = preferences.hashOnlyDefault;

		const requestedTab = new URLSearchParams(window.location.search).get('tab');
		if (requestedTab && tabs.some((tab) => tab.id === requestedTab)) activeTab = requestedTab;

		const controller = new AbortController();
		void loadSupportData(controller.signal);
		return () => {
			controller.abort();
			submitController?.abort();
		};
	});

	async function finishCreate(id: string): Promise<void> {
		statusMessage = 'Scan created. Opening the live report…';
		await goto(resolve('/report/[id]', { id }));
	}

	async function runSubmission(
		action: string,
		task: (signal: AbortSignal) => Promise<{ id: string }>
	): Promise<void> {
		if (isBusy) return;
		formError = '';
		statusMessage = '';
		busyAction = action;
		uploadProgress = action === 'file' ? 0 : null;
		submitController = new AbortController();

		try {
			const result = await task(submitController.signal);
			await finishCreate(result.id);
		} catch (error) {
			if (error instanceof DOMException && error.name === 'AbortError') {
				statusMessage = 'Submission cancelled. No report was opened.';
			} else {
				await showError(errorMessage(error, 'The scan could not be created.'));
			}
		} finally {
			busyAction = '';
			uploadProgress = null;
			submitController = undefined;
		}
	}

	async function submitFile(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (!selectedFile) {
			await showError('Choose or drop a file before starting the scan.');
			return;
		}
		if (selectedFile.size > MAX_UPLOAD_BYTES) {
			await showError('That file is larger than the 200 MB deployment limit.');
			return;
		}
		const file = selectedFile;
		await runSubmission('file', (signal) =>
			createFileScanWithProgress(
				{ file, hashOnly: fileHashOnly, greenlistKey },
				(fraction) => (uploadProgress = fraction),
				signal
			)
		);
	}

	async function submitText(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (!textValue.trim()) {
			await showError('Paste some text before starting the scan.');
			return;
		}
		await runSubmission('text', (signal) =>
			createTextScan({ text: textValue, greenlistKey }, signal)
		);
	}

	async function submitUrl(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		let parsed: URL;
		try {
			parsed = new URL(urlValue.trim());
		} catch {
			await showError('Enter a complete public http(s) URL.');
			return;
		}
		if (!['http:', 'https:'].includes(parsed.protocol)) {
			await showError('Only http and https URLs can be fetched.');
			return;
		}
		await runSubmission('url', (signal) =>
			createUrlScan({ url: parsed.toString(), hashOnly: urlHashOnly }, signal)
		);
	}

	async function submitDemo(event: SubmitEvent, name: string): Promise<void> {
		event.preventDefault();
		await runSubmission(`demo:${name}`, (signal) => createDemoScan(name, signal));
	}

	function cancelSubmission(): void {
		submitController?.abort();
	}

	async function refreshSupportData(): Promise<void> {
		const controller = new AbortController();
		await loadSupportData(controller.signal);
	}
</script>

<PageHead
	title="Scan — Detect AI provenance"
	description="Scan a file, text, public URL or bundled demo fixture for Content Credentials, AI metadata, watermarks and other graded provenance signals."
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Step 1 · Detect</p>
		<h1>Detect AI provenance</h1>
		<p class="lede">
			One graded Provenance Report per input—Content Credentials, metadata forensics, open watermark
			decoders, forensic context and text checks. A report describes signals and evidence; it is not
			a verdict on authorship.
		</p>
	</header>

	<div class="grid grid--sidebar scan-layout">
		<section aria-labelledby="scan-form-title">
			<h2 class="visually-hidden" id="scan-form-title">Create a scan</h2>
			<Tabs
				idPrefix="scan"
				items={tabs}
				bind:active={activeTab}
				label="Scan input type"
				onchange={onTabChange}
			/>

			{#if formError}
				<div class="form-alert" bind:this={errorRegion} tabindex="-1">
					<Notice tone="error" title="The scan was not created."><p>{formError}</p></Notice>
				</div>
			{/if}

			<p class="visually-hidden" aria-live="polite">{statusMessage}</p>

			<div
				id="scan-panel-file"
				role="tabpanel"
				aria-labelledby="scan-tab-file"
				tabindex="0"
				hidden={activeTab !== 'file'}
			>
				<form method="post" action="/v1/scans" enctype="multipart/form-data" onsubmit={submitFile}>
					<FileDrop
						id="scan-file"
						name="file"
						label="Drop a file to inspect its provenance"
						description="Image, video, audio, PDF, DOCX or text · up to 200 MB · the file is analyzed by FastAPI, never in this page"
						bind:files
						disabled={isBusy}
						required
					/>

					<label class="check">
						<input
							type="checkbox"
							name="hash_only"
							value="true"
							bind:checked={fileHashOnly}
							disabled={isBusy}
						/>
						<span
							><strong>Hash-only</strong> — delete uploaded bytes immediately after analysis, keeping
							only SHA-256 and the report.</span
						>
					</label>

					<div class="field">
						<label for="scan-file-key">Green-list key <span class="muted">(optional)</span></label>
						<input
							id="scan-file-key"
							name="greenlist_key"
							type="text"
							bind:value={greenlistKey}
							placeholder="demo-key"
							autocomplete="off"
							disabled={isBusy}
							aria-describedby="scan-file-key-hint"
						/>
						<p class="field-hint" id="scan-file-key-hint">
							Only needed for the keyed text-watermark check demonstrated in the Lab.
						</p>
					</div>

					{#if busyAction === 'file'}
						<div class="upload-status" aria-live="polite">
							<div class="row row--between">
								<span
									><span class="spinner" aria-hidden="true"></span> Uploading and creating the scan…</span
								>
								<span>{progressPercent === null ? 'Working' : `${progressPercent}%`}</span>
							</div>
							<div
								class={progressPercent === null ? 'progress progress--indeterminate' : 'progress'}
								role="progressbar"
								aria-label="File upload progress"
								aria-valuemin="0"
								aria-valuemax="100"
								aria-valuenow={progressPercent ?? undefined}
							>
								<span
									style={progressPercent === null
										? undefined
										: `transform:scaleX(${uploadProgress})`}
								></span>
							</div>
						</div>
					{/if}

					<div class="actions form-actions">
						<button class="btn" type="submit" disabled={isBusy || !selectedFile}>
							{busyAction === 'file' ? 'Creating scan…' : 'Scan file'}
							<Icon name="arrow-right" size={18} />
						</button>
						{#if busyAction === 'file'}
							<button class="btn btn--secondary" type="button" onclick={cancelSubmission}
								>Cancel upload</button
							>
						{/if}
						<span class="small muted">Retained uploads are deleted after 24 hours by default.</span>
					</div>
				</form>
			</div>

			<div
				id="scan-panel-text"
				role="tabpanel"
				aria-labelledby="scan-tab-text"
				tabindex="0"
				hidden={activeTab !== 'text'}
			>
				<form method="post" action="/v1/scans" enctype="multipart/form-data" onsubmit={submitText}>
					<div class="field">
						<label for="scan-text">Paste text</label>
						<textarea
							id="scan-text"
							name="text"
							bind:value={textValue}
							placeholder="Paste text to scan for hidden characters and provenance signals…"
							required
							disabled={isBusy}
							aria-describedby="scan-text-count"></textarea>
						<p class="field-hint" id="scan-text-count">
							{textValue.length.toLocaleString()} characters · hidden-character, stylometry and optional
							green-list checks
						</p>
					</div>

					<div class="field">
						<label for="scan-text-key">Green-list key <span class="muted">(optional)</span></label>
						<input
							id="scan-text-key"
							name="greenlist_key"
							type="text"
							bind:value={greenlistKey}
							placeholder="demo-key"
							autocomplete="off"
							disabled={isBusy}
						/>
					</div>

					<div class="actions form-actions">
						<button class="btn" type="submit" disabled={isBusy || !textValue.trim()}>
							{busyAction === 'text' ? 'Creating scan…' : 'Scan text'}
							<Icon name="arrow-right" size={18} />
						</button>
						{#if busyAction === 'text'}<button
								class="btn btn--secondary"
								type="button"
								onclick={cancelSubmission}>Cancel</button
							>{/if}
					</div>
				</form>
			</div>

			<div
				id="scan-panel-url"
				role="tabpanel"
				aria-labelledby="scan-tab-url"
				tabindex="0"
				hidden={activeTab !== 'url'}
			>
				<form method="post" action="/v1/scans" enctype="multipart/form-data" onsubmit={submitUrl}>
					<div class="field">
						<label for="scan-url">Public file URL</label>
						<input
							id="scan-url"
							name="url"
							type="url"
							bind:value={urlValue}
							placeholder="https://example.com/image.jpg"
							required
							disabled={isBusy}
							inputmode="url"
							autocomplete="url"
							aria-describedby="scan-url-hint"
						/>
						<p class="field-hint" id="scan-url-hint">
							http(s) only · public hosts only · SSRF-guarded and size-capped by the API.
						</p>
					</div>

					<label class="check">
						<input
							type="checkbox"
							name="hash_only"
							value="true"
							bind:checked={urlHashOnly}
							disabled={isBusy}
						/>
						<span
							><strong>Hash-only</strong> — delete fetched bytes immediately after analysis.</span
						>
					</label>

					<div class="actions form-actions">
						<button class="btn" type="submit" disabled={isBusy || !urlValue.trim()}>
							{busyAction === 'url' ? 'Fetching…' : 'Fetch & scan'}
							<Icon name="arrow-right" size={18} />
						</button>
						{#if busyAction === 'url'}<button
								class="btn btn--secondary"
								type="button"
								onclick={cancelSubmission}>Cancel</button
							>{/if}
					</div>
				</form>
			</div>

			<div
				id="scan-panel-demo"
				role="tabpanel"
				aria-labelledby="scan-tab-demo"
				tabindex="0"
				hidden={activeTab !== 'demo'}
			>
				<p>
					No file handy? The bundled corpus covers valid, tampered, watermarked, stripped and
					metadata-only fixtures across image, video, audio and text.
				</p>

				{#if demoError}
					<Notice tone="error" title="Demo files unavailable">
						<p>{demoError}</p>
						<p>
							<button
								class="btn btn--secondary btn--small"
								type="button"
								onclick={refreshSupportData}>Retry</button
							>
						</p>
					</Notice>
				{:else if loadingSupportData && !demoFiles.length}
					<StateBlock
						kind="loading"
						title="Loading demo files…"
						description="Reading the FastAPI demo catalogue."
					/>
				{:else if demoFiles.length}
					<div class="table-wrap">
						<table>
							<caption class="visually-hidden">Bundled demo files available to scan</caption>
							<thead
								><tr
									><th scope="col">File</th><th scope="col">Demonstrates</th><th scope="col"
										>Size</th
									><th scope="col">Action</th></tr
								></thead
							>
							<tbody>
								{#each demoFiles as demo (demo.name)}
									<tr>
										<th scope="row">
											<span class="mono">{demo.name}</span><br />
											<Tag>{demo.modality}</Tag>
										</th>
										<td>{demo.desc}</td>
										<td class="num">{formatBytes(demo.size)}</td>
										<td>
											<form
												method="post"
												action={`/v1/scans/demo/${encodeURIComponent(demo.name)}`}
												onsubmit={(event) => submitDemo(event, demo.name)}
											>
												<button class="btn btn--small" type="submit" disabled={isBusy}>
													{busyAction === `demo:${demo.name}` ? 'Starting…' : 'Scan'}
												</button>
											</form>
											<!-- eslint-disable svelte/no-navigation-without-resolve -- FastAPI path outside the Svelte route manifest. -->
											<a
												class="small"
												href={`/demo-assets/${encodeURIComponent(demo.name)}`}
												data-sveltekit-reload>download fixture</a
											>
											<!-- eslint-enable svelte/no-navigation-without-resolve -->
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<StateBlock
						title="No demo files found"
						description="Run tools/make_demo_assets.py in the backend deployment to generate the corpus."
					/>
				{/if}
			</div>
		</section>

		<aside class="scan-aside" aria-label="What Provenably checks and its limits">
			<div class="card">
				<h2>What gets checked</h2>
				<dl class="check-list">
					<div>
						<dt>Content Credentials</dt>
						<dd>Signature, trust, source type, actions, ingredients and tamper state.</dd>
					</div>
					<div>
						<dt>Metadata</dt>
						<dd>EXIF, XMP/IPTC, PNG text, generator strings and container tags.</dd>
					</div>
					<div>
						<dt>Watermarks</dt>
						<dd>Open DWT-DCT decoding plus honestly labelled vendor-connector slots.</dd>
					</div>
					<div>
						<dt>Forensic context</dt>
						<dd>Container, image, audio and frame observations—never the sole verdict.</dd>
					</div>
					<div>
						<dt>Text</dt>
						<dd>Hidden characters, stylometric features and optional keyed watermark test.</dd>
					</div>
					<div>
						<dt>Platform preview</dt>
						<dd>Likely label triggers derived from the completed report.</dd>
					</div>
				</dl>
			</div>

			<Notice title="Honest limits">
				<p>
					Every report shows <strong>coverage</strong>: what ran, what needs manual integration and
					what errored. Absence of provenance is <strong>not</strong> evidence of human origin—metadata
					is routinely stripped by screenshots, messaging apps and social platforms.
				</p>
				<p><a href={resolve('/api')}>Inspect this deployment’s live coverage</a></p>
			</Notice>
		</aside>
	</div>

	<section class="recent" aria-labelledby="recent-title">
		<div class="row row--between">
			<div>
				<p class="eyebrow">Deployment activity</p>
				<h2 id="recent-title">Recent scans</h2>
			</div>
			<div class="actions">
				<button
					class="btn btn--secondary btn--small"
					type="button"
					onclick={refreshSupportData}
					disabled={loadingSupportData}
				>
					{loadingSupportData ? 'Refreshing…' : 'Refresh'}
				</button>
				<a class="btn btn--dark btn--small" href={resolve('/history')}>Open history</a>
			</div>
		</div>

		{#if recentError}
			<Notice tone="info"><p>{recentError}</p></Notice>
		{:else if loadingSupportData && !recentScans.length}
			<div class="skeleton" aria-label="Loading recent scans"></div>
		{:else if recentScans.length}
			<div class="table-wrap">
				<table>
					<caption class="visually-hidden">Most recent scans in this deployment</caption>
					<thead
						><tr
							><th scope="col">When</th><th scope="col">File</th><th scope="col">Type</th><th
								scope="col">Conclusion</th
							><th scope="col">Evidence</th><th scope="col">Report</th></tr
						></thead
					>
					<tbody>
						{#each recentScans as scan (scan.id)}
							<tr>
								<td class="muted">{formatTimestamp(scan.created_at)}</td>
								<th scope="row" class="mono">{scan.filename ?? scan.id}</th>
								<td>{scan.modality ?? '—'}</td>
								<td class="mono small">{scan.conclusion ?? titleCaseToken(scan.status)}</td>
								<td
									>{#if scan.evidence_grade}<Tag tone={gradeTone(scan.evidence_grade)}
											>{scan.evidence_grade}</Tag
										>{:else}<span class="muted">—</span>{/if}</td
								>
								<td><a href={resolve('/report/[id]', { id: scan.id })}>report</a></td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<StateBlock
				title="No scans yet"
				description="Completed and in-progress scans for this deployment will appear here."
			/>
		{/if}
	</section>
</div>

<style>
	.scan-layout {
		align-items: start;
	}

	.form-alert {
		margin-bottom: 1rem;
		outline-offset: 4px;
	}

	.form-actions {
		margin-top: 1.25rem;
	}

	.upload-status {
		background: var(--canvas-soft);
		border-radius: var(--radius);
		margin-top: 1.1rem;
		padding: 1rem;
	}

	.upload-status .progress {
		margin-top: 0.75rem;
	}

	.upload-status .spinner {
		margin-right: 0.45rem;
		vertical-align: -0.15rem;
	}

	.scan-aside {
		display: grid;
		gap: 1rem;
	}

	.check-list {
		display: grid;
		gap: 0.9rem;
		margin: 0;
	}

	.check-list div {
		border-bottom: 1px solid var(--line);
		padding-bottom: 0.85rem;
	}

	.check-list div:last-child {
		border-bottom: 0;
		padding-bottom: 0;
	}

	.check-list dt {
		color: var(--ink);
		font-weight: 700;
	}

	.check-list dd {
		margin: 0.2rem 0 0;
	}

	.recent {
		margin-top: clamp(3rem, 7vw, 5rem);
	}

	.recent .table-wrap,
	.recent .skeleton {
		margin-top: 1.2rem;
	}

	[role='tabpanel'][hidden] {
		display: none;
	}
</style>
