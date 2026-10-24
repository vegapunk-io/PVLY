<script lang="ts">
	import type { Snippet } from 'svelte';
	import Icon from './Icon.svelte';

	interface Props {
		kind?: 'empty' | 'loading' | 'error';
		title: string;
		description?: string;
		children?: Snippet;
	}

	let { kind = 'empty', title, description, children }: Props = $props();
</script>

<div
	class="empty-state"
	role={kind === 'error' ? 'alert' : 'status'}
	aria-live={kind === 'loading' ? 'polite' : undefined}
	aria-busy={kind === 'loading'}
>
	{#if kind === 'loading'}
		<span class="spinner" aria-hidden="true"></span>
	{:else}
		<span class="state-icon"><Icon name={kind === 'error' ? 'alert' : 'file'} size={26} /></span>
	{/if}
	<h2>{title}</h2>
	{#if description}<p>{description}</p>{/if}
	{#if children}<div class="actions center-actions">{@render children()}</div>{/if}
</div>

<style>
	.empty-state h2 {
		font-size: 1.45rem;
		margin-top: 0.9rem;
	}

	.state-icon {
		align-items: center;
		background: var(--canvas);
		border: 1px solid var(--line);
		border-radius: 50%;
		color: var(--primary-hover);
		display: inline-flex;
		height: 3.25rem;
		justify-content: center;
		width: 3.25rem;
	}

	.spinner {
		height: 1.7rem;
		width: 1.7rem;
	}

	.center-actions {
		justify-content: center;
		margin-top: 1.2rem;
	}
</style>
