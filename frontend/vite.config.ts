import { defineConfig } from 'vitest/config';
import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';

const apiOrigin = process.env.PROVENABLY_API_ORIGIN ?? 'http://127.0.0.1:8000';

const apiProxy = {
	target: apiOrigin,
	changeOrigin: true
};

const developmentServer = {
	host: '0.0.0.0',
	allowedHosts: ['localhost', '.e2b.app'],
	proxy: {
		'/v1': apiProxy,
		'/api': apiProxy,
		'/demo-assets': apiProxy,
		'/health': apiProxy
	}
};

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Force runes mode for project code; dependencies retain their own mode.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			adapter: adapter({
				pages: 'build',
				assets: 'build',
				fallback: '200.html',
				precompress: true,
				strict: true
			}),
			prerender: {
				handleHttpError: 'warn'
			}
		})
	],
	server: {
		...developmentServer,
		port: 5173
	},
	preview: {
		...developmentServer,
		port: 4173
	},
	build: {
		target: 'es2020',
		cssCodeSplit: true,
		cssMinify: true,
		minify: 'oxc',
		sourcemap: false,
		reportCompressedSize: true,
		chunkSizeWarningLimit: 120,
		assetsInlineLimit: 2048
	},
	test: {
		expect: { requireAssertions: true },
		projects: [
			{
				extends: './vite.config.ts',
				test: {
					name: 'unit',
					environment: 'node',
					include: ['src/**/*.{test,spec}.{js,ts}'],
					exclude: ['src/**/*.svelte.{test,spec}.{js,ts}']
				}
			}
		]
	}
});
