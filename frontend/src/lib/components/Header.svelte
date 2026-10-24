<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import BrandMark from './BrandMark.svelte';
	import Icon from './Icon.svelte';

	const primaryLinks = [
		{ href: '/scan', label: 'Scan' },
		{ href: '/remove', label: 'Remove' },
		{ href: '/batch', label: 'Batch' },
		{ href: '/presets', label: 'Presets' },
		{ href: '/registry', label: 'Registry' },
		{ href: '/rules', label: 'Rules' },
		{ href: '/pricing', label: 'Pricing' },
		{ href: '/api', label: 'API' }
	] as const;

	const mobileGroups = [
		{
			label: 'Product',
			links: [
				{ href: '/scan', label: 'Scan' },
				{ href: '/remove', label: 'Remove' },
				{ href: '/batch', label: 'Batch' },
				{ href: '/presets', label: 'Presets' }
			]
		},
		{
			label: 'Reference',
			links: [
				{ href: '/registry', label: 'Registry' },
				{ href: '/rules', label: 'Rules' },
				{ href: '/tools', label: 'Text tools' },
				{ href: '/lab', label: 'Lab' },
				{ href: '/api', label: 'API & status' }
			]
		},
		{
			label: 'Account',
			links: [
				{ href: '/history', label: 'History' },
				{ href: '/settings', label: 'Settings' },
				{ href: '/pricing', label: 'Pricing' },
				{ href: '/auth', label: 'Sign in' }
			]
		}
	] as const;

	function isCurrent(href: string): boolean {
		const path = page.url.pathname;
		return href === '/' ? path === '/' : path === href || path.startsWith(`${href}/`);
	}
</script>

<a class="skip-link" href="#main">Skip to main content</a>

<header class="site-header no-print">
	<div class="shell header__inner">
		<a
			class="brand"
			href={resolve('/')}
			aria-label="Provenably home"
			aria-current={isCurrent('/') ? 'page' : undefined}
		>
			<BrandMark size={44} decorative />
			<span class="brand__copy">
				<span class="brand__name">Provenably</span>
				<span class="brand__tagline">AI provenance &amp; metadata control</span>
			</span>
		</a>

		<nav class="desktop-nav" aria-label="Primary">
			{#each primaryLinks as link (link.href)}
				<a href={resolve(link.href)} aria-current={isCurrent(link.href) ? 'page' : undefined}
					>{link.label}</a
				>
			{/each}
		</nav>

		<div class="header__actions">
			<a href={resolve('/history')} aria-current={isCurrent('/history') ? 'page' : undefined}
				>History</a
			>
			<a href={resolve('/settings')} aria-current={isCurrent('/settings') ? 'page' : undefined}
				>Settings</a
			>
			<a class="btn btn--dark btn--small" href={resolve('/auth')}>Sign in</a>
		</div>

		<details class="mobile-nav">
			<summary><span>Menu</span><span class="menu-lines" aria-hidden="true"></span></summary>
			<div class="mobile-nav__panel">
				<nav aria-label="Mobile">
					{#each mobileGroups as group (group.label)}
						<section>
							<h2>{group.label}</h2>
							<ul>
								{#each group.links as link (link.href)}
									<li>
										<a
											href={resolve(link.href)}
											aria-current={isCurrent(link.href) ? 'page' : undefined}>{link.label}</a
										>
									</li>
								{/each}
							</ul>
						</section>
					{/each}
				</nav>
				<a class="btn btn--block" href={resolve('/scan')}
					>Scan a file <Icon name="arrow-right" size={18} /></a
				>
			</div>
		</details>
	</div>
</header>

<style>
	.site-header {
		background: rgb(255 254 251 / 96%);
		border-bottom: 1px solid var(--line);
		position: sticky;
		top: 0;
		z-index: 50;
	}

	@supports (backdrop-filter: blur(10px)) {
		.site-header {
			backdrop-filter: blur(10px);
		}
	}

	.header__inner {
		align-items: center;
		display: flex;
		gap: 1.4rem;
		min-height: var(--header-height);
		position: relative;
	}

	.brand {
		align-items: center;
		color: var(--ink);
		display: inline-flex;
		flex: 0 0 auto;
		gap: 0.7rem;
		min-height: 48px;
		text-decoration: none;
	}

	.brand:hover {
		color: var(--ink);
		text-decoration: none;
	}

	.brand__copy {
		display: grid;
		line-height: 1.05;
	}

	.brand__name {
		font-family: var(--font-display);
		font-size: 1.28rem;
		font-weight: 650;
		letter-spacing: -0.035em;
	}

	.brand__tagline {
		color: var(--body-mid);
		font-size: 0.72rem;
		margin-top: 0.18rem;
		white-space: nowrap;
	}

	.desktop-nav {
		align-items: center;
		display: flex;
		flex: 1;
		gap: 0.15rem;
		justify-content: center;
	}

	.desktop-nav a,
	.header__actions > a:not(.btn) {
		border-radius: 8px;
		color: var(--ink);
		font-size: 0.96rem;
		line-height: 1.2;
		padding: 0.62rem 0.55rem;
		text-decoration: none;
	}

	.desktop-nav a:hover,
	.header__actions > a:not(.btn):hover {
		background: var(--canvas-soft);
		color: var(--primary-hover);
	}

	.desktop-nav a[aria-current='page'],
	.header__actions > a[aria-current='page'] {
		color: var(--primary-hover);
		font-weight: 750;
	}

	.header__actions {
		align-items: center;
		display: flex;
		flex: 0 0 auto;
		gap: 0.2rem;
	}

	.header__actions .btn {
		margin-left: 0.45rem;
	}

	.mobile-nav {
		background: transparent;
		border: 0;
		display: none;
		margin: 0 0 0 auto;
		padding: 0;
	}

	.mobile-nav summary {
		border: 1px solid var(--ink);
		border-radius: 10px;
		font-size: 0.94rem;
		list-style: none;
		min-height: 44px;
		padding: 0.55rem 0.8rem;
	}

	.mobile-nav summary::-webkit-details-marker {
		display: none;
	}

	.mobile-nav summary::marker {
		content: '';
	}

	.menu-lines,
	.menu-lines::before,
	.menu-lines::after {
		background: currentColor;
		border-radius: 999px;
		display: block;
		height: 2px;
		position: relative;
		width: 18px;
	}

	.menu-lines::before,
	.menu-lines::after {
		content: '';
		position: absolute;
	}

	.menu-lines::before {
		top: -6px;
	}

	.menu-lines::after {
		top: 6px;
	}

	.mobile-nav__panel {
		background: var(--canvas);
		border: 1px solid var(--line);
		border-radius: 0 0 var(--radius) var(--radius);
		left: 0;
		max-height: calc(100dvh - var(--header-height));
		overflow: auto;
		padding: 1.2rem;
		position: absolute;
		right: 0;
		top: calc(100% + 1px);
	}

	.mobile-nav nav {
		display: grid;
		gap: 1.2rem;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		margin-bottom: 1.2rem;
	}

	.mobile-nav h2 {
		font-family: var(--font-sans);
		font-size: 0.8rem;
		font-weight: 750;
		letter-spacing: 0.08em;
		margin-bottom: 0.55rem;
		text-transform: uppercase;
	}

	.mobile-nav ul {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.mobile-nav li a {
		align-items: center;
		border-radius: 8px;
		color: var(--ink);
		display: flex;
		min-height: 44px;
		padding: 0.55rem 0.65rem;
		text-decoration: none;
	}

	.mobile-nav li a[aria-current='page'] {
		background: var(--primary-soft);
		color: var(--accent-ink);
		font-weight: 750;
	}

	@media (max-width: 1240px) {
		.brand__tagline {
			display: none;
		}
	}

	@media (max-width: 1080px) {
		.desktop-nav,
		.header__actions {
			display: none;
		}

		.mobile-nav {
			display: block;
		}
	}

	@media (max-width: 620px) {
		.mobile-nav nav {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
</style>
