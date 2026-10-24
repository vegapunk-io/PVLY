<script lang="ts">
	import type { Snippet } from 'svelte';
	import Icon from './Icon.svelte';

	type Tone = 'warning' | 'info' | 'error' | 'success';

	interface Props {
		tone?: Tone;
		title?: string;
		children: Snippet;
	}

	let { tone = 'warning', title, children }: Props = $props();
	const className = $derived(tone === 'warning' ? 'notice' : `notice notice--${tone}`);
	const icon = $derived(tone === 'success' ? 'check' : tone === 'info' ? 'info' : 'alert');
	const role = $derived(tone === 'error' ? 'alert' : 'note');
</script>

<div class={className} {role}>
	<div class="notice__layout">
		<span class="notice__icon"><Icon name={icon} size={18} /></span>
		<div class="notice__content">
			{#if title}<p class="notice__title"><strong>{title}</strong></p>{/if}
			{@render children()}
		</div>
	</div>
</div>

<style>
	.notice__layout {
		align-items: flex-start;
		display: flex;
		gap: 0.85rem;
	}

	.notice__icon {
		align-items: center;
		background: var(--notice-icon-surface, var(--canvas));
		border: 1px solid var(--line);
		border-radius: 9px;
		color: var(--notice-accent, var(--ink));
		display: inline-flex;
		flex: 0 0 auto;
		height: 2rem;
		justify-content: center;
		line-height: 0;
		width: 2rem;
	}

	.notice__content {
		min-width: 0;
	}

	.notice__title {
		margin-bottom: 0.3rem;
	}

	.notice__layout :global(p:last-child) {
		margin-bottom: 0;
	}
</style>
