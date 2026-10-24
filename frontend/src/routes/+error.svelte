<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import PageHead from '#lib/components/PageHead.svelte';
	import StateBlock from '#lib/components/StateBlock.svelte';
</script>

<PageHead title={page.status === 404 ? 'Page not found' : 'Something went wrong'} noindex />

<div class="shell page error-page">
	<StateBlock
		kind="error"
		title={page.status === 404 ? 'We could not find that page.' : 'This page could not be loaded.'}
		description={page.error?.message ??
			'The address may have changed, or the deployment may be temporarily unavailable.'}
	>
		<a class="btn" href={resolve('/scan')}>Scan a file</a>
		<a class="btn btn--secondary" href={resolve('/')}>Return home</a>
	</StateBlock>
	<p class="small muted center">HTTP {page.status}</p>
</div>

<style>
	.error-page {
		max-width: 820px;
	}

	.error-page > p {
		margin-top: 1rem;
	}
</style>
