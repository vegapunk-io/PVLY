<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { ApiError, errorMessage, getRegistryEntry } from '#lib/api.js';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import { confidenceTone, titleCaseToken } from '#lib/format.js';
	import type { RegistryEntry } from '#lib/types.js';

	const slug = $derived(page.params.slug ?? '');

	let entry = $state<RegistryEntry | null>(null);
	let loading = $state(true);
	let loadError = $state('');
	let errorStatus = $state(0);

	let runToken = 0;

	async function loadEntry(token: number, currentSlug: string, signal: AbortSignal): Promise<void> {
		loading = true;
		try {
			const result = await getRegistryEntry(currentSlug, signal);
			if (token !== runToken) return;
			entry = result;
			loadError = '';
			errorStatus = 0;
		} catch (error) {
			if (token !== runToken || (error instanceof DOMException && error.name === 'AbortError'))
				return;
			errorStatus = error instanceof ApiError ? error.status : 0;
			loadError =
				errorStatus === 404
					? 'That generator is not in the current registry.'
					: errorMessage(error, 'The registry entry could not be loaded.');
		} finally {
			if (token === runToken) loading = false;
		}
	}

	$effect(() => {
		const currentSlug = slug;
		runToken += 1;
		const token = runToken;
		const controller = new AbortController();
		entry = null;
		loadError = '';
		errorStatus = 0;
		if (currentSlug) void loadEntry(token, currentSlug, controller.signal);
		return () => {
			if (runToken === token) runToken += 1;
			controller.abort();
		};
	});

	function has(text: string | undefined, needle: string): boolean {
		return Boolean(text?.toLowerCase().includes(needle.toLowerCase()));
	}

	const hasC2pa = $derived(Boolean(entry && (has(entry.c2pa, 'yes') || has(entry.c2pa, 'c2pa'))));
	const hasSynthId = $derived(has(entry?.invisible_watermark, 'SynthID'));
	const hasOpenWatermark = $derived(
		Boolean(
			entry &&
			(has(entry.invisible_watermark, 'dwt') ||
				has(entry.invisible_watermark, 'invisible-watermark'))
		)
	);
	const hasSeal = $derived(
		Boolean(
			entry &&
			(has(entry.invisible_watermark, 'AudioSeal') ||
				has(entry.invisible_watermark, 'Video Seal') ||
				has(entry.invisible_watermark, 'VideoSeal'))
		)
	);
</script>

<PageHead
	title={entry ? `Does ${entry.tool} watermark its output?` : 'Registry entry'}
	description={entry
		? `${entry.vendor} ${entry.tool}: visible marks, invisible watermarks, C2PA, IPTC, public detector and robustness notes.`
		: 'A Provenably generator registry entry.'}
/>

<div class="shell page registry-detail">
	<p><a href={resolve('/registry')}>← Registry</a></p>

	{#if loading && !entry}
		<StateBlock
			kind="loading"
			title="Loading registry entry…"
			description="Reading the FastAPI generator record."
		/>
	{:else if loadError}
		<StateBlock
			kind="error"
			title={errorStatus === 404 ? 'Generator not found' : 'Registry entry unavailable'}
			description={loadError}
		>
			<a class="btn" href={resolve('/registry')}>Browse the registry</a>
		</StateBlock>
	{:else if entry}
		<header class="page-head">
			<p class="eyebrow">{entry.vendor} · {titleCaseToken(entry.modality)}</p>
			<h1>Does {entry.tool} watermark or sign its output?</h1>
			<p class="lede">
				Confidence <Tag tone={confidenceTone(entry.confidence)}>{entry.confidence}</Tag>
				<span> · last verified {entry.last_verified}</span>
			</p>
		</header>

		<div class="grid grid--sidebar detail-layout">
			<section class="card card--canvas" aria-labelledby="record-title">
				<h2 id="record-title">Registry record</h2>
				<dl class="kv record">
					<dt>Visible mark</dt>
					<dd>{entry.visible_mark}</dd>
					<dt>Invisible watermark</dt>
					<dd>{entry.invisible_watermark}</dd>
					<dt>Content Credentials</dt>
					<dd>{entry.c2pa}</dd>
					<dt>IPTC source type</dt>
					<dd>{entry.iptc}</dd>
					<dt>Public detector</dt>
					<dd>{entry.public_detector}</dd>
					<dt>Robustness</dt>
					<dd>{entry.survives}</dd>
					{#if entry.notes}<dt>Notes</dt>
						<dd>{entry.notes}</dd>{/if}
				</dl>
			</section>

			<aside class="stack" aria-label="How Provenably handles this generator">
				<section class="card">
					<h2>How Provenably checks for it</h2>
					<ul class="action-list">
						{#if hasC2pa}
							<li>
								<Icon name="shield" size={19} />
								<span
									><strong>C2PA runs live.</strong> A credential is trusted only when the signer chains
									to a configured trust anchor.</span
								>
							</li>
						{/if}
						{#if hasSynthId}
							<li>
								<Icon name="search" size={19} />
								<span
									><strong>SynthID is vendor-keyed.</strong> Without a configured Google/OpenAI connector,
									the report says “not configured,” never “no watermark.”</span
								>
							</li>
						{/if}
						{#if hasOpenWatermark}
							<li>
								<Icon name="scan" size={19} />
								<span
									><strong>The open DWT-DCT decoder runs live</strong> and reports match evidence rather
									than a hard binary claim.</span
								>
							</li>
						{/if}
						{#if hasSeal}
							<li>
								<Icon name="layers" size={19} />
								<span
									><strong>An open seal detector exists.</strong> It becomes live when the corresponding
									worker package is installed.</span
								>
							</li>
						{/if}
						<li>
							<Icon name="file" size={19} />
							<span
								>Unsigned IPTC, XMP, PNG text and container metadata are read and graded weak
								because they are editable.</span
							>
						</li>
					</ul>
				</section>

				<Notice tone="info" title="Layer boundary">
					<p>
						C2PA manifests and metadata are Layer-1 container footprints. Invisible watermarks
						embedded in the content are Layer-2: reportable where a detector exists, never claimed
						removed by metadata editing.
					</p>
				</Notice>
			</aside>
		</div>

		<section class="card next-card">
			<div>
				<h2>Test an actual {entry.tool} file</h2>
				<p>
					Exports, screenshots and platform processing can change what survives. The scan checks the
					copy in front of you—not the marketing claim.
				</p>
			</div>
			<div class="actions">
				<a class="btn" href={resolve('/scan')}>Scan such a file</a>
				<a class="btn btn--secondary" href={resolve('/remove')}>Review metadata removal</a>
				<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- FastAPI path outside the Svelte route manifest. -->
				<a
					class="text-link"
					href={`/v1/registry/${entry.slug}`}
					rel="external"
					data-sveltekit-reload>JSON record <Icon name="external" size={16} /></a
				>
			</div>
		</section>
	{/if}
</div>

<style>
	.registry-detail .page-head h1 {
		font-size: clamp(2.1rem, 4.5vw, 3.3rem);
	}

	.detail-layout {
		align-items: start;
	}

	.record {
		margin-top: 1.2rem;
	}

	.action-list {
		display: grid;
		gap: 1rem;
		list-style: none;
		margin: 1rem 0 0;
		padding: 0;
	}

	.action-list li {
		align-items: flex-start;
		display: flex;
		gap: 0.65rem;
	}

	.action-list :global(svg) {
		color: var(--primary-hover);
		margin-top: 0.16rem;
	}

	.next-card {
		align-items: center;
		display: flex;
		gap: 1.5rem;
		justify-content: space-between;
		margin-top: 2rem;
	}

	@media (max-width: 760px) {
		.next-card {
			align-items: stretch;
			flex-direction: column;
		}
	}
</style>
