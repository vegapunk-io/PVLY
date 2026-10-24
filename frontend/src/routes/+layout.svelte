<script lang="ts">
	import '#lib/hanken-grotesk-font.css';
	import '../app.css';
	import favicon from '#lib/assets/brand/provenably-mark.png';
	import Footer from '#lib/components/Footer.svelte';
	import Header from '#lib/components/Header.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} type="image/png" sizes="64x64" />
	<meta property="og:site_name" content="Provenably" />
</svelte:head>

<Header />
<main id="main" tabindex="-1">
	{@render children()}
</main>
<Footer />
