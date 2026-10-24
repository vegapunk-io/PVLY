<script lang="ts">
	import mark from '#lib/assets/brand/provenably-mark.png';

	interface Props {
		size?: number;
		decorative?: boolean;
	}

	let { size = 40, decorative = false }: Props = $props();
</script>

<img
	class="brand-mark"
	src={mark}
	width={size}
	height={size}
	alt={decorative ? '' : 'Provenably logo'}
	aria-hidden={decorative ? 'true' : undefined}
	decoding="async"
	style={`--brand-mark-size: ${size}px`}
/>

<style>
	.brand-mark {
		display: block;
		flex: 0 0 auto;
		height: var(--brand-mark-size);
		object-fit: contain;
		width: var(--brand-mark-size);
	}
</style>
