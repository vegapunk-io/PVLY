import { getSessionApiKey } from './settings';
import type {
	Capabilities,
	CreateScanResponse,
	DemoFile,
	DisclosureInput,
	DisclosureResult,
	GreenlistResult,
	Health,
	JurisdictionRule,
	PlatformRule,
	RegistryEntry,
	RegistryResponse,
	ScanDetail,
	ScanSummary,
	UnicodeResult
} from './types';

export const MAX_UPLOAD_BYTES = 200 * 1024 * 1024;
export const SCAN_ACCEPT =
	'image/*,video/*,audio/*,text/plain,text/markdown,application/pdf,.docx,.txt,.md,.html,.mp3,.mp4,.mov,.wav,.webp,.heic,.avif,.tif,.tiff';

export class ApiError extends Error {
	readonly status: number;

	constructor(message: string, status = 0) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
	}
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
	body?: BodyInit | null;
	timeoutMs?: number;
}

function mergeSignal(signal: AbortSignal | null | undefined, timeoutMs: number): AbortSignal {
	const timeoutSignal = AbortSignal.timeout(timeoutMs);
	if (!signal) return timeoutSignal;
	return AbortSignal.any([signal, timeoutSignal]);
}

function apiHeaders(extra: HeadersInit | undefined, hasJsonBody = false): Headers {
	const headers = new Headers(extra);
	headers.set('Accept', 'application/json');
	if (hasJsonBody) headers.set('Content-Type', 'application/json');
	const apiKey = getSessionApiKey();
	if (apiKey) headers.set('X-API-Key', apiKey);
	return headers;
}

function detailToMessage(detail: unknown, fallback: string): string {
	if (typeof detail === 'string' && detail.trim()) return detail;
	if (Array.isArray(detail)) {
		const messages = detail
			.map((item) => {
				if (item && typeof item === 'object' && 'msg' in item) return String(item.msg);
				return '';
			})
			.filter(Boolean);
		if (messages.length) return messages.join('; ');
	}
	if (detail && typeof detail === 'object') {
		try {
			return JSON.stringify(detail);
		} catch {
			return fallback;
		}
	}
	return fallback;
}

async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
	const { timeoutMs = 30_000, signal, headers, ...init } = options;
	let response: Response;

	try {
		response = await fetch(path, {
			...init,
			headers: apiHeaders(headers),
			signal: mergeSignal(signal, timeoutMs)
		});
	} catch (error) {
		if (error instanceof DOMException && error.name === 'AbortError') throw error;
		if (error instanceof DOMException && error.name === 'TimeoutError') {
			throw new ApiError('The Provenably API took too long to respond. Please try again.');
		}
		throw new ApiError(
			'Could not reach the Provenably API. Check that FastAPI is running, then retry.'
		);
	}

	const payload: unknown = await response.json().catch(() => null);
	if (!response.ok) {
		const detail =
			payload && typeof payload === 'object' && 'detail' in payload
				? (payload as { detail: unknown }).detail
				: null;
		throw new ApiError(
			detailToMessage(detail, response.statusText || `HTTP ${response.status}`),
			response.status
		);
	}

	return payload as T;
}

async function postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
	// requestJson installs Accept and X-API-Key; JSON requests need their own content type.
	const { timeoutMs = 30_000 } = {};
	let response: Response;
	try {
		response = await fetch(path, {
			method: 'POST',
			headers: apiHeaders(undefined, true),
			body: JSON.stringify(body),
			signal: mergeSignal(signal, timeoutMs)
		});
	} catch (error) {
		if (error instanceof DOMException && error.name === 'AbortError') throw error;
		throw new ApiError(
			'Could not reach the Provenably API. Check that FastAPI is running, then retry.'
		);
	}

	const payload: unknown = await response.json().catch(() => null);
	if (!response.ok) {
		const detail =
			payload && typeof payload === 'object' && 'detail' in payload
				? (payload as { detail: unknown }).detail
				: null;
		throw new ApiError(
			detailToMessage(detail, response.statusText || `HTTP ${response.status}`),
			response.status
		);
	}
	return payload as T;
}

export interface ScanFileInput {
	file: File;
	hashOnly: boolean;
	greenlistKey?: string;
}

export interface ScanTextInput {
	text: string;
	greenlistKey?: string;
}

export interface ScanUrlInput {
	url: string;
	hashOnly: boolean;
}

export function assertFileSize(file: File): void {
	if (!file.size) throw new ApiError('That file is empty. Choose a file with content to scan.');
	if (file.size > MAX_UPLOAD_BYTES) {
		throw new ApiError('That file is larger than the 200 MB deployment limit.');
	}
}

function scanFileForm(input: ScanFileInput): FormData {
	assertFileSize(input.file);
	const form = new FormData();
	form.append('file', input.file);
	form.append('hash_only', String(input.hashOnly));
	if (input.greenlistKey?.trim()) form.append('greenlist_key', input.greenlistKey.trim());
	return form;
}

export async function createFileScan(
	input: ScanFileInput,
	signal?: AbortSignal
): Promise<CreateScanResponse> {
	return requestJson('/v1/scans', {
		method: 'POST',
		body: scanFileForm(input),
		timeoutMs: 180_000,
		signal
	});
}

/**
 * Fetch cannot consistently expose upload progress. This narrow XMLHttpRequest path is used
 * only for file uploads so large scans on slow devices get deterministic progress and cancel.
 */
export function createFileScanWithProgress(
	input: ScanFileInput,
	onProgress: (fraction: number | null) => void,
	signal?: AbortSignal
): Promise<CreateScanResponse> {
	const form = scanFileForm(input);

	return new Promise((resolve, reject) => {
		if (signal?.aborted) {
			reject(new DOMException('The request was cancelled.', 'AbortError'));
			return;
		}

		const request = new XMLHttpRequest();
		request.open('POST', '/v1/scans');
		request.responseType = 'json';
		request.timeout = 180_000;
		request.setRequestHeader('Accept', 'application/json');
		const apiKey = getSessionApiKey();
		if (apiKey) request.setRequestHeader('X-API-Key', apiKey);

		const abort = () => request.abort();
		signal?.addEventListener('abort', abort, { once: true });

		const cleanup = () => signal?.removeEventListener('abort', abort);
		request.upload.addEventListener('progress', (event) => {
			onProgress(event.lengthComputable ? Math.min(1, event.loaded / event.total) : null);
		});
		request.addEventListener('load', () => {
			cleanup();
			const payload = request.response as unknown;
			if (request.status >= 200 && request.status < 300) {
				resolve(payload as CreateScanResponse);
				return;
			}
			const detail =
				payload && typeof payload === 'object' && 'detail' in payload
					? (payload as { detail: unknown }).detail
					: null;
			reject(
				new ApiError(
					detailToMessage(detail, request.statusText || `HTTP ${request.status}`),
					request.status
				)
			);
		});
		request.addEventListener('abort', () => {
			cleanup();
			reject(new DOMException('The request was cancelled.', 'AbortError'));
		});
		request.addEventListener('timeout', () => {
			cleanup();
			reject(new ApiError('The upload took too long. Check the connection and try again.'));
		});
		request.addEventListener('error', () => {
			cleanup();
			reject(
				new ApiError(
					'Could not reach the Provenably API. Check that FastAPI is running, then retry.'
				)
			);
		});

		onProgress(0);
		request.send(form);
	});
}

export async function createTextScan(
	input: ScanTextInput,
	signal?: AbortSignal
): Promise<CreateScanResponse> {
	const form = new FormData();
	form.append('text', input.text);
	if (input.greenlistKey?.trim()) form.append('greenlist_key', input.greenlistKey.trim());
	return requestJson('/v1/scans', { method: 'POST', body: form, timeoutMs: 120_000, signal });
}

export async function createUrlScan(
	input: ScanUrlInput,
	signal?: AbortSignal
): Promise<CreateScanResponse> {
	const form = new FormData();
	form.append('url', input.url.trim());
	form.append('hash_only', String(input.hashOnly));
	return requestJson('/v1/scans', { method: 'POST', body: form, timeoutMs: 180_000, signal });
}

export async function createDemoScan(
	name: string,
	signal?: AbortSignal
): Promise<CreateScanResponse> {
	return requestJson(`/v1/scans/demo/${encodeURIComponent(name)}`, {
		method: 'POST',
		timeoutMs: 120_000,
		signal
	});
}

export function getDemoFiles(signal?: AbortSignal): Promise<{ files: DemoFile[] }> {
	return requestJson('/v1/demo-files', { signal });
}

export function listScans(limit = 25, signal?: AbortSignal): Promise<{ scans: ScanSummary[] }> {
	const bounded = Math.max(1, Math.min(limit, 200));
	return requestJson(`/v1/scans?limit=${bounded}`, { signal });
}

export function getScan(id: string, signal?: AbortSignal): Promise<ScanDetail> {
	return requestJson(`/v1/scans/${encodeURIComponent(id)}`, { signal, timeoutMs: 20_000 });
}

export function getRegistry(modality = '', signal?: AbortSignal): Promise<RegistryResponse> {
	const query = modality ? `?modality=${encodeURIComponent(modality)}` : '';
	return requestJson(`/v1/registry${query}`, { signal });
}

export function getRegistryEntry(slug: string, signal?: AbortSignal): Promise<RegistryEntry> {
	return requestJson(`/v1/registry/${encodeURIComponent(slug)}`, { signal });
}

export function getPlatforms(signal?: AbortSignal): Promise<{ platforms: PlatformRule[] }> {
	return requestJson('/v1/rules/platforms', { signal });
}

export function getJurisdictions(
	signal?: AbortSignal
): Promise<{ jurisdictions: JurisdictionRule[] }> {
	return requestJson('/v1/rules/jurisdictions', { signal });
}

export function checkDisclosure(
	input: DisclosureInput,
	signal?: AbortSignal
): Promise<DisclosureResult> {
	return postJson('/v1/disclosure/check', input, signal);
}

export function getCapabilities(signal?: AbortSignal): Promise<Capabilities> {
	return requestJson('/v1/capabilities', { signal });
}

export function getHealth(signal?: AbortSignal): Promise<Health> {
	return requestJson('/health', { signal, timeoutMs: 10_000 });
}

export function scanUnicode(
	input: { text: string; keep_joiners: boolean; ascii_dashes: boolean },
	signal?: AbortSignal
): Promise<UnicodeResult> {
	return postJson('/v1/text/unicode', input, signal);
}

export function runGreenlist(
	input: {
		action: 'generate' | 'detect';
		key: string;
		gamma: number;
		strength?: number;
		n?: number;
		text?: string;
	},
	signal?: AbortSignal
): Promise<GreenlistResult> {
	return postJson('/v1/lab/greenlist', input, signal);
}

export async function fetchText(path: string, signal?: AbortSignal): Promise<string> {
	const response = await fetch(path, { signal: mergeSignal(signal, 30_000) });
	if (!response.ok) throw new ApiError(`Could not load ${path}.`, response.status);
	return response.text();
}

export function errorMessage(
	error: unknown,
	fallback = 'Something went wrong. Please try again.'
): string {
	if (error instanceof ApiError) return error.message;
	if (error instanceof DOMException && error.name === 'AbortError')
		return 'The request was cancelled.';
	if (error instanceof Error && error.message) return error.message;
	return fallback;
}
