<script lang="ts">
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import { errorMessage, getHealth, listScans } from '#lib/api.js';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import PlatformMark from '#lib/components/PlatformMark.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import { platformLabel } from '#lib/data/platform-labels.js';
	import { genericPreset, presetDefinitions } from '#lib/data/presets.js';
	import {
		defaultPreferences,
		getPreferences,
		getSessionApiKey,
		setPreferences,
		setSessionApiKey,
		type LocalPreferences
	} from '#lib/settings.js';
	import type { Health } from '#lib/types.js';

	const allPresets = [genericPreset, ...presetDefinitions];

	let preferences = $state<LocalPreferences>({ ...defaultPreferences });
	let apiKey = $state('');
	let savedMessage = $state('');
	let connectionMessage = $state('');
	let testingConnection = $state(false);
	let health = $state<Health | null>(null);

	const apiKeyConfigured = $derived(Boolean(apiKey.trim()));
	const preferredPresetDefinition = $derived(
		allPresets.find((preset) => preset.slug === preferences.preferredPreset) ?? genericPreset
	);
	const preferredPresetLabel = $derived(platformLabel(preferences.preferredPreset));

	onMount(() => {
		preferences = getPreferences();
		apiKey = getSessionApiKey();
		const controller = new AbortController();
		void getHealth(controller.signal)
			.then((result) => (health = result))
			.catch(() => {
				health = null;
			});
		return () => controller.abort();
	});

	function savePreferences(event: SubmitEvent): void {
		event.preventDefault();
		setPreferences(preferences);
		savedMessage =
			'Browser preferences saved. Server retention remains controlled by the deployment.';
	}

	function saveApiKey(event: SubmitEvent): void {
		event.preventDefault();
		setSessionApiKey(apiKey);
		savedMessage = apiKey.trim()
			? 'API key saved for this browser session only.'
			: 'Session API key cleared.';
		connectionMessage = '';
	}

	function clearApiKey(): void {
		apiKey = '';
		setSessionApiKey('');
		savedMessage = 'Session API key cleared.';
		connectionMessage = '';
	}

	async function testConnection(): Promise<void> {
		setSessionApiKey(apiKey);
		testingConnection = true;
		connectionMessage = '';
		try {
			await listScans(1);
			connectionMessage =
				'Connection succeeded. FastAPI accepted the current session configuration.';
		} catch (error) {
			connectionMessage = errorMessage(error, 'Connection failed.');
		} finally {
			testingConnection = false;
		}
	}

	function clearLocalData(): void {
		preferences = { ...defaultPreferences };
		apiKey = '';
		setPreferences(preferences);
		setSessionApiKey('');
		savedMessage = 'Provenably preferences and the session API key were cleared from this browser.';
		connectionMessage = '';
	}
</script>

<PageHead
	title="Settings — Privacy, retention and API key"
	description="Configure browser-local scan defaults, preferred platform preset and a session-only FastAPI key for this Provenably deployment."
	noindex
/>

<div class="shell page settings-page">
	<header class="page-head">
		<p class="eyebrow">Settings</p>
		<h1>Account, privacy &amp; API access</h1>
		<p class="lede">
			Until identity ships, these controls are honest about their scope: preferences live in this
			browser, the API key lives only in this tab session, and server retention is controlled by the
			deployment.
		</p>
	</header>

	{#if savedMessage}
		<div class="notice-gap" aria-live="polite">
			<Notice tone="success"><p>{savedMessage}</p></Notice>
		</div>
	{/if}

	<div class="settings-grid">
		<section class="card card--canvas" aria-labelledby="account-title">
			<div class="row row--between row--start">
				<div>
					<h2 id="account-title">Account</h2>
					<p class="muted">Anonymous deployment mode</p>
				</div>
				<Tag tone="tag--accent">Free</Tag>
			</div>
			<dl class="kv">
				<dt>Identity</dt>
				<dd>Not signed in</dd>
				<dt>History scope</dt>
				<dd>Deployment-visible until auth ships</dd>
				<dt>Deployment health</dt>
				<dd>
					{health
						? `${health.ok ? 'Healthy' : 'Degraded'} · ${health.scans_done.toLocaleString()} completed scans`
						: 'Unavailable'}
				</dd>
			</dl>
			<div class="actions">
				<a class="btn btn--secondary" href={resolve('/auth')}>Account roadmap</a>
				<a class="btn btn--ghost" href={resolve('/pricing')}>Compare plans</a>
			</div>
		</section>

		<form class="card" aria-labelledby="privacy-title" onsubmit={savePreferences}>
			<h2 id="privacy-title">Privacy &amp; defaults</h2>

			<div class="field">
				<label for="settings-retention">Preferred retention label</label>
				<select
					id="settings-retention"
					bind:value={preferences.retentionLabel}
					aria-describedby="retention-hint"
				>
					<option value="24-hours">24 hours, then delete bytes (deployment default)</option>
					<option value="hash-only">Hash-only always</option>
					<option value="7-days">7 days (Creator plan target)</option>
					<option value="30-days">30 days (Pro plan target)</option>
				</select>
				<p class="field-hint" id="retention-hint">
					This records your browser preference. The live FastAPI deployment currently controls the
					actual TTL; hash-only below is applied directly to new scans.
				</p>
			</div>

			<label class="check">
				<input type="checkbox" bind:checked={preferences.hashOnlyDefault} />
				<span
					><strong>Default new file/URL scans to hash-only</strong> — delete bytes after analysis.</span
				>
			</label>
			<label class="check">
				<input type="checkbox" bind:checked={preferences.includeJurisdictionNote} />
				<span>Include a jurisdiction disclosure note in future removal outputs.</span>
			</label>

			<div class="field">
				<label for="settings-preset">Preferred platform preset</label>
				<div class="preset-choice">
					<PlatformMark
						slug={preferredPresetDefinition.slug}
						name={preferredPresetDefinition.name}
						size={38}
					/>
					<select
						id="settings-preset"
						bind:value={preferences.preferredPreset}
						aria-describedby="settings-preset-hint"
					>
						{#each allPresets as preset (preset.slug)}<option value={preset.slug}
								>{preset.name}</option
							>{/each}
					</select>
				</div>
				<p class="field-hint" id="settings-preset-hint">
					<strong>{preferredPresetLabel.labelDisplay}:</strong>
					{preferredPresetLabel.labelSubtext}
				</p>
			</div>

			<button class="btn" type="submit">Save browser preferences</button>
		</form>

		<form class="card card--canvas" aria-labelledby="api-key-title" onsubmit={saveApiKey}>
			<div class="row row--between row--start">
				<div>
					<h2 id="api-key-title">API key for this session</h2>
					<p class="muted">
						Sent as <code>X-API-Key</code> only to same-origin Provenably API calls.
					</p>
				</div>
				<Tag tone={apiKeyConfigured ? 'tag--ok' : ''}
					>{apiKeyConfigured ? 'configured' : 'not set'}</Tag
				>
			</div>

			<div class="field">
				<label for="settings-api-key">Deployment API key</label>
				<input
					id="settings-api-key"
					type="password"
					bind:value={apiKey}
					autocomplete="off"
					placeholder="Paste a key issued by this deployment"
					aria-describedby="api-key-hint"
				/>
				<p class="field-hint" id="api-key-hint">
					Stored in <strong>sessionStorage</strong>, never localStorage, analytics or a Provenably
					server database. Closing the tab clears it.
				</p>
			</div>

			<div class="actions">
				<button class="btn btn--dark" type="submit">Save for session</button>
				<button
					class="btn btn--secondary"
					type="button"
					onclick={testConnection}
					disabled={testingConnection}
				>
					{testingConnection ? 'Testing…' : 'Test connection'}
				</button>
				<button class="btn btn--ghost" type="button" onclick={clearApiKey}>Clear</button>
			</div>
			{#if connectionMessage}<p class="small" aria-live="polite">{connectionMessage}</p>{/if}
			<p class="small muted">
				Managed personal API keys (create, scope, revoke, last-used) arrive with accounts. This
				field configures an existing deployment key; it does not mint one.
			</p>
		</form>

		<section class="card" aria-labelledby="billing-title">
			<h2 id="billing-title">Billing &amp; usage</h2>
			<p>
				Checkout, invoices and quota enforcement arrive with the billing milestone. The current
				deployment does not charge this browser or associate scans with a person.
			</p>
			<dl class="kv">
				<dt>Current mode</dt>
				<dd>Anonymous Detect</dd>
				<dt>Deployment scans</dt>
				<dd>{health ? health.scans_total.toLocaleString() : '—'}</dd>
				<dt>Personal quota</dt>
				<dd>Not tracked until accounts ship</dd>
			</dl>
			<a class="btn btn--secondary" href={resolve('/pricing')}>Review planned tiers</a>
		</section>
	</div>

	<section class="card danger-zone" aria-labelledby="danger-title">
		<div>
			<h2 id="danger-title">Browser-local data</h2>
			<p>
				Clear Provenably preferences and the session API key from this browser. Server-side scan
				reports and retained files follow the deployment’s retention job; account-level deletion
				controls require authenticated ownership.
			</p>
		</div>
		<div class="actions">
			<button class="btn btn--secondary danger-button" type="button" onclick={clearLocalData}
				>Clear browser-local data</button
			>
			<button class="btn btn--ghost" type="button" disabled>Delete account — auth pending</button>
		</div>
	</section>
</div>

<style>
	.settings-page {
		max-width: 1120px;
	}

	.notice-gap {
		margin-bottom: 1.2rem;
	}

	.settings-grid {
		display: grid;
		gap: 1rem;
		grid-template-columns: repeat(2, minmax(0, 1fr));
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

	.danger-zone {
		align-items: center;
		background: var(--bad-soft);
		display: flex;
		gap: 1.5rem;
		justify-content: space-between;
		margin-top: 1rem;
	}

	.danger-button {
		border-color: var(--bad);
		color: var(--bad);
	}

	@media (max-width: 820px) {
		.settings-grid {
			grid-template-columns: 1fr;
		}

		.danger-zone {
			align-items: stretch;
			flex-direction: column;
		}
	}
</style>
