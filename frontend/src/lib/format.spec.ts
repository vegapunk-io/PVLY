import { describe, expect, it } from 'vitest';
import { formatBytes, gradeTone, shortenHash, titleCaseToken } from './format';

describe('format helpers', () => {
	it('formats bytes with binary units', () => {
		expect(formatBytes(512)).toBe('512 B');
		expect(formatBytes(1536)).toBe('1.5 KB');
		expect(formatBytes(5 * 1024 * 1024)).toBe('5.0 MB');
	});

	it('shortens long hashes without hiding short values', () => {
		expect(shortenHash('abcdef')).toBe('abcdef');
		expect(shortenHash('1234567890abcdefghijklmnopqrstuvwxyz', 6)).toBe('123456…uvwxyz');
	});

	it('keeps evidence grades semantically distinct from the action accent', () => {
		expect(gradeTone('strong')).toBe('tag--strong');
		expect(gradeTone('moderate')).toBe('tag--moderate');
		expect(gradeTone('weak')).toBe('tag--weak');
		expect(gradeTone('none')).toBe('');
	});

	it('humanizes API tokens', () => {
		expect(titleCaseToken('ai_generated_declared')).toBe('Ai Generated Declared');
	});
});
