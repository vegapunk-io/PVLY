<script lang="ts">
	import '#lib/inter-font.css';
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import Footer from '#lib/components/Footer.svelte';
	import Header from '#lib/components/Header.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} type="image/svg+xml" />
	<meta property="og:site_name" content="Provenably" />
</svelte:head>

<Header />
<main id="main" tabindex="-1">
	{@render children()}
</main>
<Footer />
