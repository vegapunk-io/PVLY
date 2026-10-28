import { describe, expect, it } from 'vitest';
import { ApiError, errorMessage, friendlyApiError } from './api';

describe('friendlyApiError', () => {
	it('never exposes status codes or framework names', () => {
		for (const status of [400, 401, 404, 413, 429, 500, 502, 503]) {
			const { message } = friendlyApiError(status, null);
			expect(message).not.toMatch(/HTTP|FastAPI|\b\d{3}\b.*error|Internal Server/i);
		}
	});

	it('tells the user how to fix a missing key', () => {
		expect(friendlyApiError(401, 'invalid or missing X-API-Key').message).toContain('Settings');
	});

	it('hides server internals behind a retry message', () => {
		const error = friendlyApiError(500, 'Traceback (most recent call last)');
		expect(error.message).toBe('Something went wrong on our side. Please try again in a moment.');
		expect(error.status).toBe(500);
	});

	it('keeps the server wording for rate limits so Retry guidance survives', () => {
		const error = friendlyApiError(429, 'Wait a minute and try again.');
		expect(error.message).toBe('Wait a minute and try again.');
	});

	it('keeps plain 400-level detail from the server', () => {
		expect(friendlyApiError(400, 'attested=true required').message).toBe('attested=true required');
	});

	it('falls back to a generic sentence when there is no detail', () => {
		expect(friendlyApiError(400, null).message).toBe('That request could not be completed.');
	});
});

describe('errorMessage', () => {
	it('passes ApiError text through unchanged', () => {
		expect(errorMessage(new ApiError('Hello', 404))).toBe('Hello');
	});

	it('uses the fallback for unknown values', () => {
		expect(errorMessage(undefined, 'fallback')).toBe('fallback');
	});
});
