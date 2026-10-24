<script lang="ts">
	import '#lib/mono-font.css';
	import { onMount } from 'svelte';
	import { errorMessage, getCapabilities, getHealth } from '#lib/api.js';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import type { Capabilities, Health } from '#lib/types.js';

	let capabilities = $state<Capabilities | null>(null);
	let health = $state<Health | null>(null);
	let loading = $state(true);
	let loadError = $state('');
	let copiedSnippet = $state('');

	let loadController: AbortController | undefined;

	const endpoints = [
		[
			'POST',
			'/v1/scans',
			'Detect from file, text or URL; synchronous with wait=true or async by default',
			'live'
		],
		['GET', '/v1/scans/{id}', 'Scan status plus the complete graded report', 'live'],
		['GET', '/v1/scans', 'Deployment scan history summaries', 'live'],
		['POST', '/v1/scans/demo/{name}', 'Create a scan from a bundled fixture', 'live'],
		['GET', '/v1/demo-files', 'Bundled fixture catalogue for the frontend', 'live'],
		['POST', '/v1/remove', 'Detect → Remove → Verify with policy, preset and attestation', 'R0–R2'],
		['POST', '/v1/batch', 'Native multi-file job with ZIP and manifest outputs', 'R3'],
		['GET', '/v1/presets', 'Platform preset catalogue', 'R3'],
		['GET', '/v1/registry', 'Generator watermark/provenance registry', 'live'],
		['POST', '/v1/disclosure/check', 'Jurisdiction disclosure checklist', 'live'],
		['POST', '/v1/platforms/preview', 'Likely platform labels from report facts', 'live'],
		['POST', '/v1/text/unicode', 'Hidden Unicode scan and cleaner', 'live'],
		['POST', '/v1/lab/greenlist', 'Toy keyed green-list watermark lab', 'live'],
		['GET', '/v1/capabilities', 'Live versus manual-integration capability matrix', 'live'],
		['GET', '/health', 'Process and scan-store health', 'live']
	] as const;

	const snippets = [
		{
			id: 'detect-file',
			title: 'Detect a file (synchronous)',
			code: `curl -s \\
  -F "file=@photo.jpg" \\
  -F "wait=true" \\
  https://your-deployment.example/v1/scans | jq .conclusion`
		},
		{
			id: 'detect-async',
			title: 'Detect asynchronously, then poll',
			code: `scan_id=$(curl -s -F "file=@clip.mp4" \\
  https://your-deployment.example/v1/scans | jq -r .id)

curl -s "https://your-deployment.example/v1/scans/$scan_id" | jq .`
		},
		{
			id: 'disclosure',
			title: 'Run a disclosure check',
			code: `curl -s https://your-deployment.example/v1/disclosure/check \\
  -H 'content-type: application/json' \\
  -d '{"content_type":"video","is_ai_generated":true}' | jq .`
		},
		{
			id: 'remove-contract',
			title: 'Target Remove contract (R0–R2)',
			code: `# Not deployed yet—shown so clients can design against the locked workflow.
curl -s \\
  -F "file=@photo.jpg" \\
  -F "preset=instagram" \\
  -F "attestation=true" \\
  https://your-deployment.example/v1/remove`
		}
	];

	async function loadStatus(signal?: AbortSignal): Promise<void> {
		loading = true;
		try {
			const [nextCapabilities, nextHealth] = await Promise.all([
				getCapabilities(signal),
				getHealth(signal)
			]);
			capabilities = nextCapabilities;
			health = nextHealth;
			loadError = '';
		} catch (error) {
			if (!(error instanceof DOMException && error.name === 'AbortError')) {
				loadError = errorMessage(error, 'Live API status could not be loaded.');
			}
		} finally {
			if (!signal?.aborted) loading = false;
		}
	}

	onMount(() => {
		loadController = new AbortController();
		void loadStatus(loadController.signal);
		return () => loadController?.abort();
	});

	async function refresh(): Promise<void> {
		loadController?.abort();
		loadController = new AbortController();
		await loadStatus(loadController.signal);
	}

	function formatCapability(value: string | number | boolean | string[]): string {
		if (Array.isArray(value)) return value.length ? value.join(', ') : 'none configured';
		if (typeof value === 'boolean') return value ? 'live' : 'not available';
		return String(value);
	}

	async function copySnippet(id: string, code: string): Promise<void> {
		try {
			await navigator.clipboard.writeText(code);
			copiedSnippet = id;
		} catch {
			copiedSnippet = '';
		}
	}
</script>

<PageHead
	title="API & deployment status"
	description="Live FastAPI capability matrix, endpoint contract, quickstart examples and health for this Provenably deployment."
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Developers</p>
		<h1>API &amp; deployment status</h1>
		<p class="lede">
			SvelteKit is the interface; FastAPI remains the source of truth. This page reads live
			capability and health endpoints so integrators can see exactly what will—and will not—run
			before trusting a report.
		</p>
		<div class="actions">
			<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- FastAPI path outside the Svelte route manifest. -->
			<a class="btn btn--dark" href="/api/docs" rel="external" data-sveltekit-reload
				>Open interactive OpenAPI <Icon name="external" size={17} /></a
			>
			<button class="btn btn--secondary" type="button" onclick={refresh} disabled={loading}
				>{loading ? 'Refreshing…' : 'Refresh status'}</button
			>
			<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- FastAPI path outside the Svelte route manifest. -->
			<a class="text-link" href="/health" rel="external" data-sveltekit-reload
				>Raw health JSON <Icon name="external" size={16} /></a
			>
		</div>
	</header>

	{#if loadError}
		<StateBlock kind="error" title="Live deployment status unavailable" description={loadError}>
			<button class="btn" type="button" onclick={refresh}>Retry</button>
		</StateBlock>
	{:else if loading && !capabilities}
		<StateBlock
			kind="loading"
			title="Loading live capabilities…"
			description="FastAPI reports optional analyzers and manual integrations honestly."
		/>
	{:else if capabilities && health}
		<section class="metrics" aria-label="API health summary">
			<div>
				<span class="dot dot--ok" aria-hidden="true"></span><strong
					>{health.ok ? 'API healthy' : 'API degraded'}</strong
				><span>FastAPI status</span>
			</div>
			<div><strong>{health.version}</strong><span>Backend version</span></div>
			<div><strong>{health.scans_done.toLocaleString()}</strong><span>completed scans</span></div>
			<div>
				<strong>{health.scans_total.toLocaleString()}</strong><span>total scans stored</span>
			</div>
		</section>

		<div class="grid grid--2 capability-grid">
			<section aria-labelledby="live-title">
				<h2 id="live-title">Live in this deployment</h2>
				<div class="table-wrap compact">
					<table>
						<caption class="visually-hidden">Live Provenably API capabilities</caption>
						<thead><tr><th scope="col">Capability</th><th scope="col">Status</th></tr></thead>
						<tbody>
							{#each Object.entries(capabilities.live) as [name, value] (name)}
								<tr>
									<th scope="row" class="mono">{name}</th>
									<td>
										{#if typeof value === 'boolean'}
											<Tag tone={value ? 'tag--ok' : 'tag--warn'}
												>{value ? 'live' : 'not available'}</Tag
											>
										{:else}
											{formatCapability(value)}
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>

			<section aria-labelledby="manual-title">
				<h2 id="manual-title">Manual integration</h2>
				<p class="muted">
					These are deployment or partner integrations, not hidden roadmap marketing. Reports mark
					the affected signals <code>not_configured</code> or <code>not_installed</code>.
				</p>
				<div class="table-wrap compact">
					<table>
						<caption class="visually-hidden">Manual integration capability state</caption>
						<thead><tr><th scope="col">Integration</th><th scope="col">Configured</th></tr></thead>
						<tbody>
							{#each Object.entries(capabilities.manual_integration) as [name, configured] (name)}
								<tr>
									<th scope="row" class="mono">{name}</th>
									<td
										><Tag tone={configured ? 'tag--ok' : 'tag--manual'}
											>{configured ? 'configured' : 'not configured'}</Tag
										></td
									>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		</div>
	{/if}

	<section class="api-section" aria-labelledby="quickstart-title">
		<div class="section-head">
			<p class="eyebrow">Quickstart</p>
			<h2 id="quickstart-title">Use relative contracts, not UI scraping.</h2>
			<p>
				Browser clients should call same-origin <code>/v1/...</code> paths. In local development Vite
				proxies them to FastAPI; in production FastAPI serves both.
			</p>
		</div>
		<div class="grid grid--2">
			{#each snippets as snippet (snippet.id)}
				<article class="snippet">
					<div class="row row--between snippet__head">
						<h3>{snippet.title}</h3>
						<button
							class="btn btn--secondary btn--small"
							type="button"
							onclick={() => copySnippet(snippet.id, snippet.code)}
						>
							{copiedSnippet === snippet.id ? 'Copied' : 'Copy'}
						</button>
					</div>
					<pre><code>{snippet.code}</code></pre>
				</article>
			{/each}
		</div>
	</section>

	<section class="api-section" aria-labelledby="endpoints-title">
		<div class="section-head">
			<p class="eyebrow">Contract</p>
			<h2 id="endpoints-title">Endpoints</h2>
			<p>
				Roadmap endpoints are listed to lock the frontend contract; their status is never shown as
				live before FastAPI implements them.
			</p>
		</div>
		<div class="table-wrap">
			<table>
				<caption class="visually-hidden">Provenably API endpoint contract</caption>
				<thead
					><tr
						><th scope="col">Method</th><th scope="col">Path</th><th scope="col">Purpose</th><th
							scope="col">Status</th
						></tr
					></thead
				>
				<tbody>
					{#each endpoints as [method, path, purpose, status] (path + method)}
						<tr>
							<td><Tag>{method}</Tag></td>
							<th scope="row" class="mono">{path}</th>
							<td>{purpose}</td>
							<td><Tag tone={status === 'live' ? 'tag--ok' : 'tag--accent'}>{status}</Tag></td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>

	<div class="api-section">
		<Notice tone="info" title="Authentication in this prototype">
			<p>
				When a deployment sets API keys, scan endpoints require <code>X-API-Key</code>. The Settings
				page can store a key for the current browser session only. Public production should replace
				this hook with the selected identity provider and per-user authorization.
			</p>
		</Notice>
	</div>
</div>

<style>
	.metrics {
		display: grid;
		gap: 0.8rem;
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.metrics > div {
		background: var(--canvas-soft);
		border-radius: var(--radius);
		padding: 1.1rem;
	}

	.metrics strong {
		display: block;
		font-family: var(--font-display);
		font-size: 1.6rem;
		font-variant-numeric: lining-nums tabular-nums;
		font-weight: var(--fw-display-strong);
		letter-spacing: -0.03em;
		line-height: 1.15;
		margin-top: 0.25rem;
		overflow-wrap: anywhere;
	}

	.metrics span {
		color: var(--body-mid);
		font-size: 0.88rem;
	}

	.capability-grid,
	.api-section {
		margin-top: clamp(2.5rem, 6vw, 4rem);
	}

	.compact table {
		min-width: 0;
	}

	.snippet {
		min-width: 0;
	}

	.snippet__head {
		margin-bottom: 0.7rem;
	}

	.snippet h3 {
		margin: 0;
	}

	@media (max-width: 800px) {
		.metrics {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
</style>
