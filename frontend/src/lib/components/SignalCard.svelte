<script lang="ts">
	import '#lib/mono-font.css';
	import { formatDuration, gradeTone, safeJson, statusTone, titleCaseToken } from '../format';
	import type { JsonValue, Signal } from '../types';
	import Tag from './Tag.svelte';

	interface Props {
		signal: Signal;
	}

	let { signal }: Props = $props();
	let showRaw = $state(false);

	const showGrade = $derived(signal.status === 'detected' || signal.status === 'inconclusive');
	const rawJson = $derived(showRaw && signal.data ? safeJson(signal.data) : '');

	type JsonRecord = Record<string, JsonValue>;

	function asRecord(value: JsonValue | undefined): JsonRecord | undefined {
		return value && typeof value === 'object' && !Array.isArray(value) ? value : undefined;
	}

	function asArray(value: JsonValue | undefined): JsonValue[] {
		return Array.isArray(value) ? value : [];
	}

	function asText(value: JsonValue | undefined): string {
		if (typeof value === 'string') return value;
		if (typeof value === 'number' || typeof value === 'boolean') return String(value);
		return '';
	}

	function joined(value: JsonValue | undefined): string {
		return asArray(value).map(asText).filter(Boolean).join(', ');
	}

	function manifestEntries(): Array<[string, JsonRecord]> {
		const manifests = asRecord(signal.data?.manifests);
		if (!manifests) return [];
		return Object.entries(manifests).flatMap(([label, value]) => {
			const manifest = asRecord(value);
			return manifest ? [[label, manifest] as [string, JsonRecord]] : [];
		});
	}

	function signerText(manifest: JsonRecord): string {
		const signer = asRecord(manifest.signer);
		if (!signer) return '—';
		return (
			[asText(signer.issuer), asText(signer.common_name), asText(signer.alg), asText(signer.time)]
				.filter(Boolean)
				.join(' · ') || '—'
		);
	}

	function actionRows(
		manifest: JsonRecord
	): Array<{ action: string; agent: string; source: string }> {
		return asArray(manifest.actions).flatMap((value) => {
			const action = asRecord(value);
			if (!action) return [];
			return [
				{
					action: asText(action.action) || 'action',
					agent: asText(action.softwareAgent),
					source: asText(action.digitalSourceType)
				}
			];
		});
	}

	function ingredientText(manifest: JsonRecord): string {
		const values = asArray(manifest.ingredients).flatMap((value) => {
			const ingredient = asRecord(value);
			if (!ingredient) return [];
			const statuses = asArray(ingredient.validation_status).length;
			const relationship = asText(ingredient.relationship);
			return [
				`${asText(ingredient.title) || 'Untitled ingredient'}${relationship ? ` [${relationship}${statuses ? `, ${statuses} status item(s)` : ''}]` : ''}`
			];
		});
		return values.join(', ') || '—';
	}

	function softBindingText(manifest: JsonRecord): string {
		return asArray(manifest.soft_bindings)
			.flatMap((value) => {
				const binding = asRecord(value);
				if (!binding) return [];
				return [`${asText(binding.alg) || 'unknown'} (${asText(binding.blocks) || '0'} blocks)`];
			})
			.join(', ');
	}

	function validationRows(): Array<{ label: string; tone: string; codes: string[] }> {
		const validation = asRecord(signal.data?.validation_codes);
		if (!validation) return [];
		const definitions = [
			['failure', 'failures', 'tag--bad'],
			['success', 'passed', 'tag--ok'],
			['informational', 'info', '']
		] as const;
		return definitions.flatMap(([key, label, tone]) => {
			const codes = asArray(validation[key]).flatMap((value) => {
				const item = asRecord(value);
				const code = item ? asText(item.code) : asText(value);
				return code ? [code] : [];
			});
			return codes.length ? [{ label, tone, codes }] : [];
		});
	}

	const manifests = $derived(manifestEntries());
	const validations = $derived(validationRows());
	const activeManifest = $derived(asText(signal.data?.active_manifest));
	const remoteManifestUrl = $derived(asText(signal.data?.remote_manifest_url));
</script>

<article class="signal">
	<div>
		<h3 class="signal__name">{signal.name}</h3>
		<p class="signal__meta">
			{titleCaseToken(signal.kind)}
			{#if signal.duration_ms !== undefined && signal.duration_ms !== null}· {formatDuration(
					signal.duration_ms
				)}{/if}
		</p>
		<div class="signal__tags">
			<Tag tone={statusTone(signal.status)}>{titleCaseToken(signal.status)}</Tag>
			{#if showGrade}<Tag tone={gradeTone(signal.evidence_grade)}>{signal.evidence_grade}</Tag>{/if}
		</div>
	</div>

	<div>
		<p class="signal__summary">{signal.summary}</p>
		{#if signal.method}<p class="small muted">Method: {signal.method}</p>{/if}
		{#if signal.manual_integration}<p class="signal__how">
				<strong>Enable:</strong>
				{signal.manual_integration}
			</p>{/if}

		{#if signal.kind === 'c2pa' && manifests.length}
			<div class="manifests">
				{#each manifests as [label, manifest] (label)}
					<section
						class="card card--canvas manifest"
						aria-label={`Content Credential manifest ${label}`}
					>
						<div class="row row--between row--start">
							<div>
								<h4>{asText(manifest.title) || label}</h4>
								<p class="tiny muted mono">{label}</p>
							</div>
							{#if label === activeManifest}<Tag tone="tag--accent">active manifest</Tag>{/if}
						</div>

						<dl class="kv manifest__facts">
							<dt>Claim generator</dt>
							<dd>{asText(manifest.claim_generator) || '—'}</dd>
							<dt>Signer</dt>
							<dd>{signerText(manifest)}</dd>
							<dt>Source classes</dt>
							<dd>{joined(manifest.dst_classes) || '—'}</dd>
							<dt>Actions</dt>
							<dd>
								{#if actionRows(manifest).length}
									<ul class="action-list">
										{#each actionRows(manifest) as action (action.action + action.agent + action.source)}
											<li>
												<code>{action.action}</code>
												{#if action.agent}<span> · {action.agent}</span>{/if}
												{#if action.source}<br /><code class="muted">{action.source}</code>{/if}
											</li>
										{/each}
									</ul>
								{:else}—{/if}
							</dd>
							<dt>Ingredients</dt>
							<dd>{ingredientText(manifest)}</dd>
							<dt>Assertions</dt>
							<dd class="mono">{joined(manifest.assertion_labels) || '—'}</dd>
							{#if softBindingText(manifest)}<dt>Soft bindings</dt>
								<dd>{softBindingText(manifest)}</dd>{/if}
							{#if manifest.training_mining}<dt>Training/mining</dt>
								<dd class="mono">{safeJson(manifest.training_mining)}</dd>{/if}
						</dl>
					</section>
				{/each}
			</div>

			{#if validations.length}
				<div class="validations" aria-label="C2PA validation codes">
					{#each validations as row (row.label)}
						<p>
							<Tag tone={row.tone}>{row.label}</Tag>
							<span class="mono validation-codes">{row.codes.join(' ')}</span>
						</p>
					{/each}
				</div>
			{/if}

			{#if remoteManifestUrl}
				<p class="small muted">Remote manifest: <span class="mono">{remoteManifestUrl}</span></p>
			{/if}
		{/if}

		{#if signal.data && Object.keys(signal.data).length}
			<details
				ontoggle={(event) => {
					showRaw = (event.currentTarget as HTMLDetailsElement).open;
				}}
			>
				<summary>Raw signal data</summary>
				{#if showRaw}<pre aria-label={`Raw data for ${signal.name}`}>{rawJson}</pre>{/if}
			</details>
		{/if}
	</div>
</article>

<style>
	.signal__name {
		font-size: 1.02rem;
		margin: 0;
	}

	.signal__tags {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		margin-top: 0.65rem;
	}

	.signal__summary {
		color: var(--ink-mid);
		margin-bottom: 0.55rem;
	}

	.manifests {
		display: grid;
		gap: 0.8rem;
		margin-top: 1rem;
	}

	.manifest {
		padding: 1rem;
	}

	.manifest h4 {
		color: var(--ink);
		font-size: 1rem;
		margin: 0 0 0.2rem;
	}

	.manifest__facts {
		margin-top: 1rem;
	}

	.action-list {
		margin: 0;
		padding-left: 1.1rem;
	}

	.validations {
		margin-top: 0.9rem;
	}

	.validations p {
		align-items: flex-start;
		display: flex;
		flex-wrap: wrap;
		gap: 0.55rem;
		margin-bottom: 0.45rem;
	}

	.validation-codes {
		font-size: 0.8rem;
		overflow-wrap: anywhere;
	}
</style>
