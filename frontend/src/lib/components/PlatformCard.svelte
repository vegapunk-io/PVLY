<script lang="ts">
	import type { ResolvedPathname } from '$app/types';
	import { platformLabel } from '../data/platform-labels';
	import type { PresetDefinition } from '../data/presets';
	import Icon from './Icon.svelte';
	import PlatformMark from './PlatformMark.svelte';

	interface Props {
		preset: PresetDefinition;
		selected?: boolean;
		href?: ResolvedPathname;
		onselect?: (preset: PresetDefinition) => void;
	}

	let { preset, selected = false, href, onselect }: Props = $props();
	const interactive = $derived(Boolean(onselect || href));
	const label = $derived(platformLabel(preset.slug));
</script>

{#snippet content()}
	<span class="platform-card__head">
		<PlatformMark slug={preset.slug} name={preset.name} size={48} />
		<span class="platform-card__heading">
			<span class="platform-card__name">{preset.name}</span>
			<span class="platform-card__meta">{preset.media} · {preset.formats}</span>
		</span>
	</span>
	<span class="platform-card__output">{preset.output}</span>
	<span class="platform-card__label-box">
		<span class="platform-card__label-top">
			<span class="platform-card__label-caption">Platform label</span>
			<span class={`platform-card__label platform-card__label--${label.labelKind}`}
				>{label.labelDisplay}</span
			>
		</span>
		<span class="platform-card__label-subtext">{label.labelSubtext}</span>
		<span class="platform-card__signals">{label.signalSummary}</span>
	</span>
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
		gap: 0.65rem;
		height: 100%;
		min-height: 272px;
		padding: 1.15rem;
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
		gap: 0.8rem;
	}

	.platform-card__heading {
		display: flex;
		flex-direction: column;
		gap: 0.12rem;
		min-width: 0;
	}

	.platform-card__name {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.16rem;
		font-weight: 600;
		letter-spacing: -0.025em;
		line-height: 1.15;
	}

	.platform-card__meta {
		color: var(--accent-ink);
		font-size: 0.8rem;
		font-weight: 700;
		line-height: 1.35;
	}

	.platform-card__output {
		color: var(--ink-mid);
		line-height: 1.45;
	}

	.platform-card__label-box {
		border-top: 1px solid var(--line);
		display: flex;
		flex-direction: column;
		gap: 0.38rem;
		margin-top: auto;
		padding-top: 0.8rem;
	}

	.platform-card__label-top {
		align-items: flex-start;
		display: flex;
		flex-wrap: wrap;
		gap: 0.45rem 0.6rem;
		justify-content: space-between;
	}

	.platform-card__label-caption {
		color: var(--ink);
		font-size: 0.78rem;
		font-weight: 750;
		padding-top: 0.18rem;
	}

	.platform-card__label {
		background: var(--canvas);
		border: 1px solid var(--mute);
		border-radius: 999px;
		color: var(--ink);
		font-size: 0.78rem;
		font-weight: 750;
		line-height: 1.25;
		padding: 0.22rem 0.5rem;
	}

	.platform-card__label--none,
	.platform-card__label--private {
		background: transparent;
		border-style: dashed;
		color: var(--ink-mid);
	}

	.platform-card__label--provenance {
		border-color: var(--accent-ink);
	}

	.platform-card__label-subtext {
		font-size: 0.86rem;
		line-height: 1.45;
	}

	.platform-card__signals {
		color: var(--accent-ink);
		font-size: 0.78rem;
		font-weight: 650;
		line-height: 1.4;
	}

	.platform-card__action {
		align-items: center;
		color: var(--primary-hover);
		display: inline-flex;
		font-size: 0.9rem;
		font-weight: 720;
		gap: 0.35rem;
		padding-top: 0.2rem;
	}
</style>
