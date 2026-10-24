<script lang="ts">
	import { resolve } from '$app/paths';
	import { tick } from 'svelte';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import Tabs, { type TabItem } from '#lib/components/Tabs.svelte';

	const tabs: TabItem[] = [
		{ id: 'signin', label: 'Sign in' },
		{ id: 'signup', label: 'Create account' }
	];

	let activeTab = $state('signin');
	let signInEmail = $state('');
	let signInPassword = $state('');
	let signUpName = $state('');
	let signUpEmail = $state('');
	let signUpPassword = $state('');
	let acceptedTerms = $state(false);
	let submitted = $state(false);
	let noticeRegion: HTMLDivElement | undefined = $state();

	async function submitAuth(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		// Accounts are not enabled in this deployment. Passwords are intentionally not sent,
		// logged or persisted; clear them as soon as the unavailable state is shown.
		signInPassword = '';
		signUpPassword = '';
		submitted = true;
		await tick();
		noticeRegion?.focus();
	}
</script>

<PageHead
	title="Sign in"
	description="Accounts will add private history, managed API keys and higher limits. Anonymous Detect scans remain available in this deployment."
	noindex
/>

<div class="shell shell--narrow page auth-page">
	<header class="page-head center auth-head">
		<p class="eyebrow">Account</p>
		<h1>Sign in to Provenably</h1>
		<p class="lede">
			Private history, managed API keys, billing and higher limits arrive with the identity
			milestone.
		</p>
	</header>

	<section class="card card--canvas auth-card" aria-labelledby="auth-title">
		<h2 class="visually-hidden" id="auth-title">Account access</h2>
		<Tabs idPrefix="auth" items={tabs} bind:active={activeTab} label="Account action" />

		{#if submitted}
			<div class="auth-notice" bind:this={noticeRegion} tabindex="-1">
				<Notice tone="info" title="Accounts are not enabled in this deployment yet">
					<p>
						No credentials were sent or stored. Continue with anonymous Detect, or configure a
						deployment API key for this browser session in Settings.
					</p>
					<div class="actions">
						<a class="btn btn--small" href={resolve('/scan')}>Continue to Scan</a>
						<a class="btn btn--secondary btn--small" href={resolve('/settings')}>Open Settings</a>
					</div>
				</Notice>
			</div>
		{/if}

		<div
			id="auth-panel-signin"
			role="tabpanel"
			aria-labelledby="auth-tab-signin"
			tabindex="0"
			hidden={activeTab !== 'signin'}
		>
			<form onsubmit={submitAuth}>
				<div class="field">
					<label for="signin-email">Email</label>
					<input
						id="signin-email"
						type="email"
						bind:value={signInEmail}
						autocomplete="email"
						required
					/>
				</div>
				<div class="field">
					<label for="signin-password">Password</label>
					<input
						id="signin-password"
						type="password"
						bind:value={signInPassword}
						autocomplete="current-password"
						required
					/>
				</div>
				<button class="btn btn--block" type="submit">Sign in</button>
				<p class="small muted">
					Password recovery will be provided by the selected identity provider.
				</p>
			</form>
		</div>

		<div
			id="auth-panel-signup"
			role="tabpanel"
			aria-labelledby="auth-tab-signup"
			tabindex="0"
			hidden={activeTab !== 'signup'}
		>
			<form onsubmit={submitAuth}>
				<div class="field">
					<label for="signup-name">Name</label>
					<input
						id="signup-name"
						type="text"
						bind:value={signUpName}
						autocomplete="name"
						required
					/>
				</div>
				<div class="field">
					<label for="signup-email">Email</label>
					<input
						id="signup-email"
						type="email"
						bind:value={signUpEmail}
						autocomplete="email"
						required
					/>
				</div>
				<div class="field">
					<label for="signup-password">Password</label>
					<input
						id="signup-password"
						type="password"
						bind:value={signUpPassword}
						autocomplete="new-password"
						minlength="12"
						required
						aria-describedby="password-hint"
					/>
					<p class="field-hint" id="password-hint">
						Use at least 12 characters when accounts are enabled.
					</p>
				</div>
				<label class="check">
					<input type="checkbox" bind:checked={acceptedTerms} required />
					<span
						>I agree to the future Terms and Privacy Policy presented by the production identity
						provider.</span
					>
				</label>
				<button class="btn btn--block" type="submit">Create free account</button>
			</form>
		</div>

		<div class="divider-row" aria-hidden="true"><span></span>or<span></span></div>

		<button class="btn btn--secondary btn--block" type="button" disabled>
			Continue with Google — identity provider pending
		</button>
	</section>

	<section class="card anonymous-card">
		<div>
			<h2>No account needed for Detect</h2>
			<p>
				Anonymous scans stay available. An account will make history private rather than
				deployment-wide and will unlock managed keys and quotas.
			</p>
		</div>
		<a class="btn btn--dark" href={resolve('/scan')}
			>Scan anonymously <Icon name="arrow-right" size={18} /></a
		>
	</section>
</div>

<style>
	.auth-page {
		max-width: 720px;
	}

	.auth-head {
		margin-inline: auto;
		text-align: center;
	}

	.auth-head .lede {
		margin-inline: auto;
	}

	.auth-card {
		padding: clamp(1.4rem, 4vw, 2.2rem);
	}

	.auth-notice {
		margin-bottom: 1.2rem;
		outline-offset: 4px;
	}

	.divider-row {
		align-items: center;
		color: var(--body-mid);
		display: flex;
		gap: 1rem;
		margin: 1.4rem 0;
	}

	.divider-row span {
		background: var(--line);
		flex: 1;
		height: 1px;
	}

	.anonymous-card {
		align-items: center;
		display: flex;
		gap: 1.5rem;
		justify-content: space-between;
		margin-top: 1rem;
	}

	[role='tabpanel'][hidden] {
		display: none;
	}

	@media (max-width: 640px) {
		.anonymous-card {
			align-items: stretch;
			flex-direction: column;
		}
	}
</style>
