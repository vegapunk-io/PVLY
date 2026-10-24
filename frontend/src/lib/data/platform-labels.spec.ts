import { describe, expect, it } from 'vitest';
import { platformLabel, platformLabelCatalog } from './platform-labels';
import { genericPreset, presetDefinitions } from './presets';

describe('platform label catalogue', () => {
	it('covers every preset with the researched viewer wording', () => {
		const expected: Record<string, string> = {
			youtube: '“Made with AI”',
			instagram: '“AI info”',
			tiktok: '“AI-generated”',
			linkedin: '“cr” pin',
			pinterest: '“AI modified”',
			reddit: 'No site-wide AI label',
			x: '“Made with AI”',
			facebook: '“AI info”'
		};

		for (const preset of [genericPreset, ...presetDefinitions]) {
			expect(platformLabelCatalog[preset.slug], preset.slug).toBeDefined();
		}
		for (const [slug, label] of Object.entries(expected)) {
			expect(platformLabel(slug).labelDisplay).toBe(label);
		}
	});

	it('keeps provenance and no-label destinations semantically distinct', () => {
		expect(platformLabel('linkedin').labelKind).toBe('provenance');
		expect(platformLabel('linkedin').labelDisplay).not.toContain('CC');
		expect(platformLabel('reddit').labelKind).toBe('none');
		expect(platformLabel('amazon_kdp').labelKind).toBe('private');
	});

	it('does not overstate documented Pinterest or X detection', () => {
		expect(platformLabel('pinterest').detectionSummary).toContain(
			'official help does not separately name C2PA'
		);
		expect(platformLabel('x').confidence).toBe('medium');
		expect(platformLabel('x').detectionSummary).toContain('complete trigger list');
	});

	it('dates and sources every external platform record', () => {
		for (const info of Object.values(platformLabelCatalog)) {
			expect(info.lastVerified).toBe('2026-10-24');
			expect(info.metadataSignals.length).toBeGreaterThan(0);
			if (info.slug !== 'generic') {
				expect(info.sources.length, info.slug).toBeGreaterThan(0);
				for (const source of info.sources) expect(source.url).toMatch(/^https:\/\//);
			}
		}
		expect(platformLabel('unknown-platform')).toBe(platformLabelCatalog.generic);
	});
});
