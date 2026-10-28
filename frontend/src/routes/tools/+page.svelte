<script lang="ts">
	import { resolve } from '$app/paths';
	import '#lib/mono-font.css';
	import { errorMessage, fetchText, scanUnicode } from '#lib/api.js';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import Tag from '#lib/components/Tag.svelte';
	import type { UnicodeFinding, UnicodeResult } from '#lib/types.js';

	let inputText = $state('');
	let cleanedText = $state('');
	let keepJoiners = $state(true);
	let asciiDashes = $state(false);
	let result = $state<UnicodeResult | null>(null);
	let scannedText = $state('');
	let loadingAction = $state('');
	let pageError = $state('');
	let copyMessage = $state('');

	let requestController: AbortController | undefined;

	const inputCharacters = $derived(Array.from(inputText).length);
	const findings = $derived((result?.scan.findings ?? []).slice(0, 25));

	async function loadSample(): Promise<void> {
		requestController?.abort();
		requestController = new AbortController();
		loadingAction = 'sample';
		pageError = '';
		try {
			inputText = await fetchText('/demo-assets/text_hidden_chars.txt', requestController.signal);
			result = null;
			cleanedText = '';
		} catch (error) {
			if (!(error instanceof DOMException && error.name === 'AbortError')) {
				pageError = errorMessage(error, 'The demo text could not be loaded.');
			}
		} finally {
			loadingAction = '';
		}
	}

	async function runScan(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		if (!inputText) {
			pageError = 'Paste or type some text first.';
			return;
		}
		requestController?.abort();
		requestController = new AbortController();
		loadingAction = 'scan';
		pageError = '';
		copyMessage = '';
		scannedText = inputText;

		try {
			result = await scanUnicode(
				{ text: inputText, keep_joiners: keepJoiners, ascii_dashes: asciiDashes },
				requestController.signal
			);
			cleanedText = result.cleaned;
		} catch (error) {
			if (!(error instanceof DOMException && error.name === 'AbortError')) {
				pageError = errorMessage(error, 'The Unicode scan could not be completed.');
			}
		} finally {
			loadingAction = '';
		}
	}

	function contextFor(finding: UnicodeFinding): { before: string; after: string } {
		const characters = Array.from(scannedText);
		return {
			before: characters.slice(Math.max(0, finding.pos - 12), finding.pos).join(''),
			after: characters.slice(finding.pos + 1, finding.pos + 13).join('')
		};
	}

	async function copyCleaned(): Promise<void> {
		try {
			await navigator.clipboard.writeText(cleanedText);
			copyMessage = 'Cleaned text copied.';
		} catch {
			copyMessage = 'Clipboard access was unavailable; select the cleaned text to copy it.';
		}
	}

	function downloadCleaned(): void {
		const blob = new Blob([cleanedText], { type: 'text/plain;charset=utf-8' });
		const objectUrl = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = objectUrl;
		link.download = 'provenably-cleaned.txt';
		document.body.append(link);
		link.click();
		link.remove();
		setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
	}
</script>

<PageHead
	title="Text tools: Unicode hygiene"
	description="Find zero-width characters, bidi controls, homoglyphs and suspicious typography, then produce a cleaned copy without destroying legitimate joining characters by default."
/>

<div class="shell page">
	<header class="page-head">
		<p class="eyebrow">Text tools</p>
		<h1>Unicode hygiene, with the evidence left visible.</h1>
		<p class="lede">
			Find invisible characters, directional controls, homoglyphs and formatting artifacts that can
			survive copy-paste. The cleaner returns a separate copy, and your original stays untouched.
		</p>
	</header>

	<Notice tone="info" title="Hidden characters are not proof of AI authorship">
		<p>
			They can come from editors, PDFs, web pages, messaging apps or deliberate marking. Provenably
			grades them as a text-hygiene signal and shows each code point’s position so a human can judge
			the context.
		</p>
	</Notice>

	<form class="tools-layout" onsubmit={runScan}>
		<section class="card card--canvas" aria-labelledby="input-title">
			<div class="row row--between row--start">
				<div>
					<h2 id="input-title">Input</h2>
					<p class="small muted">{inputCharacters.toLocaleString()} Unicode code points</p>
				</div>
				<button
					class="btn btn--secondary btn--small"
					type="button"
					onclick={loadSample}
					disabled={Boolean(loadingAction)}
				>
					{loadingAction === 'sample' ? 'Loading…' : 'Load hidden-char sample'}
				</button>
			</div>

			<div class="field">
				<label for="unicode-input">Text to inspect</label>
				<textarea
					id="unicode-input"
					bind:value={inputText}
					placeholder="Paste text here…"
					spellcheck="false"
					disabled={loadingAction === 'scan'}
					aria-describedby="unicode-input-hint"></textarea>
				<p class="field-hint" id="unicode-input-hint">
					Text is sent only to this deployment’s <code>/v1/text/unicode</code> endpoint.
				</p>
			</div>

			<fieldset>
				<legend>Cleaning options</legend>
				<label class="check">
					<input type="checkbox" bind:checked={keepJoiners} />
					<span
						><strong>Keep legitimate joiners</strong>: preserve ZWJ/ZWNJ where scripts need them
						(recommended).</span
					>
				</label>
				<label class="check">
					<input type="checkbox" bind:checked={asciiDashes} />
					<span>Normalize typographic dashes to ASCII hyphens in the cleaned copy.</span>
				</label>
			</fieldset>

			{#if pageError}<p class="field-error" role="alert">{pageError}</p>{/if}

			<button class="btn" type="submit" disabled={!inputText || Boolean(loadingAction)}>
				{loadingAction === 'scan' ? 'Scanning…' : 'Scan & clean'}
				<Icon name="arrow-right" size={18} />
			</button>
		</section>

		<section class="card" aria-labelledby="output-title">
			<div class="row row--between row--start">
				<div>
					<h2 id="output-title">Cleaned copy</h2>
					<p class="small muted">{Array.from(cleanedText).length.toLocaleString()} code points</p>
				</div>
				{#if result}<Tag tone={result.changed ? 'tag--warn' : 'tag--ok'}
						>{result.changed ? 'changed' : 'unchanged'}</Tag
					>{/if}
			</div>

			<div class="field">
				<label for="unicode-output">Cleaned text</label>
				<textarea
					id="unicode-output"
					bind:value={cleanedText}
					readonly
					placeholder="Run a scan to produce the cleaned copy."
					spellcheck="false"></textarea>
			</div>

			<div class="actions">
				<button class="btn btn--dark" type="button" disabled={!cleanedText} onclick={copyCleaned}
					>Copy cleaned text</button
				>
				<button
					class="btn btn--secondary"
					type="button"
					disabled={!cleanedText}
					onclick={downloadCleaned}
				>
					<Icon name="download" size={18} /> Download .txt
				</button>
			</div>
			{#if copyMessage}<p class="small" aria-live="polite">{copyMessage}</p>{/if}
			<p class="small muted">
				Need the full graded provenance report instead? Paste the same text into <a
					href={resolve('/scan?tab=text')}>Scan → Text</a
				>.
			</p>
		</section>
	</form>

	{#if result}
		<section class="results" aria-labelledby="unicode-results-title" aria-live="polite">
			<div class="section-head">
				<p class="eyebrow">Findings</p>
				<h2 id="unicode-results-title">
					{result.scan.count} suspicious code point{result.scan.count === 1 ? '' : 's'} in {result.scan.stats.chars.toLocaleString()}
					characters
				</h2>
				<p>
					{result.changed
						? 'The cleaned copy differs from the input under the selected policy.'
						: 'Nothing was changed under the selected cleaning policy.'}
				</p>
			</div>

			<div class="metrics" aria-label="Typography statistics">
				<div><strong>{result.scan.stats.em_dashes}</strong><span>em dashes</span></div>
				<div><strong>{result.scan.stats.curly_quotes}</strong><span>curly quotes</span></div>
				<div><strong>{result.scan.stats.double_spaces}</strong><span>double spaces</span></div>
				<div>
					<strong>{result.scan.stats.trailing_space_lines}</strong><span
						>lines with trailing spaces</span
					>
				</div>
			</div>

			{#if Object.keys(result.scan.by_type ?? {}).length}
				<h3>By category</h3>
				<div class="table-wrap compact">
					<table>
						<caption class="visually-hidden">Suspicious Unicode findings by category</caption>
						<thead
							><tr><th scope="col">Category</th><th scope="col" class="num">Count</th></tr></thead
						>
						<tbody>
							{#each Object.entries(result.scan.by_type ?? {}) as [category, count] (category)}
								<tr><th scope="row">{category}</th><td class="num">{count}</td></tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}

			{#if findings.length}
				<h3>First {findings.length} findings</h3>
				<div class="table-wrap">
					<table>
						<caption class="visually-hidden"
							>Suspicious Unicode code points and their context</caption
						>
						<thead
							><tr
								><th scope="col">Code point</th><th scope="col">Name</th><th scope="col" class="num"
									>Position</th
								><th scope="col">Context</th></tr
							></thead
						>
						<tbody>
							{#each findings as finding (`${finding.cp}-${finding.pos}`)}
								{@const context = contextFor(finding)}
								<tr>
									<td class="mono">{finding.cp}</td>
									<td>{finding.name}</td>
									<td class="num">{finding.pos}</td>
									<td class="mono context"
										>{context.before}<mark aria-label="suspicious invisible character">·</mark
										>{context.after}</td
									>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				<p class="small muted">
					The dot marks the suspicious code point; it is not present in the source text.
				</p>
			{/if}
		</section>
	{/if}
</div>

<style>
	.tools-layout {
		align-items: start;
		display: grid;
		gap: 1rem;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		margin-top: 2rem;
	}

	.tools-layout textarea {
		font-family: var(--font-mono);
		font-size: 0.92rem;
		min-height: 280px;
	}

	.results {
		margin-top: clamp(3rem, 7vw, 5rem);
	}

	.metrics {
		display: grid;
		gap: 0.8rem;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		margin-bottom: 2rem;
	}

	.metrics > div {
		background: var(--canvas-soft);
		border-radius: var(--radius);
		padding: 1rem;
	}

	.metrics strong {
		display: block;
		font-family: var(--font-display);
		font-size: 1.85rem;
		font-variant-numeric: lining-nums tabular-nums;
		font-weight: var(--fw-display-strong);
		letter-spacing: -0.034em;
		line-height: 1;
	}

	.metrics span {
		color: var(--body-mid);
		font-size: 0.88rem;
	}

	.compact {
		margin-bottom: 2rem;
		max-width: 640px;
	}

	.compact table {
		min-width: 0;
	}

	.context mark {
		background: var(--primary-soft);
		border-radius: 4px;
		color: var(--accent-ink);
		padding: 0 0.18rem;
	}

	@media (max-width: 860px) {
		.tools-layout,
		.metrics {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.tools-layout {
			grid-template-columns: minmax(0, 1fr);
		}
	}
</style>
