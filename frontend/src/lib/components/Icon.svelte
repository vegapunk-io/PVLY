<script lang="ts">
	type IconName =
		| 'arrow-right'
		| 'check'
		| 'upload'
		| 'file'
		| 'shield'
		| 'scan'
		| 'layers'
		| 'download'
		| 'external'
		| 'alert'
		| 'info'
		| 'search'
		| 'clock'
		| 'x';

	interface Props {
		name: IconName;
		size?: number;
		label?: string;
		class?: string;
	}

	let { name, size = 20, label, class: className = '' }: Props = $props();

	interface Glyph {
		paths: string[];
		circles?: Array<{ cx: number; cy: number; r: number }>;
	}

	const glyphs: Record<IconName, Glyph> = {
		'arrow-right': { paths: ['M4 12h15m-6-7 7 7-7 7'] },
		check: { paths: ['m4.5 12.5 5 5L19.5 6.5'] },
		upload: {
			paths: [
				'M12 16V4m0 0 4.5 4.5M12 4 7.5 8.5',
				'M4 16v3.5A1.5 1.5 0 0 0 5.5 21h13A1.5 1.5 0 0 0 20 19.5V16'
			]
		},
		file: {
			paths: ['M6 3h8l4 4v14H6Z', 'M14 3v4h4M9 13h6M9 17h6']
		},
		shield: {
			paths: ['M12 3 5 5.5v5c0 4.5 3 8.4 7 10 4-1.6 7-5.5 7-10v-5Z', 'm8.8 12 2.2 2.2 4.2-4.4']
		},
		scan: {
			paths: [
				'M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8m8 0h2.5A1.5 1.5 0 0 1 20 5.5V8m0 8v2.5a1.5 1.5 0 0 1-1.5 1.5H16m-8 0H5.5A1.5 1.5 0 0 1 4 18.5V16',
				'M4 12h16'
			]
		},
		layers: {
			paths: ['m12 3 9 5-9 5-9-5Z', 'm3 13 9 5 9-5']
		},
		download: {
			paths: [
				'M12 4v12m0 0 4.5-4.5M12 16 7.5 11.5',
				'M4 16v3.5A1.5 1.5 0 0 0 5.5 21h13A1.5 1.5 0 0 0 20 19.5V16'
			]
		},
		external: {
			paths: ['M10 5H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-4', 'M14 4h6v6m0-6L11 13']
		},
		alert: {
			paths: ['M12 4 2.8 20h18.4Z', 'M12 9v5m0 3v.1']
		},
		info: {
			paths: ['M12 11v5m0-8v.1'],
			circles: [{ cx: 12, cy: 12, r: 9 }]
		},
		search: {
			paths: ['m16 16 5 5'],
			circles: [{ cx: 11, cy: 11, r: 6 }]
		},
		clock: {
			paths: ['M12 7v5l3.5 2'],
			circles: [{ cx: 12, cy: 12, r: 9 }]
		},
		x: { paths: ['m6 6 12 12M18 6 6 18'] }
	};

	const glyph = $derived(glyphs[name]);
</script>

<svg
	class={className}
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	stroke="currentColor"
	stroke-width="1.8"
	stroke-linecap="round"
	stroke-linejoin="round"
	role={label ? 'img' : undefined}
	aria-label={label}
	aria-hidden={label ? undefined : 'true'}
	focusable="false"
>
	{#each glyph.circles ?? [] as circle (circle.cx)}
		<circle cx={circle.cx} cy={circle.cy} r={circle.r} />
	{/each}
	{#each glyph.paths as d (d)}
		<path {d} />
	{/each}
</svg>

<style>
	svg {
		flex: 0 0 auto;
	}
</style>
