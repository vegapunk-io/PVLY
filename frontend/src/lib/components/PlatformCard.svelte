<script lang="ts">
	import type { ResolvedPathname } from '$app/types';
	import type { PresetDefinition } from '../data/presets';
	import Icon from './Icon.svelte';

	interface Props {
		preset: PresetDefinition;
		selected?: boolean;
		href?: ResolvedPathname;
		onselect?: (preset: PresetDefinition) => void;
	}

	let { preset, selected = false, href, onselect }: Props = $props();
	const interactive = $derived(Boolean(onselect || href));
</script>

{#snippet content()}
	<span class="platform-card__head">
		<span class="platform-card__name">{preset.name}</span>
		<span class="platform-card__initial" aria-hidden="true">{preset.initial}</span>
	</span>
	<span class="platform-card__meta">{preset.media} · {preset.formats}</span>
	<span class="platform-card__output">{preset.output}</span>
	<span class="platform-card__note"><strong>Label note:</strong> {preset.labelNote}</span>
	{#if interactive}
		<span class="platform-card__action"
			>{selected ? 'Selected' : 'Choose preset'} <Icon name="arrow-right" size={16} /></span
		>
	{/if}
{/snippet}

{#if onselect}
	<button
		class="platform-card"
		class:selected
		type="button"
		aria-pressed={selected}
		onclick={() => onselect(preset)}
	>
		{@render content()}
	</button>
{:else if href}
	<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- href is typed as ResolvedPathname by the caller. -->
	<a class="platform-card" class:selected {href}>{@render content()}</a>
{:else}
	<article class="platform-card" class:selected>{@render content()}</article>
{/if}

<style>
	.platform-card {
		background: var(--canvas-soft);
		border: 2px solid transparent;
		border-radius: var(--radius);
		color: var(--body);
		display: flex;
		flex-direction: column;
		font: inherit;
		gap: 0.42rem;
		height: 100%;
		min-height: 190px;
		padding: 1.2rem;
		text-align: left;
		text-decoration: none;
		width: 100%;
	}

	button.platform-card {
		cursor: pointer;
	}

	button.platform-card:hover,
	a.platform-card:hover {
		border-color: var(--mute);
		color: var(--body);
		text-decoration: none;
	}

	.platform-card.selected {
		background: var(--canvas);
		border-color: var(--primary);
	}

	.platform-card__head {
		align-items: center;
		display: flex;
		gap: 1rem;
		justify-content: space-between;
	}

	.platform-card__name {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.18rem;
		font-weight: 600;
		letter-spacing: -0.025em;
	}

	.platform-card__initial {
		align-items: center;
		background: var(--primary);
		border-radius: 50%;
		color: var(--on-primary);
		display: inline-flex;
		flex: 0 0 auto;
		font-weight: 800;
		height: 2.25rem;
		justify-content: center;
		width: 2.25rem;
	}

	.platform-card__meta {
		color: var(--accent-ink);
		font-size: 0.86rem;
		font-weight: 700;
	}

	.platform-card__output {
		color: var(--ink-mid);
		line-height: 1.45;
	}

	.platform-card__note {
		font-size: 0.9rem;
		line-height: 1.45;
	}

	.platform-card__action {
		align-items: center;
		color: var(--primary-hover);
		display: inline-flex;
		font-size: 0.9rem;
		font-weight: 720;
		gap: 0.35rem;
		margin-top: auto;
		padding-top: 0.65rem;
	}
</style>
