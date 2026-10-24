export interface PresetDefinition {
	slug: string;
	name: string;
	media: string;
	formats: string;
	output: string;
	creatorDuty: string;
	platformBehavior: string;
}

export const genericPreset: PresetDefinition = {
	slug: 'generic',
	name: 'Generic master',
	media: 'Image · Video · Audio · Document · Text',
	formats: 'Original format',
	output: 'Verified-clean master with no resize or re-encode by default',
	creatorDuty: 'Keep the original and the before/after report with the exported master.',
	platformBehavior: 'Use for your own site, email, archive or a downstream editor.'
};

export const presetDefinitions: PresetDefinition[] = [
	{
		slug: 'youtube',
		name: 'YouTube',
		media: 'Video',
		formats: 'MP4 · MOV',
		output: 'H.264 publishing master, up to the source resolution',
		creatorDuty:
			'Set YouTube Studio’s AI-use answer to “Yes” when realistic content was meaningfully generated or altered with AI.',
		platformBehavior:
			'YouTube can carry forward C2PA disclosures and apply internal detection even though upload processing re-encodes the video.'
	},
	{
		slug: 'instagram',
		name: 'Instagram',
		media: 'Image · Video',
		formats: 'JPG · MP4',
		output: 'sRGB export sized for feed and Reels workflows',
		creatorDuty: 'Self-disclose photorealistic synthetic content where Meta policy requires it.',
		platformBehavior:
			'Meta can inspect C2PA and IPTC provenance signals before its normal upload processing removes metadata.'
	},
	{
		slug: 'tiktok',
		name: 'TikTok',
		media: 'Video',
		formats: 'MP4',
		output: 'Vertical-first 1080 × 1920 publishing export',
		creatorDuty: 'Turn on TikTok’s AI-generated content label when applicable.',
		platformBehavior:
			'TikTok layers C2PA reading, native-tool provenance, detection models and invisible watermarking; a clean container does not settle the label.'
	},
	{
		slug: 'linkedin',
		name: 'LinkedIn',
		media: 'Image · Document',
		formats: 'JPG · PNG · PDF',
		output: 'Professional feed image or document-safe PDF',
		creatorDuty:
			'Prioritize author, employer, location and document-revision hygiene before posting.',
		platformBehavior:
			'Any signed C2PA credential—not only an AI credential—can produce the public “cr” pin and its provenance panel.'
	},
	{
		slug: 'pinterest',
		name: 'Pinterest',
		media: 'Image',
		formats: 'JPG · PNG · WebP',
		output: '1000 × 1500 (2:3) Pin-ready image',
		creatorDuty:
			'Identify AI-generated or AI-modified Pins where Pinterest requests it and retain the source provenance report.',
		platformBehavior:
			'Pinterest combines IPTC metadata analysis with its own classifiers, so removing metadata does not guarantee an unlabeled Pin.'
	},
	{
		slug: 'reddit',
		name: 'Reddit',
		media: 'Image · Video',
		formats: 'JPG · PNG · MP4',
		output: 'Original dimensions kept unless a community requires otherwise',
		creatorDuty:
			'Check the destination subreddit’s AI-content and source-attribution rules before posting.',
		platformBehavior:
			'Community moderation and flair rules can matter more than any site-wide automated provenance label.'
	},
	{
		slug: 'x',
		name: 'X (Twitter)',
		media: 'Image · Video',
		formats: 'JPG · PNG · MP4',
		output: 'Recompression-aware social export',
		creatorDuty:
			'Use X’s “Made with AI” content disclosure for synthetic media and add context when a post could mislead.',
		platformBehavior:
			'X’s complete auto-label criteria are not published; C2PA-linked detection has been observed, and deceptive media can receive separate enforcement context.'
	},
	{
		slug: 'facebook',
		name: 'Facebook',
		media: 'Image · Video',
		formats: 'JPG · PNG · MP4',
		output: 'Feed-ready image or video export',
		creatorDuty:
			'Self-disclose where required, especially for photorealistic people, events and advertising.',
		platformBehavior:
			'Meta reads shared C2PA/IPTC indicators before normal processing; ads also use Meta-tool and third-party-AI detection signals.'
	}
];

export function findPreset(slug: string): PresetDefinition {
	return presetDefinitions.find((preset) => preset.slug === slug) ?? genericPreset;
}
