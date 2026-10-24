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
		<span class="notice__icon"><Icon name={icon} size={20} /></span>
		<div>
			{#if title}<p class="notice__title"><strong>{title}</strong></p>{/if}
			{@render children()}
		</div>
	</div>
</div>

<style>
	.notice__layout {
		display: flex;
		gap: 0.8rem;
	}

	.notice__icon {
		color: var(--ink);
		line-height: 0;
		margin-top: 0.12rem;
	}

	.notice__title {
		margin-bottom: 0.3rem;
	}

	.notice__layout :global(p:last-child) {
		margin-bottom: 0;
	}
</style>
