<script lang="ts">
	import { resolve } from '$app/paths';
	import Icon from '#lib/components/Icon.svelte';
	import Notice from '#lib/components/Notice.svelte';
	import PageHead from '#lib/components/PageHead.svelte';
	import Tag from '#lib/components/Tag.svelte';

	interface PricingPlan {
		name: string;
		price: string;
		period: string;
		features: string[];
		cta: { label: string; href?: '/scan' | '/api'; disabled?: boolean };
		featured: boolean;
		badge?: string;
	}

	const plans: PricingPlan[] = [
		{
			name: 'Free',
			price: '$0',
			period: 'forever · no card',
			features: [
				'10 scans / month',
				'5 removals / month when R0 ships',
				'Images + text',
				'24-hour file retention'
			],
			cta: { label: 'Start free', href: '/scan' },
			featured: false
		},
		{
			name: 'Creator',
			price: '$9',
			period: '/ month',
			features: [
				'300 scans',
				'300 removals when available',
				'Image + audio + documents',
				'8 platform presets',
				'7-day retention'
			],
			cta: { label: 'Checkout opens with billing', disabled: true },
			featured: true,
			badge: 'For publishing workflows'
		},
		{
			name: 'Pro',
			price: '$29',
			period: '/ month',
			features: [
				'2,000 scans / removals',
				'Video included',
				'Batch up to 50 files',
				'ZIP + manifest in R3',
				'30-day retention',
				'Priority queue'
			],
			cta: { label: 'Checkout opens with billing', disabled: true },
			featured: false
		},
		{
			name: 'API / Teams',
			price: 'Usage',
			period: '$0.02 image · $0.15 video-minute',
			features: ['API keys & webhooks', 'Audit-trail export', 'Custom retention', 'SSO roadmap'],
			cta: { label: 'Explore the API', href: '/api' },
			featured: false
		}
	];
</script>

<PageHead
	title="Pricing"
	description="Simple scan and removal plans for creators, professionals and API teams—with graded reports, coverage and verified Layer-1 removal in every tier."
/>

<div class="shell page">
	<header class="page-head center pricing-head">
		<p class="eyebrow">Pricing</p>
		<h1>Pay for volume, not for honesty.</h1>
		<p class="lede">
			Every plan keeps the same evidence grades, coverage disclosure, before/after hashes and
			Layer-2 honesty. Paid tiers raise throughput, retention and automation—not the quality of the
			truth in a report.
		</p>
	</header>

	<Notice tone="info" title="Planning prices, billing not enabled yet">
		<p>
			These are the founder-approved wireframe’s placeholder tiers. Detect is available now; removal
			volume applies as R0–R3 endpoints ship. Checkout and account billing arrive with the
			auth/billing milestone, so paid buttons are disabled rather than pretending to charge a card.
		</p>
	</Notice>

	<section class="grid grid--4 pricing-grid" aria-label="Provenably plans">
		{#each plans as plan (plan.name)}
			<article class="price-card" class:featured={plan.featured}>
				{#if plan.badge}<Tag tone={plan.featured ? 'tag--accent' : ''}>{plan.badge}</Tag>{/if}
				<h2>{plan.name}</h2>
				<p class="price">{plan.price}</p>
				<p class="period">{plan.period}</p>
				<ul>
					{#each plan.features as feature (feature)}
						<li><Icon name="check" size={18} /><span>{feature}</span></li>
					{/each}
				</ul>
				{#if plan.cta.href}
					<a
						class="btn btn--block"
						class:btn--secondary={!plan.featured}
						href={resolve(plan.cta.href)}>{plan.cta.label}</a
					>
				{:else}
					<button class="btn btn--block" type="button" disabled>{plan.cta.label}</button>
				{/if}
			</article>
		{/each}
	</section>

	<section class="card included" aria-labelledby="included-title">
		<h2 id="included-title">Every plan includes</h2>
		<ul class="included__grid">
			<li><Icon name="shield" size={20} /> Graded provenance reports with visible coverage</li>
			<li>
				<Icon name="check" size={20} /> Lossless-first, verified Layer-1 removal as formats ship
			</li>
			<li><Icon name="file" size={20} /> Before/after hashes and machine-readable JSON</li>
			<li><Icon name="clock" size={20} /> Automatic file deletion and hash-only mode</li>
		</ul>
	</section>

	<section class="faq" aria-labelledby="faq-title">
		<div class="section-head">
			<p class="eyebrow">Questions</p>
			<h2 id="faq-title">The details that matter</h2>
		</div>
		<div class="faq__list">
			<details open>
				<summary>Does removal delete embedded watermarks such as SynthID?</summary>
				<p>
					No—and Provenably will never claim that it does. Removal is for Layer-1 container
					footprints. Embedded Layer-2 marks are detected or marked “not checked” according to the
					connectors configured in the deployment.
				</p>
			</details>
			<details>
				<summary>Is removing metadata legal?</summary>
				<p>
					Removing GPS, device, author and other metadata from your own files is a normal privacy
					action. It does not remove synthetic-content disclosure obligations. Reports pair
					technical findings with jurisdiction notes, but they are not legal advice.
				</p>
			</details>
			<details>
				<summary>What happens to my files?</summary>
				<p>
					Files are deleted at the retention expiry for the deployment or plan. Hash-only scans
					delete bytes right after analysis and keep only the hash and findings needed for the
					report.
				</p>
			</details>
			<details>
				<summary>Why can I use Detect before paid checkout exists?</summary>
				<p>
					The current deployment is the production frontend and Detect API foundation. Accounts,
					quotas, payments and per-user history ship together so billing is never attached to an
					anonymous shared history.
				</p>
			</details>
		</div>
	</section>
</div>

<style>
	.pricing-head {
		margin-inline: auto;
		text-align: center;
	}

	.pricing-head .lede {
		margin-inline: auto;
	}

	.pricing-grid {
		align-items: stretch;
		margin-top: 2rem;
	}

	.price-card {
		background: var(--canvas);
		border: 1px solid var(--ink);
		border-radius: var(--radius);
		display: flex;
		flex-direction: column;
		padding: 1.5rem;
	}

	.price-card.featured {
		background: var(--ink);
		color: var(--canvas-soft);
	}

	.price-card h2 {
		font-size: 1.35rem;
		margin-top: 1rem;
	}

	.price-card.featured h2,
	.price-card.featured .price {
		color: var(--on-primary);
	}

	.price-card.featured :global(.tag--accent) {
		background: var(--primary);
		border-color: var(--primary);
		color: var(--on-primary);
	}

	.price {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 2.6rem;
		font-weight: 560;
		letter-spacing: -0.04em;
		line-height: 1;
		margin-bottom: 0.35rem;
	}

	.period {
		color: var(--body-mid);
		min-height: 3.2rem;
	}

	.price-card.featured .period {
		color: #d8d2c4;
	}

	.price-card ul {
		display: grid;
		gap: 0.65rem;
		list-style: none;
		margin: 0 0 1.6rem;
		padding: 0;
	}

	.price-card li {
		align-items: flex-start;
		display: flex;
		gap: 0.55rem;
		line-height: 1.45;
	}

	.price-card li :global(svg) {
		color: var(--primary-hover);
		margin-top: 0.16rem;
	}

	.price-card.featured li :global(svg) {
		color: var(--primary-line);
	}

	.price-card .btn {
		margin-top: auto;
	}

	.included {
		margin-top: 1.2rem;
	}

	.included__grid {
		display: grid;
		gap: 1rem;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		list-style: none;
		margin: 1rem 0 0;
		padding: 0;
	}

	.included__grid li {
		align-items: flex-start;
		color: var(--ink-mid);
		display: flex;
		gap: 0.6rem;
	}

	.included__grid :global(svg) {
		color: var(--primary-hover);
		margin-top: 0.15rem;
	}

	.faq {
		margin-top: clamp(3rem, 7vw, 5rem);
	}

	.faq__list {
		margin-inline: auto;
		max-width: 880px;
	}

	@media (max-width: 900px) {
		.included__grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 600px) {
		.included__grid {
			grid-template-columns: 1fr;
		}

		.period {
			min-height: 0;
		}
	}
</style>
