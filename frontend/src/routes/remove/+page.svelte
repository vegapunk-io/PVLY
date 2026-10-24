<script lang="ts">
	import { resolve } from '$app/paths';
	import '#lib/mono-font.css';
	import { onMount, tick } from 'svelte';
	import { createFileScanWithProgress, errorMessage, getScan, MAX_UPLOAD_BYTES } from '#lib/api.js';
	import FileDrop from '#lib/components/FileDrop.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import PlatformMark from '#lib/components/PlatformMark.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import { platformLabel } from '#lib/data/platform-labels.js';
	import { genericPreset, presetDefinitions } from '#lib/data/presets.js';
	import { formatBytes, gradeTone, shortenHash, titleCaseToken } from '#lib/format.js';
	import { getPreferences, setPreferences } from '#lib/settings.js';
	import type { ScanDetail, Signal } from '#lib/types.js';

	const allPresets = [genericPreset, ...presetDefinitions];

	let files = $state<File[]>([]);
	let scan = $state<ScanDetail | null>(null);
	let loadingExisting = $state(false);
	let detecting = $state(false);
	let checkingScan = $state(false);
	let uploadProgress = $state<number | null>(null);
	let statusMessage = $state('');
	let pageError = $state('');
	let selectedPreset = $state('generic');
	let keepIcc = $state(true);
	let bakeOrientation = $state(true);
	let reencode = $state(false);
	let attested = $state(false);
	let endpointNoticeVisible = $state(false);
	let endpointNotice: HTMLDivElement | undefined = $state();

	let workflowController: AbortController | undefined;

	const selectedFile = $derived(files[0]);
	const report = $derived(scan?.report);
	const isWorking = $derived(loadingExisting || detecting || checkingScan);
	const progressPercent = $derived(
		uploadProgress === null ? null : Math.round(uploadProgress * 100)
	);
	const preset = $derived(allPresets.find((item) => item.slug === selectedPreset) ?? genericPreset);
	const presetLabel = $derived(platformLabel(preset.slug));

	function signalFor(kind: string): Signal | undefined {
		return report?.signals.find((signal) => signal.kind === kind);
	}

	function finding(signal: Signal | undefined, presentText = 'Present'): string {
		if (!signal) return 'Not applicable';
		if (signal.status === 'detected') return presentText;
		if (signal.status === 'not_configured' || signal.status === 'not_installed')
			return 'Not checked in this deployment';
		if (signal.status === 'info') return 'Observed — inspect report';
		return titleCaseToken(signal.status);
	}

	const c2paSignal = $derived(signalFor('c2pa'));
	const metadataSignal = $derived(signalFor('metadata'));
	const openWatermarkSignal = $derived(signalFor('open_watermark'));
	const vendorSignal = $derived(signalFor('vendor_watermark'));
	const textSignal = $derived(signalFor('text_hygiene'));

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

	async function pollScan(id: string, signal: AbortSignal): Promise<ScanDetail> {
		checkingScan = true;
		try {
			for (let attempt = 0; attempt < 90; attempt += 1) {
				const nextScan = await getScan(id, signal);
				scan = nextScan;
				statusMessage = `Detect status: ${titleCaseToken(nextScan.status)}.`;
				if (nextScan.report || nextScan.status === 'error') return nextScan;
				await wait(attempt < 8 ? 800 : attempt < 25 ? 1_600 : 2_500, signal);
			}
			throw new Error(
				'Detect is taking longer than expected. Open the report to keep checking without holding this page open.'
			);
		} finally {
			checkingScan = false;
		}
	}

	onMount(() => {
		const preferences = getPreferences();
		selectedPreset = allPresets.some((item) => item.slug === preferences.preferredPreset)
			? preferences.preferredPreset
			: 'generic';

		const scanId = new URLSearchParams(window.location.search).get('scan');
		if (!scanId) return;

		workflowController = new AbortController();
		loadingExisting = true;
		void pollScan(scanId, workflowController.signal)
			.catch(async (error) => {
				if (!(error instanceof DOMException && error.name === 'AbortError')) {
					pageError = errorMessage(error, 'The selected scan could not be loaded.');
					await tick();
				}
			})
			.finally(() => {
				loadingExisting = false;
			});

		return () => workflowController?.abort();
	});

	$effect(() => {
		if (typeof window === 'undefined') return;
		const preferences = getPreferences();
		if (preferences.preferredPreset !== selectedPreset) {
			setPreferences({ ...preferences, preferredPreset: selectedPreset });
		}
	});

	function onFilesChange(nextFiles: File[]): void {
		if (!nextFiles.length) return;
		scan = null;
		pageError = '';
		endpointNoticeVisible = false;
		statusMessage = `${nextFiles[0].name} selected. Detect runs before removal options can be applied.`;
	}

	async function detectSelectedFile(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (!selectedFile || isWorking) return;
		if (selectedFile.size > MAX_UPLOAD_BYTES) {
			pageError = 'That file is larger than the 200 MB deployment limit.';
			return;
		}

		pageError = '';
		statusMessage = 'Uploading the file for Detect…';
		detecting = true;
		uploadProgress = 0;
		workflowController = new AbortController();

		try {
			const created = await createFileScanWithProgress(
				{ file: selectedFile, hashOnly: false },
				(fraction) => (uploadProgress = fraction),
				workflowController.signal
			);
			uploadProgress = 1;
			statusMessage = 'Upload complete. Waiting for the graded Detect report…';
			await pollScan(created.id, workflowController.signal);
		} catch (error) {
			if (error instanceof DOMException && error.name === 'AbortError') {
				statusMessage = 'Detect was cancelled before a report was ready.';
			} else {
				pageError = errorMessage(error, 'Detect could not be completed.');
			}
		} finally {
			detecting = false;
			uploadProgress = null;
			workflowController = undefined;
		}
	}

	function cancelWorkflow(): void {
		workflowController?.abort();
	}

	async function requestRemoval(): Promise<void> {
		endpointNoticeVisible = true;
		await tick();
		endpointNotice?.focus();
	}
</script>

<PageHead
	title="Remove — Strip footprints, prove it"
	description="Detect first, choose a Layer-1 removal policy and platform preset, then verify the output. Embedded Layer-2 watermarks are reported, never falsely claimed removed."
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Step 2 · Remove</p>
		<h1>Strip footprints. Prove it.</h1>
		<p class="lede">
			Nothing is removed blind. Provenably runs the live Detect report first, applies a
			lossless-first Layer-1 policy, then re-scans the output. Embedded watermarks are Layer-2 and
			stay explicitly reported.
		</p>
	</header>

	<Notice tone="info" title="R0 endpoint status">
		<p>
			Detect is live in this deployment. The production <code>POST /v1/remove</code> endpoint ships in
			roadmap R0–R2, so this completed workflow performs the real detection and readiness review but does
			not pretend to produce a cleaned file yet.
		</p>
	</Notice>

	<div class="grid grid--sidebar remove-layout">
		<div class="stack stack--large">
			<section class="card card--canvas" aria-labelledby="remove-step-title">
				<h2 id="remove-step-title">Workflow</h2>
				<ol class="steps">
					<li data-state={report ? 'done' : 'current'}>
						<strong>Detect</strong><br />
						<span
							>{report
								? 'Graded provenance report is ready.'
								: 'Run the live report before choosing a removal policy.'}</span
						>
					</li>
					<li data-state={report ? 'current' : 'pending'}>
						<strong>Choose what to remove</strong><br />
						<span>Preset, color profile, orientation, encoding and attestation.</span>
					</li>
					<li data-state="pending">
						<strong>Verify &amp; download</strong><br />
						<span>Before/after diff, hashes, residual Layer-2 note and audit JSON.</span>
					</li>
				</ol>
			</section>

			<section aria-labelledby="remove-file-title">
				<h2 id="remove-file-title">1 · Detect the source file</h2>
				<form onsubmit={detectSelectedFile}>
					<FileDrop
						id="remove-file"
						label="Drop a file to clean"
						description="Detect runs on the original bytes first · up to 200 MB · no client-side metadata guessing"
						bind:files
						onchange={onFilesChange}
						disabled={isWorking}
					/>

					{#if detecting}
						<div class="workflow-status" aria-live="polite">
							<div class="row row--between">
								<span><span class="spinner" aria-hidden="true"></span> Uploading for Detect…</span>
								<span>{progressPercent === null ? 'Working' : `${progressPercent}%`}</span>
							</div>
							<div
								class={progressPercent === null ? 'progress progress--indeterminate' : 'progress'}
								role="progressbar"
								aria-label="Detect upload progress"
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
					{:else if checkingScan || loadingExisting}
						<div class="workflow-status" aria-live="polite">
							<p>
								<span class="spinner" aria-hidden="true"></span> Waiting for analyzers to finish…
							</p>
							<div
								class="progress progress--indeterminate"
								role="progressbar"
								aria-label="Detect in progress"
							>
								<span></span>
							</div>
						</div>
					{/if}

					<div class="actions form-actions">
						<button class="btn" type="submit" disabled={!selectedFile || isWorking}>
							{detecting || checkingScan ? 'Detect running…' : 'Detect this file'}
							<Icon name="arrow-right" size={18} />
						</button>
						{#if isWorking}<button class="btn btn--secondary" type="button" onclick={cancelWorkflow}
								>Cancel</button
							>{/if}
						{#if scan}<a class="text-link" href={resolve('/report/[id]', { id: scan.id })}
								>Open full report <Icon name="arrow-right" size={17} /></a
							>{/if}
					</div>
				</form>

				<p class="small muted" aria-live="polite">{statusMessage}</p>
				{#if pageError}
					<div class="top-gap">
						<Notice tone="error" title="Detect did not finish"><p>{pageError}</p></Notice>
					</div>
				{/if}
			</section>

			{#if scan?.status === 'error'}
				<StateBlock
					kind="error"
					title="Detect failed for this file"
					description={scan.error ?? 'The scan pipeline returned an error.'}
				/>
			{:else if report && scan}
				<section aria-labelledby="detected-title">
					<div class="row row--between row--start">
						<div>
							<h2 id="detected-title">Detected in this file</h2>
							<p class="muted">
								{report.file.filename} · {formatBytes(report.file.size)} · SHA-256 {shortenHash(
									report.file.sha256,
									8
								)}
							</p>
						</div>
						<Tag tone={gradeTone(report.conclusion.evidence_grade)}
							>evidence: {report.conclusion.evidence_grade}</Tag
						>
					</div>

					<p><strong>{report.conclusion.label}</strong></p>

					<div class="table-wrap">
						<table>
							<caption class="visually-hidden">Detected removable and reported footprints</caption>
							<thead
								><tr
									><th scope="col">Footprint</th><th scope="col">Finding</th><th scope="col"
										>Layer</th
									><th scope="col">Planned action</th></tr
								></thead
							>
							<tbody>
								<tr>
									<th scope="row">C2PA manifest (JUMBF)</th>
									<td
										>{finding(c2paSignal)}<br /><span class="small muted"
											>{c2paSignal?.summary ?? ''}</span
										></td
									>
									<td><Tag tone="tag--accent">Layer 1</Tag></td>
									<td>Remove the manifest container without re-encoding by default.</td>
								</tr>
								<tr>
									<th scope="row">EXIF · XMP · IPTC · container tags</th>
									<td
										>{finding(metadataSignal, 'AI/generator metadata present')}<br /><span
											class="small muted">{metadataSignal?.summary ?? ''}</span
										></td
									>
									<td><Tag tone="tag--accent">Layer 1</Tag></td>
									<td>Strip according to the format policy; keep ICC only when selected.</td>
								</tr>
								<tr>
									<th scope="row">Open embedded watermark</th>
									<td
										>{finding(openWatermarkSignal)}<br /><span class="small muted"
											>{openWatermarkSignal?.summary ?? ''}</span
										></td
									>
									<td><Tag>Layer 2 — stays</Tag></td>
									<td
										>Report in verification; metadata removal does not alter embedded
										pixels/samples.</td
									>
								</tr>
								<tr>
									<th scope="row">Vendor embedded watermark</th>
									<td
										>{finding(vendorSignal)}<br /><span class="small muted"
											>{vendorSignal?.summary ?? ''}</span
										></td
									>
									<td><Tag>Layer 2 — stays</Tag></td>
									<td
										>Use a configured vendor connector for a definitive check; never infer absence.</td
									>
								</tr>
								{#if report.modality === 'text'}
									<tr>
										<th scope="row">Hidden Unicode characters</th>
										<td
											>{finding(textSignal)}<br /><span class="small muted"
												>{textSignal?.summary ?? ''}</span
											></td
										>
										<td><Tag tone="tag--accent">Text hygiene</Tag></td>
										<td
											>Use the live Text tools cleaner today; the unified Remove endpoint will
											include it in its policy.</td
										>
									</tr>
								{/if}
							</tbody>
						</table>
					</div>
					<p class="small muted">
						Coverage: {report.coverage.live} live · {report.coverage.manual} manual · {report
							.coverage.errors} errors. Inspect every supporting signal in the
						<a href={resolve('/report/[id]', { id: scan.id })}>full report</a>.
					</p>
				</section>
			{:else}
				<StateBlock
					title="No Detect report yet"
					description="Select a file and run Detect. Removal choices stay locked to evidence from the actual source—not a sample."
				/>
			{/if}
		</div>

		<aside class="remove-aside" aria-labelledby="options-title">
			<div class="card">
				<h2 id="options-title">2 · Removal options</h2>

				<div class="field">
					<label for="remove-preset">Export preset</label>
					<div class="preset-choice">
						<PlatformMark slug={preset.slug} name={preset.name} size={38} />
						<select id="remove-preset" bind:value={selectedPreset}>
							{#each allPresets as item (item.slug)}<option value={item.slug}>{item.name}</option
								>{/each}
						</select>
					</div>
					<p class="field-hint">
						{preset.output}. <strong>{presetLabel.labelDisplay}:</strong>
						{presetLabel.labelSubtext}
						{presetLabel.signalSummary}.
					</p>
				</div>

				<fieldset>
					<legend>Lossless-first policy</legend>
					<label class="check"
						><input type="checkbox" bind:checked={keepIcc} />
						<span>Keep ICC color profile (images)</span></label
					>
					<label class="check"
						><input type="checkbox" bind:checked={bakeOrientation} />
						<span>Bake EXIF orientation into pixels before stripping EXIF</span></label
					>
					<label class="check"
						><input type="checkbox" bind:checked={reencode} />
						<span
							>Re-encode when the preset requires it <span class="muted"
								>(off = byte-preserve media payload)</span
							></span
						></label
					>
				</fieldset>

				<div class="policy-summary" aria-live="polite">
					<strong>Current policy</strong>
					<ul>
						<li>{keepIcc ? 'Retain ICC profile' : 'Remove ICC profile'}</li>
						<li>
							{bakeOrientation
								? 'Normalize orientation before EXIF removal'
								: 'Do not alter orientation handling'}
						</li>
						<li>{reencode ? 'Preset re-encode allowed' : 'Lossless container edit only'}</li>
						<li>Verify output with the same Detect pipeline</li>
					</ul>
				</div>

				<label class="check attestation">
					<input
						type="checkbox"
						bind:checked={attested}
						required
						aria-describedby="attestation-hint"
					/>
					<span>
						<strong>Attestation (required):</strong> this is my content, or I have the right to modify
						it. I understand removing metadata does not remove any legal duty I have to disclose synthetic
						content.
					</span>
				</label>
				<p class="field-hint" id="attestation-hint">
					The signed attestation and policy will be stored with the future RemoveReport audit
					record.
				</p>

				<button
					class="btn btn--block"
					type="button"
					disabled={!report || !attested || isWorking}
					onclick={requestRemoval}
				>
					Remove footprints <Icon name="arrow-right" size={18} />
				</button>
				{#if !report}<p class="field-hint">
						Available after Detect completes for a real source file.
					</p>{/if}
				{#if report && !attested}<p class="field-hint">Confirm the attestation to continue.</p>{/if}

				{#if endpointNoticeVisible}
					<div class="endpoint-notice" bind:this={endpointNotice} tabindex="-1">
						<Notice tone="warning" title="The R0 removal endpoint is not deployed yet.">
							<p>
								Your Detect evidence, preset and policy are ready, but no cleaned file was created.
								The next backend milestone connects this exact contract to <code
									>POST /v1/remove</code
								> and returns a verified before/after report.
							</p>
						</Notice>
					</div>
				{/if}
			</div>

			<Notice tone="info" title="Verification contract">
				<p>
					A completed removal must show fields removed, fields retained by policy, byte-size change,
					lossless status, idempotence, input/output SHA-256 and residual embedded-watermark
					coverage. Anything less is not called “clean.”
				</p>
			</Notice>
		</aside>
	</div>

	<section class="format-roadmap" aria-labelledby="format-roadmap-title">
		<div class="section-head">
			<p class="eyebrow">Format rollout</p>
			<h2 id="format-roadmap-title">What Remove will support, in order</h2>
			<p>
				Each format gets a parser-level policy and fixture corpus. A generic metadata scrubber is
				not treated as proof across containers.
			</p>
		</div>
		<div class="table-wrap">
			<table>
				<caption class="visually-hidden">Removal format roadmap</caption>
				<thead
					><tr
						><th scope="col">Milestone</th><th scope="col">Formats</th><th scope="col"
							>Layer-1 scope</th
						><th scope="col">Verification</th></tr
					></thead
				>
				<tbody>
					<tr
						><th scope="row">R0</th><td>JPG · PNG · WebP · PDF · DOCX · TXT</td><td
							>C2PA/JUMBF, EXIF/XMP/IPTC, PNG text, document properties, hidden Unicode policy</td
						><td>Re-scan, byte diff, idempotence and document-open checks</td></tr
					>
					<tr
						><th scope="row">R1</th><td>WAV · MP3 · M4A · FLAC · OGG</td><td
							>RIFF chunks, ID3, MP4 atoms, Vorbis/FLAC comments</td
						><td>Re-scan plus sample-identical payload proof</td></tr
					>
					<tr
						><th scope="row">R2</th><td>MP4 · MOV · WebM</td><td
							>BMFF provenance boxes and container metadata</td
						><td>Re-scan, stream-copy proof and frame sampling</td></tr
					>
					<tr
						><th scope="row">R4</th><td>HEIC · AVIF · GIF · TIFF</td><td
							>Container-specific metadata and provenance boxes</td
						><td>Format fixture matrix before the preset is enabled</td></tr
					>
				</tbody>
			</table>
		</div>
	</section>
</div>

<style>
	.remove-layout {
		align-items: start;
		margin-top: 2rem;
	}

	.workflow-status {
		background: var(--canvas-soft);
		border-radius: var(--radius);
		margin-top: 1rem;
		padding: 1rem;
	}

	.workflow-status .progress {
		margin-top: 0.75rem;
	}

	.workflow-status p {
		margin: 0;
	}

	.workflow-status .spinner {
		margin-right: 0.45rem;
		vertical-align: -0.15rem;
	}

	.form-actions,
	.top-gap {
		margin-top: 1.2rem;
	}

	.remove-aside {
		display: grid;
		gap: 1rem;
		position: sticky;
		top: calc(var(--header-height) + 1rem);
	}

	.preset-choice {
		align-items: center;
		display: flex;
		gap: 0.7rem;
	}

	.preset-choice select {
		flex: 1 1 auto;
		min-width: 0;
	}

	.policy-summary {
		background: var(--canvas);
		border: 1px solid var(--line);
		border-radius: var(--radius);
		margin: 1.1rem 0;
		padding: 1rem;
	}

	.policy-summary ul {
		margin: 0.55rem 0 0;
		padding-left: 1.2rem;
	}

	.attestation {
		border-top: 1px solid var(--line);
		padding-top: 1rem;
	}

	.endpoint-notice {
		margin-top: 1rem;
		outline-offset: 4px;
	}

	.format-roadmap {
		margin-top: clamp(3rem, 7vw, 5rem);
	}

	@media (max-width: 1023px) {
		.remove-aside {
			position: static;
		}
	}
</style>
