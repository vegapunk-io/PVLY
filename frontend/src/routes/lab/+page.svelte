<script lang="ts">
	import '#lib/mono-font.css';
	import { errorMessage, runGreenlist } from '#lib/api.js';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import type { GreenlistStats } from '#lib/types.js';

	let generateKey = $state('demo-key');
	let gamma = $state(0.5);
	let strength = $state(0.9);
	let tokenCount = $state(300);
	let generatedStats = $state<GreenlistStats | null>(null);
	let detectText = $state('');
	let detectKey = $state('demo-key');
	let detectStats = $state<GreenlistStats | null>(null);
	let detectedWithKey = $state('');
	let busyAction = $state('');
	let pageError = $state('');

	let requestController: AbortController | undefined;

	async function generate(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		requestController?.abort();
		requestController = new AbortController();
		busyAction = 'generate';
		pageError = '';
		try {
			const result = await runGreenlist(
				{ action: 'generate', key: generateKey, gamma, strength, n: tokenCount },
				requestController.signal
			);
			detectText = result.text ?? '';
			detectKey = generateKey;
			generatedStats = result.stats;
			detectStats = null;
			detectedWithKey = '';
		} catch (error) {
			if (!(error instanceof DOMException && error.name === 'AbortError')) {
				pageError = errorMessage(error, 'The lab could not generate sample text.');
			}
		} finally {
			busyAction = '';
		}
	}

	async function detect(key: string): Promise<void> {
		if (!detectText.trim()) {
			pageError = 'Generate or paste text before running detection.';
			return;
		}
		requestController?.abort();
		requestController = new AbortController();
		busyAction = key === detectKey ? 'detect' : 'wrong-key';
		pageError = '';
		try {
			const result = await runGreenlist(
				{ action: 'detect', key, gamma, text: detectText },
				requestController.signal
			);
			detectStats = result.stats;
			detectedWithKey = key;
		} catch (error) {
			if (!(error instanceof DOMException && error.name === 'AbortError')) {
				pageError = errorMessage(error, 'The lab could not run detection.');
			}
		} finally {
			busyAction = '';
		}
	}

	function verdictTone(stats: GreenlistStats): string {
		if (stats.error) return 'tag--bad';
		if ((stats.z ?? 0) > 4) return 'tag--ok';
		if ((stats.z ?? 0) > 2) return 'tag--warn';
		return '';
	}

	function exponential(value: number | undefined): string {
		return typeof value === 'number' && Number.isFinite(value) ? value.toExponential(2) : '–';
	}
</script>

<PageHead
	title="Lab: Green-list text watermark"
	description="Generate and detect a toy keyed green-list text watermark to understand z-scores, green-token counts and why key possession changes the conclusion."
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Watermark lab</p>
		<h1>Why a key changes what a detector can claim.</h1>
		<p class="lede">
			This is a deliberately small, transparent green-list watermark. Generate marked token text,
			detect it with the same key, then try a wrong key and watch the statistical signal disappear.
		</p>
	</header>

	<Notice tone="warning" title="A teaching model, not a production AI detector">
		<p>
			The lab uses a toy vocabulary and a known key. Real vendor text watermarks are keyed inside
			generation; without the provider’s key or detector, Provenably reports that check as not
			configured instead of guessing.
		</p>
	</Notice>

	{#if pageError}<div class="notice-gap"><Notice tone="error"><p>{pageError}</p></Notice></div>{/if}

	<div class="grid grid--2 lab-layout">
		<form class="card card--canvas" aria-labelledby="generate-title" onsubmit={generate}>
			<p class="eyebrow">Generate</p>
			<h2 id="generate-title">Create marked text</h2>

			<div class="field">
				<label for="lab-generate-key">Secret key</label>
				<input
					id="lab-generate-key"
					type="text"
					bind:value={generateKey}
					autocomplete="off"
					required
				/>
			</div>

			<div class="field">
				<label for="lab-gamma"
					>Gamma (green-list fraction): <output for="lab-gamma">{gamma.toFixed(2)}</output></label
				>
				<input id="lab-gamma" type="range" min="0.1" max="0.9" step="0.05" bind:value={gamma} />
				<p class="field-hint">
					Gamma is shared with detection. The API’s default teaching value is 0.50.
				</p>
			</div>

			<div class="field">
				<label for="lab-strength"
					>Strength: <output for="lab-strength">{strength.toFixed(2)}</output></label
				>
				<input id="lab-strength" type="range" min="0" max="1" step="0.05" bind:value={strength} />
			</div>

			<div class="field">
				<label for="lab-count">Tokens</label>
				<input
					id="lab-count"
					type="number"
					min="20"
					max="2000"
					step="10"
					bind:value={tokenCount}
					required
				/>
			</div>

			<button class="btn" type="submit" disabled={Boolean(busyAction)}>
				{busyAction === 'generate' ? 'Generating…' : 'Generate marked text'}
			</button>

			{#if generatedStats}
				<div class="stats" aria-live="polite">
					<h3>Detection with the generation key</h3>
					{#if generatedStats.error}
						<Notice tone="error"><p>{generatedStats.error}</p></Notice>
					{:else}
						<p>
							<Tag tone={verdictTone(generatedStats)}>{generatedStats.verdict ?? 'scored'}</Tag>
							<span>
								z = <strong>{generatedStats.z}</strong> · green {generatedStats.green}/{generatedStats.scored_tokens}
								tokens · one-sided p = {exponential(generatedStats.p_one_sided)}</span
							>
						</p>
					{/if}
				</div>
			{/if}
		</form>

		<section class="card" aria-labelledby="detect-title">
			<p class="eyebrow">Detect</p>
			<h2 id="detect-title">Score text against a key</h2>

			<div class="field">
				<label for="lab-detect-text">Text</label>
				<textarea
					id="lab-detect-text"
					bind:value={detectText}
					spellcheck="false"
					placeholder="Generated text will appear here, or paste space-separated toy tokens."
				></textarea>
				<p class="field-hint">
					{detectText.trim() ? detectText.trim().split(/\s+/).length : 0} tokens
				</p>
			</div>

			<div class="field">
				<label for="lab-detect-key">Detection key</label>
				<input id="lab-detect-key" type="text" bind:value={detectKey} autocomplete="off" />
			</div>

			<div class="actions">
				<button
					class="btn btn--dark"
					type="button"
					disabled={Boolean(busyAction) || !detectText.trim()}
					onclick={() => detect(detectKey)}
				>
					{busyAction === 'detect' ? 'Detecting…' : 'Detect with this key'}
				</button>
				<button
					class="btn btn--secondary"
					type="button"
					disabled={Boolean(busyAction) || !detectText.trim()}
					onclick={() => detect('not-the-key')}
				>
					{busyAction === 'wrong-key' ? 'Detecting…' : 'Try a wrong key'}
				</button>
			</div>

			{#if detectStats}
				<div class="stats" aria-live="polite">
					<h3>Result for key <code>{detectedWithKey}</code></h3>
					{#if detectStats.error}
						<Notice tone="error"><p>{detectStats.error}</p></Notice>
					{:else}
						<p>
							<Tag tone={verdictTone(detectStats)}>{detectStats.verdict ?? 'scored'}</Tag>
							<span>
								z = <strong>{detectStats.z}</strong> · green {detectStats.green}/{detectStats.scored_tokens}
								tokens · one-sided p = {exponential(detectStats.p_one_sided)}</span
							>
						</p>
						<p class="small muted">
							A high z-score means green-list tokens occur far more often than chance under this
							exact key and gamma. It does not identify a real-world model or author.
						</p>
					{/if}
				</div>
			{/if}
		</section>
	</div>

	<section class="card lab-explainer">
		<h2>How to read the result</h2>
		<div class="grid grid--3">
			<div>
				<h3>z &gt; 4</h3>
				<p>Strong statistical match for this toy scheme and key.</p>
			</div>
			<div>
				<h3>2 &lt; z ≤ 4</h3>
				<p>Borderline. Get more tokens and corroborate before making a claim.</p>
			</div>
			<div>
				<h3>z ≤ 2</h3>
				<p>No meaningful green-list excess. The key may be wrong or the text may be unmarked.</p>
			</div>
		</div>
	</section>
</div>

<style>
	.notice-gap,
	.lab-layout {
		margin-top: 1.5rem;
	}

	.lab-layout {
		align-items: start;
	}

	input[type='range'] {
		accent-color: var(--primary);
		min-height: 44px;
		width: 100%;
	}

	textarea {
		font-family: var(--font-mono);
		font-size: 0.9rem;
		min-height: 240px;
	}

	.stats {
		border-top: 1px solid var(--line);
		margin-top: 1.4rem;
		padding-top: 1.1rem;
	}

	.lab-explainer {
		margin-top: 1rem;
	}
</style>
