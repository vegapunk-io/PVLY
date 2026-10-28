<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import PageHead from '#lib/components/PageHead.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';

	const notFound = $derived(page.status === 404);
</script>

<PageHead title={notFound ? 'Page not found' : 'Something went wrong'} noindex />

<div class="shell page error-page">
	<StateBlock
		kind="error"
		title={notFound ? 'We could not find that page.' : 'Something went wrong on our side.'}
		description={notFound
			? 'The link may be old or mistyped. You can scan a file or go back to the home page.'
			: 'Please try again in a moment. If it keeps happening, come back a little later.'}
	>
		<a class="btn" href={resolve('/scan')}>Scan a file</a>
		<a class="btn btn--secondary" href={resolve('/')}>Return home</a>
	</StateBlock>
</div>

<style>
	.error-page {
		max-width: 820px;
	}
</style>
