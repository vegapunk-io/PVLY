const API_KEY_STORAGE_KEY = 'provenably.sessionApiKey';
const PREFERENCES_STORAGE_KEY = 'provenably.preferences.v1';

export interface LocalPreferences {
	hashOnlyDefault: boolean;
	includeJurisdictionNote: boolean;
	preferredPreset: string;
	retentionLabel: string;
}

export const defaultPreferences: LocalPreferences = {
	hashOnlyDefault: false,
	includeJurisdictionNote: true,
	preferredPreset: 'generic',
	retentionLabel: '24-hours'
};

function canUseStorage(storage: Storage | undefined): storage is Storage {
	return typeof window !== 'undefined' && Boolean(storage);
}

export function getSessionApiKey(): string {
	if (!canUseStorage(window.sessionStorage)) return '';
	try {
		return window.sessionStorage.getItem(API_KEY_STORAGE_KEY) ?? '';
	} catch {
		return '';
	}
}

export function setSessionApiKey(value: string): void {
	if (!canUseStorage(window.sessionStorage)) return;
	try {
		const trimmed = value.trim();
		if (trimmed) window.sessionStorage.setItem(API_KEY_STORAGE_KEY, trimmed);
		else window.sessionStorage.removeItem(API_KEY_STORAGE_KEY);
	} catch {
		// Storage may be unavailable in private or embedded contexts; the UI remains usable.
	}
}

export function getPreferences(): LocalPreferences {
	if (!canUseStorage(window.localStorage)) return defaultPreferences;
	try {
		const raw = window.localStorage.getItem(PREFERENCES_STORAGE_KEY);
		if (!raw) return defaultPreferences;
		const parsed = JSON.parse(raw) as Partial<LocalPreferences>;
		return {
			hashOnlyDefault: Boolean(parsed.hashOnlyDefault),
			includeJurisdictionNote: parsed.includeJurisdictionNote !== false,
			preferredPreset:
				typeof parsed.preferredPreset === 'string' && parsed.preferredPreset
					? parsed.preferredPreset
					: defaultPreferences.preferredPreset,
			retentionLabel:
				typeof parsed.retentionLabel === 'string' && parsed.retentionLabel
					? parsed.retentionLabel
					: defaultPreferences.retentionLabel
		};
	} catch {
		return defaultPreferences;
	}
}

export function setPreferences(preferences: LocalPreferences): void {
	if (!canUseStorage(window.localStorage)) return;
	try {
		window.localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(preferences));
	} catch {
		// Preference persistence is progressive enhancement only.
	}
}
