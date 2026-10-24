export interface PresetDefinition {
	slug: string;
	name: string;
	initial: string;
	media: string;
	formats: string;
	output: string;
	labelNote: string;
	creatorDuty: string;
	platformBehavior: string;
}

export const genericPreset: PresetDefinition = {
	slug: 'generic',
	name: 'Generic master',
	initial: 'G',
	media: 'Image · Video · Audio · Document · Text',
	formats: 'Original format',
	output: 'Verified-clean master with no resize or re-encode by default',
	labelNote: 'Your own publication context controls disclosure',
	creatorDuty: 'Keep the original and the before/after report with the exported master.',
	platformBehavior: 'Use for your own site, email, archive or a downstream editor.'
};

export const presetDefinitions: PresetDefinition[] = [
	{
		slug: 'youtube',
		name: 'YouTube',
		initial: 'Y',
		media: 'Video',
		formats: 'MP4 · MOV',
		output: 'H.264 publishing master, up to the source resolution',
		labelNote: 'Altered-content disclosure may apply',
		creatorDuty: 'Use YouTube Studio’s altered-content disclosure when the content requires it.',
		platformBehavior:
			'Upload processing re-encodes video; embedded signals and platform detection may remain relevant.'
	},
	{
		slug: 'instagram',
		name: 'Instagram',
		initial: 'I',
		media: 'Image · Video',
		formats: 'JPG · MP4',
		output: 'sRGB export sized for feed and Reels workflows',
		labelNote: 'Meta may read C2PA/IPTC and show AI info',
		creatorDuty: 'Self-disclose photorealistic synthetic content where Meta policy requires it.',
		platformBehavior:
			'Meta can inspect provenance signals before its normal upload processing removes metadata.'
	},
	{
		slug: 'tiktok',
		name: 'TikTok',
		initial: 'T',
		media: 'Video',
		formats: 'MP4',
		output: 'Vertical-first 1080 × 1920 publishing export',
		labelNote: 'AI-generated label rules apply',
		creatorDuty: 'Turn on TikTok’s AI-generated content label when applicable.',
		platformBehavior:
			'C2PA and platform-side detection can inform labelling; recompression does not erase creator duties.'
	},
	{
		slug: 'linkedin',
		name: 'LinkedIn',
		initial: 'L',
		media: 'Image · Document',
		formats: 'JPG · PNG · PDF',
		output: 'Professional feed image or document-safe PDF',
		labelNote: 'Content Credentials can surface through the CR icon',
		creatorDuty:
			'Prioritize author, employer, location and document-revision hygiene before posting.',
		platformBehavior:
			'A valid Content Credential may remain visible to viewers through LinkedIn’s provenance UI.'
	},
	{
		slug: 'pinterest',
		name: 'Pinterest',
		initial: 'P',
		media: 'Image',
		formats: 'JPG · PNG · WebP',
		output: '1000 × 1500 (2:3) Pin-ready image',
		labelNote: 'AI-modified labelling may use provenance or classifiers',
		creatorDuty:
			'Check the current Pin policy and retain the provenance report for the source asset.',
		platformBehavior:
			'Pinterest may inspect C2PA/IPTC signals and its own classifiers before serving resized variants.'
	},
	{
		slug: 'reddit',
		name: 'Reddit',
		initial: 'R',
		media: 'Image · Video',
		formats: 'JPG · PNG · MP4',
		output: 'Original dimensions kept unless a community requires otherwise',
		labelNote: 'Subreddit rules vary materially',
		creatorDuty:
			'Check the destination subreddit’s AI-content and source-attribution rules before posting.',
		platformBehavior:
			'Community moderation can matter more than platform-wide automated provenance labels.'
	},
	{
		slug: 'x',
		name: 'X (Twitter)',
		initial: 'X',
		media: 'Image · Video',
		formats: 'JPG · PNG · MP4',
		output: 'Recompression-aware social export',
		labelNote: 'Limited automation; policy and community context matter',
		creatorDuty:
			'Do not present synthetic media as authentic; add context in the post when it could mislead.',
		platformBehavior:
			'Uploads are commonly recompressed, while screenshots and reposts rapidly separate files from provenance.'
	},
	{
		slug: 'facebook',
		name: 'Facebook',
		initial: 'F',
		media: 'Image · Video',
		formats: 'JPG · PNG · MP4',
		output: 'Feed-ready image or video export',
		labelNote: 'Same Meta AI-info pipeline as Instagram',
		creatorDuty:
			'Self-disclose where required, especially for photorealistic people, events and advertising.',
		platformBehavior:
			'Meta may combine provenance metadata, vendor signals and classifiers before applying AI info.'
	}
];

export function findPreset(slug: string): PresetDefinition {
	return presetDefinitions.find((preset) => preset.slug === slug) ?? genericPreset;
}
