<script lang="ts">
	import { resolve } from '$app/paths';
	import '#lib/mono-font.css';
	import { onMount, tick } from 'svelte';
	import {
		createFileScanWithProgress,
		downloadRemoval,
		errorMessage,
		getScan,
		MAX_UPLOAD_BYTES,
		removeLayer1
	} from '#lib/api.js';
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
	import type { RemovalResult, ScanDetail, Signal } from '#lib/types.js';

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
	let removing = $state(false);
	let removal = $state<RemovalResult | null>(null);
	let removalError = $state('');
	let downloading = $state(false);
	let resultPanel: HTMLElement | undefined = $state();

	let workflowController: AbortController | undefined;

	const selectedFile = $derived(files[0]);
	const report = $derived(scan?.report);
	const isWorking = $derived(loadingExisting || detecting || checkingScan || removing);
	const removableModality = $derived(
		['image', 'document', 'text', 'video'].includes(report?.modality ?? '')
	);
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
		if (signal.status === 'info') return 'Observed: see the full report';
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
		removal = null;
		removalError = '';
		statusMessage = `${nextFiles[0].name} selected. Detect runs before removal options can be applied.`;
	}

	async function detectSelectedFile(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (!selectedFile || isWorking) return;
		if (selectedFile.size > MAX_UPLOAD_BYTES) {
			pageError = 'That file is too large. The limit is 200 MB.';
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
		if (!scan || !attested || removing) return;
		removing = true;
		removal = null;
		removalError = '';
		statusMessage = 'Cleaning hidden info and checking the result…';
		workflowController = new AbortController();
		try {
			removal = await removeLayer1(scan.id, workflowController.signal);
			statusMessage = 'Cleaning finished.';
			await tick();
			resultPanel?.focus();
		} catch (error) {
			if (error instanceof DOMException && error.name === 'AbortError') {
				statusMessage = 'Cleaning was cancelled.';
			} else {
				removalError = errorMessage(error, 'We could not clean this file.');
				await tick();
				resultPanel?.focus();
			}
		} finally {
			removing = false;
			workflowController = undefined;
		}
	}

	function cleanedName(): string {
		const name = report?.file.filename ?? 'file';
		const dot = name.lastIndexOf('.');
		return dot > 0 ? `${name.slice(0, dot)}-clean${name.slice(dot)}` : `${name}-clean`;
	}

	async function downloadCleaned(): Promise<void> {
		if (!removal || downloading) return;
		downloading = true;
		removalError = '';
		try {
			const blob = await downloadRemoval(removal.output_download_url);
			const url = URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;
			link.download = cleanedName();
			document.body.append(link);
			link.click();
			link.remove();
			setTimeout(() => URL.revokeObjectURL(url), 10_000);
		} catch (error) {
			removalError = errorMessage(error, 'We could not download the cleaned file.');
		} finally {
			downloading = false;
		}
	}

	function friendlyField(field: string): string {
		const map: Record<string, string> = {
			'jpeg:C2PA (APP11)': 'Content Credentials (AI signature)',
			'png:C2PA (caBX)': 'Content Credentials (AI signature)',
			'webp:C2PA': 'Content Credentials (AI signature)',
			'heif:C2PA': 'Content Credentials (AI signature)',
			'gif:C2PA': 'Content Credentials (AI signature)',
			'tiff:C2PA': 'Content Credentials (AI signature)',
			'gif:comment': 'Hidden comment text',
			'tiff:GPS': 'Location (GPS)',
			'tiff:make': 'Camera or generator maker',
			'tiff:model': 'Camera or generator model',
			'tiff:software': 'Software or AI tool name',
			'tiff:artist': 'Creator name',
			'tiff:copyright': 'Copyright text',
			'tiff:datetime': 'Date and time',
			'tiff:description': 'Image description',
			'video:c2pa_box': 'Content Credentials (AI signature)',
			'video:container_metadata': 'Video details (encoder, dates, location)',
			'pdf:metadata': 'Document details (author, title, software)',
			'pdf:xmp': 'Hidden document metadata',
			'text:unicode_hygiene': 'Invisible text characters'
		};
		if (map[field]) return map[field];
		if (field.endsWith('EXIF') || field.endsWith('eXIf'))
			return 'Camera and location details (EXIF)';
		if (field.endsWith('XMP')) return 'Hidden editing details (XMP)';
		if (field.includes('IPTC')) return 'Caption and credit details (IPTC)';
		if (/png:(tEXt|iTXt|zTXt)/.test(field)) return 'Text notes stored in the image';
		if (field.startsWith('docx:')) return 'Document details (author, company, dates)';
		return field;
	}
</script>

<PageHead
	title="Remove: Strip footprints, prove it"
	description="Detect first, choose a Layer-1 removal policy and platform preset, then verify the output. Embedded Layer-2 watermarks are reported, never falsely claimed removed."
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Clean a file</p>
		<h1>Remove the hidden info. See proof.</h1>
		<p class="lede">
			We scan your file first, remove the hidden info that labels it as AI (signatures, camera and
			location details, author and software tags), then scan the cleaned file again so you can see
			what changed. Your picture, video or text itself is never re-encoded.
		</p>
	</header>

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
									<td><Tag>Layer 2 · stays</Tag></td>
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
									<td><Tag>Layer 2 · stays</Tag></td>
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
					title="No scan yet"
					description="Choose a file and scan it first. Cleaning always starts from what we actually found in your file."
				/>
			{/if}

			{#if removal || removalError || removing}
				<section
					class="card result-panel"
					aria-labelledby="result-title"
					tabindex="-1"
					bind:this={resultPanel}
				>
					<h2 id="result-title">3 · Result</h2>
					{#if removing}
						<p role="status">
							<span class="spinner" aria-hidden="true"></span> Cleaning your file and checking the result…
						</p>
					{:else if removalError}
						<Notice tone="error" title="We could not clean this file"><p>{removalError}</p></Notice>
					{:else if removal}
						{#if removal.verdict === 'layer1_clean'}
							<Notice tone="success" title="Hidden info removed">
								<p>
									We scanned the cleaned file again and found no remaining signature or metadata
									labels.
								</p>
							</Notice>
						{:else if removal.verdict === 'layer1_residue'}
							<Notice tone="warning" title="Some hidden info is still there">
								<p>
									After cleaning, the new scan still finds: {removal.after.layer1_present.join(
										', '
									)}. This file type may store it in a way we cannot remove yet.
								</p>
							</Notice>
						{:else}
							<Notice tone="info" title="Nothing to remove">
								<p>
									We did not find any signature or metadata labels in this file, so it was left as
									it was.
								</p>
							</Notice>
						{/if}

						<div class="actions form-actions">
							<button class="btn" type="button" onclick={downloadCleaned} disabled={downloading}>
								{downloading ? 'Preparing…' : 'Download cleaned file'}
								<Icon name="download" size={18} />
							</button>
						</div>

						<h3>What we removed</h3>
						{#if removal.fields_removed.length}
							<ul>
								{#each removal.fields_removed as field (field)}<li>
										{friendlyField(field)}
									</li>{/each}
							</ul>
						{:else}
							<p class="muted">Nothing.</p>
						{/if}

						<h3>What may still be there</h3>
						<p>{removal.layer2_disclaimer}</p>

						<details>
							<summary>Technical details</summary>
							<dl class="kv">
								<dt>Before</dt>
								<dd>{removal.before.label ?? removal.before.provenance_class ?? 'Unknown'}</dd>
								<dt>After</dt>
								<dd>{removal.after.label ?? removal.after.provenance_class ?? 'Unknown'}</dd>
								<dt>Original SHA-256</dt>
								<dd class="mono">{removal.input_sha256}</dd>
								<dt>Cleaned SHA-256</dt>
								<dd class="mono">{removal.output_sha256}</dd>
							</dl>
						</details>
					{/if}
				</section>
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
						<strong>I confirm:</strong> this is my file (or I have the right to change it). I understand
						cleaning hidden info does not remove invisible watermarks, and does not make the file “human-made”.
					</span>
				</label>
				<p class="field-hint" id="attestation-hint">
					We record that you accepted this. Cleaning only removes hidden metadata. Invisible marks
					may still remain.
				</p>

				<button
					class="btn btn--block"
					type="button"
					disabled={!report || !attested || isWorking || !removableModality}
					onclick={requestRemoval}
				>
					{removing ? 'Cleaning…' : 'Clean this file'}
					<Icon name="arrow-right" size={18} />
				</button>
				{#if !report}<p class="field-hint">
						Available after the scan finishes for a real file.
					</p>{/if}
				{#if report && !removableModality}<p class="field-hint">
						Cleaning is not available for {report.modality} files yet.
					</p>{/if}
				{#if report && removableModality && !attested}<p class="field-hint">
						Tick the box above to continue.
					</p>{/if}
			</div>

			<Notice tone="info" title="What “clean” means here">
				<p>
					We show exactly which hidden info was removed, what was kept, the file size before and
					after, and a fingerprint (hash) of both files. We never call a file “clean” if we are not
					sure. Invisible watermarks may still remain.
				</p>
			</Notice>
		</aside>
	</div>

	<section class="format-roadmap" aria-labelledby="format-roadmap-title">
		<div class="section-head">
			<p class="eyebrow">Supported formats</p>
			<h2 id="format-roadmap-title">What can be cleaned</h2>
			<p>
				Each format has its own cleaner that understands its file structure. Every cleaned file is
				scanned again before you download it.
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
						><th scope="row">Photos</th><td>JPG · PNG · WebP · HEIC · AVIF · GIF · TIFF</td><td
							>Content Credentials, EXIF (camera, GPS), XMP, IPTC, generator and software tags</td
						><td><Tag tone="tag--ok">Live</Tag> Pixels byte-identical, re-scanned</td></tr
					>
					<tr
						><th scope="row">Video</th><td>MP4 · MOV · WebM</td><td
							>Content Credentials and container details (encoder, dates, location)</td
						><td><Tag tone="tag--ok">Live</Tag> Stream copy, no re-encode, re-scanned</td></tr
					>
					<tr
						><th scope="row">Documents</th><td>PDF · DOCX · TXT</td><td
							>Author, title, software, hidden XMP, invisible text characters</td
						><td><Tag tone="tag--ok">Live</Tag> Opens cleanly, re-scanned</td></tr
					>
					<tr
						><th scope="row">Audio</th><td>WAV · MP3 · M4A · FLAC · OGG</td><td>Scanned only</td><td
							><Tag>Not cleaned</Tag> Platforms rarely label audio</td
						></tr
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
		margin-inline-end: 0.45rem;
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
		padding-inline-start: 1.2rem;
	}

	.attestation {
		border-top: 1px solid var(--line);
		padding-top: 1rem;
	}

	.result-panel {
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
