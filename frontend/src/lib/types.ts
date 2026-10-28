export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

export type EvidenceGrade = 'strong' | 'moderate' | 'weak' | 'none';
export type ScanStatus = 'queued' | 'running' | 'done' | 'error';
export type SignalStatus =
	| 'detected'
	| 'absent'
	| 'info'
	| 'inconclusive'
	| 'error'
	| 'skipped'
	| 'not_installed'
	| 'not_configured';

export interface Conclusion {
	provenance_class: string;
	label: string;
	evidence_grade: EvidenceGrade;
	decisive_signal: string | null;
	notes: string[];
}

export interface Signal {
	kind: string;
	name: string;
	status: SignalStatus;
	evidence_grade: EvidenceGrade;
	summary: string;
	method?: string | null;
	manual_integration?: string | null;
	duration_ms?: number | null;
	data?: Record<string, JsonValue>;
}

export interface ManualModule {
	name: string;
	status: string;
	how?: string | null;
}

export interface Coverage {
	live: number;
	manual: number;
	errors: number;
	manual_modules?: ManualModule[];
}

export interface PlatformPreview {
	platform: string;
	slug: string;
	label_text: string;
	label_subtext: string;
	detection_summary: string;
	metadata_signals: string[];
	creator_duty: string;
	label_on_edit: string;
	likely_label: 'yes' | 'no' | 'unknown';
	reasons: string[];
	removal_policy: string;
	monetization_impact: string;
	confidence: Confidence;
	last_verified: string;
	sources: string[];
}

export interface Report {
	scan_id: string;
	product: { name: string; version: string };
	created_at: number;
	completed_at: number;
	duration_ms: number;
	file: { filename: string; mime: string; size: number; sha256: string };
	modality: string;
	conclusion: Conclusion;
	signals: Signal[];
	coverage: Coverage;
	timings: Array<{ analyzer: string; ms: number; signals: number }>;
	trust_sources: string[];
	hash_only: boolean;
	platform_preview: PlatformPreview[];
	facts: Record<string, JsonValue>;
}

export interface ScanSummary {
	id: string;
	created_at: number;
	status: ScanStatus;
	modality: string | null;
	filename: string | null;
	mime: string | null;
	size: number | null;
	sha256: string | null;
	conclusion: string | null;
	evidence_grade: EvidenceGrade | null;
}

export interface ScanDetail {
	id: string;
	status: ScanStatus;
	modality: string | null;
	filename: string | null;
	mime: string | null;
	size: number | null;
	sha256: string | null;
	created_at: number;
	updated_at: number;
	error: string | null;
	report?: Report;
}

export interface RemovalSummary {
	provenance_class: string | null;
	evidence_grade: string | null;
	label: string | null;
	layer1_present: string[];
}

export interface RemovalResult {
	removal_id: string;
	scan_id: string;
	status: string;
	modality: string;
	input_sha256: string;
	output_sha256: string;
	fields_removed: string[];
	output_download_url: string;
	verdict: 'layer1_clean' | 'layer1_residue' | 'no_layer1_found';
	before: RemovalSummary;
	after: RemovalSummary;
	layer2_disclaimer: string;
}

export interface CreateScanResponse {
	id: string;
	status: string;
	report_url?: string;
	html_url?: string;
}

export interface DemoFile {
	name: string;
	modality: string;
	desc: string;
	size: number;
}

export type Confidence = 'high' | 'medium' | 'low';

export interface RegistryEntry {
	slug: string;
	vendor: string;
	tool: string;
	modality: string;
	visible_mark: string;
	invisible_watermark: string;
	c2pa: string;
	iptc: string;
	public_detector: string;
	survives: string;
	confidence: Confidence;
	last_verified: string;
	notes?: string;
}

export interface RegistryResponse {
	meta: { note: string; last_reviewed: string; fields?: Record<string, string> };
	entries: RegistryEntry[];
}

export interface PlatformRule {
	slug: string;
	name: string;
	label_text: string;
	label_subtext: string;
	detection_summary: string;
	metadata_signals: string[];
	creator_duty: string;
	auto_label_triggers: string[];
	label_on_edit: string;
	removal_policy: string;
	monetization_impact: string;
	notes: string;
	confidence: Confidence;
	last_verified: string;
	sources: string[];
}

export interface JurisdictionRule {
	slug: string;
	name: string;
	effective: string;
	status: string;
	penalty: string;
	obligations: Record<string, string>;
	content_types: Record<string, string[]>;
	confidence: Confidence;
	last_verified: string;
	sources: string[];
	notes?: string;
}

export interface DisclosureInput {
	content_type: 'image' | 'video' | 'audio' | 'text';
	is_ai_generated: boolean;
	is_ai_edited: boolean;
	depicts_real_person: boolean;
	public_interest_text: boolean;
	human_reviewed: boolean;
	artistic: boolean;
	has_c2pa: boolean;
	has_visible_label: boolean;
	has_metadata_id: boolean;
	jurisdictions: string[];
}

export interface DisclosureItem {
	key: string;
	requirement: string;
	status: 'todo' | 'done' | 'exempt' | 'optional';
	note: string;
}

export interface DisclosureResult {
	content_type: string;
	synthetic: boolean;
	open_items: number;
	jurisdictions: Array<{
		jurisdiction: string;
		slug: string;
		effective: string;
		status_note: string;
		penalty: string;
		items: DisclosureItem[];
		confidence: Confidence;
		last_verified: string;
		applies: boolean;
	}>;
	recommendations: string[];
	disclaimer: string;
}

export interface Capabilities {
	live: Record<string, string | number | boolean | string[]>;
	manual_integration: Record<string, boolean>;
}

export interface Health {
	ok: boolean;
	version: string;
	scans_total: number;
	scans_done: number;
}

export interface UnicodeFinding {
	cp: string;
	name: string;
	pos: number;
	type?: string;
}

export interface UnicodeResult {
	scan: {
		count: number;
		by_type?: Record<string, number>;
		findings?: UnicodeFinding[];
		stats: {
			chars: number;
			em_dashes: number;
			curly_quotes: number;
			double_spaces: number;
			trailing_space_lines: number;
		};
	};
	cleaned: string;
	changed: boolean;
}

export interface GreenlistStats {
	verdict?: string;
	z?: number;
	green?: number;
	scored_tokens?: number;
	p_one_sided?: number;
	error?: string;
}

export interface GreenlistResult {
	text?: string;
	stats: GreenlistStats;
}
