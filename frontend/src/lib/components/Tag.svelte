<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		tone?: string;
		children: Snippet;
	}

	let { tone = '', children }: Props = $props();
</script>

<span class={`tag ${tone}`}>{@render children()}</span>
