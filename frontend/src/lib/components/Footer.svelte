<script lang="ts">
	import { resolve } from '$app/paths';
	import BrandMark from './BrandMark.svelte';

	const year = new Date().getFullYear();
</script>

<footer class="site-footer no-print">
	<div class="shell">
		<div class="footer__grid">
			<div class="footer__brand">
				<a class="footer__logo" href={resolve('/')}>
					<BrandMark size={40} decorative />
					Provenably
				</a>
				<p>
					Detect content credentials and AI footprints, understand the removable Layer-1 metadata,
					and report embedded Layer-2 signals honestly—before you publish.
				</p>
				<p class="footer__status">
					<span class="dot dot--ok" aria-hidden="true"></span> Detect is live; removal, batch and presets
					follow the published roadmap.
				</p>
			</div>

			<nav aria-label="Product">
				<h2>Product</h2>
				<ul>
					<li><a href={resolve('/scan')}>Scan</a></li>
					<li><a href={resolve('/remove')}>Remove</a></li>
					<li><a href={resolve('/batch')}>Batch</a></li>
					<li><a href={resolve('/presets')}>Platform presets</a></li>
					<li><a href={resolve('/history')}>History</a></li>
				</ul>
			</nav>

			<nav aria-label="Reference">
				<h2>Reference</h2>
				<ul>
					<li><a href={resolve('/registry')}>Generator registry</a></li>
					<li><a href={resolve('/rules')}>Disclosure rules</a></li>
					<li><a href={resolve('/tools')}>Text tools</a></li>
					<li><a href={resolve('/lab')}>Watermark lab</a></li>
					<li><a href={resolve('/design-system')}>Design system</a></li>
				</ul>
			</nav>

			<nav aria-label="Developers and account">
				<h2>Developers</h2>
				<ul>
					<li><a href={resolve('/api')}>API &amp; status</a></li>
					<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- FastAPI path outside the Svelte route manifest. -->
					<li><a href="/api/docs" rel="external" data-sveltekit-reload>OpenAPI</a></li>
					<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -- FastAPI path outside the Svelte route manifest. -->
					<li><a href="/health" rel="external" data-sveltekit-reload>Health check</a></li>
					<li><a href={resolve('/settings')}>Settings &amp; API key</a></li>
					<li><a href={resolve('/pricing')}>Pricing</a></li>
				</ul>
			</nav>
		</div>

		<div class="footer__legal">
			<p>
				© {year} Provenably. Reports describe signals and evidence grades; they are not a verdict on authorship.
			</p>
			<p>Rule summaries are researched, dated and confidence-graded. They are not legal advice.</p>
		</div>
	</div>
</footer>

<style>
	.site-footer {
		background: var(--ink);
		color: #d8d2c4;
		padding: clamp(2.8rem, 6vw, 4.5rem) 0 2rem;
	}

	.footer__grid {
		display: grid;
		gap: 2rem;
		grid-template-columns: 2fr 1fr 1fr 1fr;
	}

	.footer__brand p {
		max-width: 460px;
	}

	.footer__logo {
		align-items: center;
		color: var(--on-primary);
		display: inline-flex;
		font-family: var(--font-display);
		font-size: 1.3rem;
		font-weight: 650;
		gap: 0.65rem;
		margin-bottom: 1rem;
		text-decoration: none;
	}

	.footer__status {
		align-items: center;
		display: flex;
		font-size: 0.9rem;
		gap: 0.55rem;
	}

	.site-footer h2 {
		color: var(--on-primary);
		font-family: var(--font-sans);
		font-size: 0.9rem;
		font-weight: 750;
		letter-spacing: 0.06em;
		margin-bottom: 0.8rem;
		text-transform: uppercase;
	}

	.site-footer ul {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.site-footer li {
		margin: 0.2rem 0;
	}

	.site-footer nav a {
		align-items: center;
		color: #e9e2d5;
		display: inline-flex;
		min-height: 38px;
		text-decoration: none;
	}

	.site-footer nav a:hover,
	.footer__logo:hover {
		color: #fff;
		text-decoration: underline;
	}

	.footer__legal {
		border-top: 1px solid #453d38;
		display: flex;
		flex-wrap: wrap;
		font-size: 0.88rem;
		gap: 0.5rem 2rem;
		justify-content: space-between;
		margin-top: 2.5rem;
		padding-top: 1.3rem;
	}

	.footer__legal p {
		margin: 0;
	}

	@media (max-width: 900px) {
		.footer__grid {
			grid-template-columns: 1fr 1fr;
		}
	}

	@media (max-width: 560px) {
		.footer__grid {
			grid-template-columns: 1fr;
		}
	}
</style>
