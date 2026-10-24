import { readdirSync, readFileSync, statSync } from 'node:fs';
import { extname, join, relative } from 'node:path';
import { gzipSync } from 'node:zlib';

const buildDirectory = new URL('../build/', import.meta.url).pathname;

const budgets = {
	javascriptChunkGzip: 110 * 1024,
	cssChunkGzip: 35 * 1024,
	totalJavascriptGzip: 260 * 1024,
	totalCssGzip: 85 * 1024,
	htmlGzip: 90 * 1024,
	fontFile: 72 * 1024
};

function walk(directory) {
	return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
		const path = join(directory, entry.name);
		return entry.isDirectory() ? walk(path) : [path];
	});
}

function gzipSize(path) {
	return gzipSync(readFileSync(path), { level: 9 }).length;
}

function format(bytes) {
	return `${(bytes / 1024).toFixed(1)} KiB`;
}

let files;
try {
	files = walk(buildDirectory);
} catch {
	console.error('No frontend/build directory found. Run `npm run build` first.');
	process.exit(1);
}

const assets = files
	.filter((path) => !path.endsWith('.gz') && !path.endsWith('.br'))
	.map((path) => ({
		path: relative(buildDirectory, path),
		extension: extname(path).toLowerCase(),
		raw: statSync(path).size,
		gzip: gzipSize(path)
	}));

const javascript = assets.filter((asset) => asset.extension === '.js');
const css = assets.filter((asset) => asset.extension === '.css');
const html = assets.filter((asset) => asset.extension === '.html');
const fonts = assets.filter((asset) => asset.extension === '.woff2');

const totals = {
	javascript: javascript.reduce((sum, asset) => sum + asset.gzip, 0),
	css: css.reduce((sum, asset) => sum + asset.gzip, 0)
};

const failures = [];

for (const asset of javascript) {
	if (asset.gzip > budgets.javascriptChunkGzip) {
		failures.push(
			`${asset.path}: ${format(asset.gzip)} gzip exceeds per-chunk JS budget ${format(budgets.javascriptChunkGzip)}`
		);
	}
}
for (const asset of css) {
	if (asset.gzip > budgets.cssChunkGzip) {
		failures.push(
			`${asset.path}: ${format(asset.gzip)} gzip exceeds per-chunk CSS budget ${format(budgets.cssChunkGzip)}`
		);
	}
}
for (const asset of html) {
	if (asset.gzip > budgets.htmlGzip) {
		failures.push(
			`${asset.path}: ${format(asset.gzip)} gzip exceeds HTML budget ${format(budgets.htmlGzip)}`
		);
	}
}
for (const asset of fonts) {
	if (asset.raw > budgets.fontFile) {
		failures.push(
			`${asset.path}: ${format(asset.raw)} exceeds font-file budget ${format(budgets.fontFile)}`
		);
	}
}
if (totals.javascript > budgets.totalJavascriptGzip) {
	failures.push(
		`All route JS totals ${format(totals.javascript)} gzip; budget is ${format(budgets.totalJavascriptGzip)}`
	);
}
if (totals.css > budgets.totalCssGzip) {
	failures.push(
		`All route CSS totals ${format(totals.css)} gzip; budget is ${format(budgets.totalCssGzip)}`
	);
}

function report(label, values, key = 'gzip') {
	console.log(`\n${label}`);
	for (const asset of [...values].sort((a, b) => b[key] - a[key]).slice(0, 12)) {
		console.log(`  ${format(asset[key]).padStart(9)}  ${asset.path}`);
	}
}

console.log('Provenably frontend bundle budget');
console.log(
	`JavaScript total (all routes, gzip): ${format(totals.javascript)} / ${format(budgets.totalJavascriptGzip)}`
);
console.log(
	`CSS total (all routes, gzip):        ${format(totals.css)} / ${format(budgets.totalCssGzip)}`
);
report('Largest JavaScript chunks (gzip)', javascript);
report('Largest CSS chunks (gzip)', css);
report('Largest HTML documents (gzip)', html);
report('Font files (already-compressed woff2)', fonts, 'raw');

if (failures.length) {
	console.error('\nBundle budget failed:');
	for (const failure of failures) console.error(`- ${failure}`);
	process.exit(1);
}

console.log('\nBundle budget passed.');
