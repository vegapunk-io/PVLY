import type { Confidence, EvidenceGrade, SignalStatus } from './types';

const byteUnits = ['B', 'KB', 'MB', 'GB'];

export function formatBytes(value: number | null | undefined): string {
	if (value === null || value === undefined || !Number.isFinite(value)) return '–';
	if (value < 1024) return `${Math.max(0, Math.round(value))} B`;
	const exponent = Math.min(Math.floor(Math.log(value) / Math.log(1024)), byteUnits.length - 1);
	const normalized = value / 1024 ** exponent;
	return `${normalized >= 100 ? normalized.toFixed(0) : normalized.toFixed(1)} ${byteUnits[exponent]}`;
}

export function formatTimestamp(epochSeconds: number | null | undefined): string {
	if (!epochSeconds || !Number.isFinite(epochSeconds)) return '–';
	return (
		new Intl.DateTimeFormat('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			timeZone: 'UTC',
			hour12: false
		}).format(new Date(epochSeconds * 1000)) + ' UTC'
	);
}

export function formatDuration(milliseconds: number | null | undefined): string {
	if (milliseconds === null || milliseconds === undefined || !Number.isFinite(milliseconds))
		return '–';
	if (milliseconds < 1000) return `${Math.round(milliseconds)} ms`;
	return `${(milliseconds / 1000).toFixed(milliseconds < 10_000 ? 1 : 0)} s`;
}

export function shortenHash(hash: string | null | undefined, visible = 10): string {
	if (!hash) return '–';
	if (hash.length <= visible * 2 + 1) return hash;
	return `${hash.slice(0, visible)}…${hash.slice(-visible)}`;
}

export function titleCaseToken(value: string | null | undefined): string {
	if (!value) return '–';
	return value.replaceAll('_', ' ').replace(/\b\w/g, (character) => character.toUpperCase());
}

export function gradeTone(grade: EvidenceGrade | string | null | undefined): string {
	switch (grade) {
		case 'strong':
			return 'tag--strong';
		case 'moderate':
			return 'tag--moderate';
		case 'weak':
			return 'tag--weak';
		default:
			return '';
	}
}

export function statusTone(status: SignalStatus | string): string {
	switch (status) {
		case 'detected':
			return 'tag--ok';
		case 'info':
			return 'tag--accent';
		case 'inconclusive':
			return 'tag--warn';
		case 'error':
			return 'tag--bad';
		case 'not_installed':
		case 'not_configured':
			return 'tag--manual';
		default:
			return '';
	}
}

export function confidenceTone(confidence: Confidence): string {
	return confidence === 'high' ? 'tag--ok' : confidence === 'medium' ? 'tag--warn' : 'tag--bad';
}

export function isManualStatus(status: SignalStatus | string): boolean {
	return status === 'not_installed' || status === 'not_configured';
}

export function pluralize(count: number, singular: string, plural = `${singular}s`): string {
	return `${count} ${count === 1 ? singular : plural}`;
}

export function safeJson(value: unknown): string {
	try {
		return JSON.stringify(value, null, 2) ?? 'null';
	} catch {
		return String(value);
	}
}
