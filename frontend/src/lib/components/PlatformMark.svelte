<script lang="ts">
	import facebookMark from '../assets/platforms/facebook.webp';
	import instagramMark from '../assets/platforms/instagram.webp';
	import linkedinMark from '../assets/platforms/linkedin.webp';
	import pinterestMark from '../assets/platforms/pinterest.webp';
	import redditMark from '../assets/platforms/reddit.webp';
	import tiktokMark from '../assets/platforms/tiktok.webp';
	import xMark from '../assets/platforms/x.webp';
	import youtubeMark from '../assets/platforms/youtube.webp';

	interface Props {
		slug: string;
		name?: string;
		size?: number;
		class?: string;
	}

	let { slug, name = '', size = 44, class: className = '' }: Props = $props();

	const suppliedMarks: Record<string, string> = {
		facebook: facebookMark,
		instagram: instagramMark,
		linkedin: linkedinMark,
		pinterest: pinterestMark,
		reddit: redditMark,
		tiktok: tiktokMark,
		x: xMark,
		youtube: youtubeMark
	};

	const fallbackGlyphs: Record<string, string> = {
		amazon_kdp: 'a',
		generic: 'G',
		google_search: 'G',
		threads: '@',
		tiktok: '♪',
		x: 'X'
	};

	const mark = $derived(suppliedMarks[slug]);
	const glyph = $derived(fallbackGlyphs[slug] ?? (name.trim().charAt(0).toUpperCase() || '•'));
</script>

<span
	class={`platform-mark platform-mark--${slug} ${className}`}
	style={`--platform-mark-size: ${size}px`}
	aria-hidden="true"
>
	{#if mark}
		<img src={mark} alt="" width={size} height={size} loading="lazy" decoding="async" />
	{:else}
		<span class="platform-mark__fallback">{glyph}</span>
	{/if}
</span>

<style>
	.platform-mark {
		align-items: center;
		display: inline-flex;
		flex: 0 0 auto;
		height: var(--platform-mark-size);
		justify-content: center;
		line-height: 0;
		width: var(--platform-mark-size);
	}

	.platform-mark img {
		display: block;
		height: 100%;
		object-fit: contain;
		width: 100%;
	}

	.platform-mark__fallback {
		align-items: center;
		background: var(--canvas-soft);
		border: 1px solid var(--line);
		border-radius: 28%;
		color: var(--ink);
		display: inline-flex;
		font-size: calc(var(--platform-mark-size) * 0.54);
		font-weight: var(--fw-bold);
		height: 100%;
		justify-content: center;
		line-height: 1;
		width: 100%;
	}

	.platform-mark--tiktok .platform-mark__fallback {
		background: #111111;
		border-color: #111111;
		color: #ffffff;
		text-shadow:
			-0.055em 0 #25f4ee,
			0.055em 0 #fe2c55;
	}

	.platform-mark--x .platform-mark__fallback,
	.platform-mark--threads .platform-mark__fallback {
		background: #000000;
		border-color: #000000;
		color: #ffffff;
	}

	.platform-mark--threads .platform-mark__fallback {
		border-radius: 50%;
		font-size: calc(var(--platform-mark-size) * 0.48);
	}

	.platform-mark--google_search .platform-mark__fallback {
		background: var(--canvas);
		color: #4285f4;
	}

	.platform-mark--amazon_kdp .platform-mark__fallback {
		background: #232f3e;
		border-color: #232f3e;
		color: #ff9900;
	}

	.platform-mark--generic .platform-mark__fallback {
		background: var(--primary);
		border-color: var(--primary);
		color: var(--on-primary);
	}
</style>
