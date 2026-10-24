<script lang="ts">
	interface Props {
		title: string;
		description?: string;
		noindex?: boolean;
	}

	let {
		title,
		description = 'Detect content credentials, AI metadata and provenance signals with evidence-graded reports and honest coverage.',
		noindex = false
	}: Props = $props();

	const fullTitle = $derived(title === 'Provenably' ? title : `${title} — Provenably`);
</script>

<svelte:head>
	<title>{fullTitle}</title>
	<meta name="description" content={description} />
	<meta property="og:title" content={fullTitle} />
	<meta property="og:description" content={description} />
	<meta property="og:type" content="website" />
	{#if noindex}<meta name="robots" content="noindex, nofollow" />{/if}
</svelte:head>
