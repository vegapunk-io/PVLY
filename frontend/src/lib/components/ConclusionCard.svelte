<script lang="ts">
	import { formatDuration, gradeTone } from '../format';
	import type { Conclusion, Coverage } from '../types';
	import Tag from './Tag.svelte';

	interface Props {
		conclusion: Conclusion;
		coverage?: Coverage;
		durationMs?: number;
	}

	let { conclusion, coverage, durationMs }: Props = $props();
	const isTampered = $derived(conclusion.provenance_class === 'tampered_after_signing');
</script>

<section class="conclusion" aria-labelledby="report-conclusion-title">
	<div class="conclusion__header">
		<div>
			<p class="eyebrow">Provenance conclusion</p>
			<h2 class="conclusion__label" id="report-conclusion-title">{conclusion.label}</h2>
		</div>
		<div class="conclusion__tags" aria-label="Conclusion classification">
			<Tag tone={isTampered ? 'tag--tampered' : 'tag--manual'}>
				{isTampered ? 'tampered' : conclusion.provenance_class}
			</Tag>
			<Tag tone={gradeTone(conclusion.evidence_grade)}>evidence: {conclusion.evidence_grade}</Tag>
		</div>
	</div>

	{#if conclusion.decisive_signal}
		<p class="small"><strong>Decisive signal:</strong> {conclusion.decisive_signal}</p>
	{/if}

	{#each conclusion.notes as note (note)}
		<p>{note}</p>
	{/each}

	{#if coverage}
		<p class="small muted conclusion__coverage">
			Coverage: {coverage.live} live checks ran · {coverage.manual} modules require manual integration
			· {coverage.errors}
			errors{#if durationMs !== undefined}
				· completed in {formatDuration(durationMs)}{/if}.
		</p>
	{/if}
</section>

<style>
	.conclusion__header {
		align-items: flex-start;
		border-bottom: 1px solid var(--line);
		display: flex;
		gap: 1rem;
		justify-content: space-between;
		margin-bottom: 1rem;
		padding-bottom: 1rem;
	}

	.conclusion__header .eyebrow {
		margin-bottom: 0.4rem;
	}

	.conclusion__label {
		margin: 0;
	}

	.conclusion__tags {
		display: flex;
		flex: 0 0 auto;
		flex-wrap: wrap;
		gap: 0.45rem;
		justify-content: flex-end;
	}

	.conclusion__coverage {
		border-top: 1px solid var(--line);
		margin: 1rem 0 0;
		padding-top: 0.9rem;
	}

	@media (max-width: 680px) {
		.conclusion__header {
			display: grid;
		}

		.conclusion__tags {
			justify-content: flex-start;
		}
	}
</style>
