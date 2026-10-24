export type PlatformLabelKind = 'visible' | 'provenance' | 'none' | 'private';

export interface PlatformLabelSource {
	label: string;
	url: string;
}

export interface PlatformLabelInfo {
	slug: string;
	labelDisplay: string;
	labelKind: PlatformLabelKind;
	labelSubtext: string;
	signalSummary: string;
	detectionSummary: string;
	metadataSignals: string[];
	disclosureDuty: string;
	confidence: 'high' | 'medium' | 'low';
	lastVerified: string;
	sources: PlatformLabelSource[];
}

const LAST_VERIFIED = '2026-10-24';

export const platformLabelCatalog: Record<string, PlatformLabelInfo> = {
	generic: {
		slug: 'generic',
		labelDisplay: 'No platform label',
		labelKind: 'none',
		labelSubtext: 'Your own publication context controls disclosure.',
		signalSummary: 'No destination reader is assumed',
		detectionSummary:
			'No destination system is assumed. A downstream service may still read whatever provenance remains in the exported file.',
		metadataSignals: ['Depends on the downstream destination'],
		disclosureDuty:
			'Apply the disclosure required by the place where the master is eventually published.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: []
	},
	youtube: {
		slug: 'youtube',
		labelDisplay: '“Made with AI”',
		labelKind: 'visible',
		labelSubtext:
			'Can appear on the player and under “How this content was made” in the expanded description.',
		signalSummary: 'Declaration · C2PA · YouTube tools · internal detection',
		detectionSummary:
			'YouTube can apply the disclosure from the creator’s AI-use declaration, YouTube GenAI tools, valid C2PA data indicating the entire video was made with AI, or its internal detection systems.',
		metadataSignals: [
			'Creator AI-use declaration',
			'C2PA Content Credentials',
			'YouTube GenAI-tool provenance',
			'Internal detection systems'
		],
		disclosureDuty:
			'Set AI use to “Yes” for realistic content that AI meaningfully generated or altered. Minor aesthetic or non-realistic edits may not require disclosure.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'YouTube Help — How this content was made',
				url: 'https://support.google.com/youtube/answer/15447836'
			},
			{
				label: 'YouTube Help — Disclosing use of GenAI content',
				url: 'https://support.google.com/youtube/answer/14328491'
			}
		]
	},
	instagram: {
		slug: 'instagram',
		labelDisplay: '“AI info”',
		labelKind: 'visible',
		labelSubtext:
			'Generated content shows it on the post; content detected as only AI-edited places it in the post menu.',
		signalSummary: 'Reads C2PA · IPTC · creator disclosure',
		detectionSummary:
			'Meta reads industry-shared AI indicators, including “AI generated” information in C2PA and IPTC, and labels content after creator self-disclosure. Content made with Meta AI can also carry Meta’s own markers.',
		metadataSignals: [
			'C2PA AI assertion',
			'IPTC DigitalSourceType',
			'Creator disclosure',
			'Meta AI markers'
		],
		disclosureDuty:
			'Use Instagram’s AI disclosure controls where required, especially for photorealistic video or realistic audio.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'Meta — Labeling AI-generated content and manipulated media',
				url: 'https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/'
			},
			{
				label: 'Meta — C2PA and IPTC AI indicators',
				url: 'https://about.fb.com/news/2024/02/labeling-ai-generated-images-on-facebook-instagram-and-threads/'
			}
		]
	},
	tiktok: {
		slug: 'tiktok',
		labelDisplay: '“AI-generated”',
		labelKind: 'visible',
		labelSubtext:
			'TikTok-applied wording. The creator toggle can read “Creator labeled as AI-generated.”',
		signalSummary: 'C2PA · TikTok tools · detection models · invisible watermark',
		detectionSummary:
			'TikTok reads C2PA Content Credentials, automatically labels content from its AI tools and effects, uses its own detection models, and adds or uses invisible watermarking for TikTok-made and C2PA-bearing content.',
		metadataSignals: [
			'C2PA Content Credentials',
			'Creator AI-generated toggle',
			'TikTok AI tools and effects',
			'TikTok detection models',
			'Invisible watermarking'
		],
		disclosureDuty:
			'Turn on TikTok’s AI-generated content setting for realistic AI-generated or significantly AI-edited media.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'TikTok Support — AI-generated content labeling',
				url: 'https://support.tiktok.com/en/using-tiktok/creating-videos/ai-generated-content'
			},
			{
				label: 'TikTok Newsroom — Spot, shape and understand AI content',
				url: 'https://newsroom.tiktok.com/more-ways-to-spot-shape-and-understand-ai-content'
			}
		]
	},
	linkedin: {
		slug: 'linkedin',
		labelDisplay: '“cr” pin',
		labelKind: 'provenance',
		labelSubtext:
			'A Content Credentials provenance pin—not a standalone verdict that the media is AI-generated.',
		signalSummary: 'Triggered by signed C2PA metadata (documented)',
		detectionSummary:
			'LinkedIn shows the lower-case “cr” pin when an image or video carries cryptographically signed C2PA Content Credentials. Opening it can show the signer’s recorded AI use, app or device, creator, issuer and date. No general LinkedIn pixel classifier is documented.',
		metadataSignals: ['Cryptographically signed C2PA Content Credentials'],
		disclosureDuty:
			'Decide before upload whether the signed provenance history should be publicly inspectable on LinkedIn.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'LinkedIn — C2PA AI-generated content standard',
				url: 'https://news.linkedin.com/2024/May/linkedin-rolls-out-c2pa-ai-generated-content-standard'
			},
			{
				label: 'C2PA — Official Content Credentials icon',
				url: 'https://contentcredentials.org/introducing-official-content-credentials-icon/'
			}
		]
	},
	pinterest: {
		slug: 'pinterest',
		labelDisplay: '“AI modified”',
		labelKind: 'visible',
		labelSubtext: 'Appears at the bottom-left of a non-promoted image Pin in close-up view.',
		signalSummary: 'Reads IPTC metadata · classifiers · owner disclosure',
		detectionSummary:
			'Pinterest analyzes metadata under the IPTC standard, uses classifiers that can detect generative AI without obvious markers, and can label content the owner identifies as AI-generated or AI-modified. Its official help does not separately name C2PA.',
		metadataSignals: ['IPTC metadata', 'Pinterest classifiers', 'Content-owner disclosure'],
		disclosureDuty:
			'Identify AI-generated or AI-modified Pins where Pinterest asks for that disclosure.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'Pinterest Help — Gen AI labels',
				url: 'https://help.pinterest.com/en/article/gen-ai-labels'
			}
		]
	},
	reddit: {
		slug: 'reddit',
		labelDisplay: 'No site-wide AI label',
		labelKind: 'none',
		labelSubtext: 'Use an AI tag, flair or caption where the destination community requires one.',
		signalSummary: 'Community rules decide · no file-label reader documented',
		detectionSummary:
			'Reddit asks posters to be transparent and include a tag or other indication for permissible AI-generated or AI-modified content. Enforcement can use moderator and user reports plus internal policy systems; subreddit rules remain decisive. No public C2PA or IPTC label is documented.',
		metadataSignals: [
			'Post tag or flair',
			'Community rules',
			'Reports and internal policy systems'
		],
		disclosureDuty:
			'Check the destination subreddit’s AI-content, flair and source-attribution rules before posting.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'Reddit Help — Manipulated content and misleading behavior',
				url: 'https://support.reddithelp.com/hc/en-us/articles/41180423371156-Manipulated-Content-and-Misleading-Behavior'
			}
		]
	},
	x: {
		slug: 'x',
		labelDisplay: '“Made with AI”',
		labelKind: 'visible',
		labelSubtext:
			'A creator Content Disclosure toggle; automatic application has also been observed on some uploads.',
		signalSummary: 'Creator toggle · C2PA-linked detection observed',
		detectionSummary:
			'X has not published a complete trigger list for “Made with AI.” Independent 2026 upload tests found C2PA-linked detection and non-removable automatic labels, but the exact criteria are not public. “Manipulated media” remains a separate enforcement label for significantly deceptive media.',
		metadataSignals: [
			'Creator Content Disclosure toggle',
			'C2PA-linked detection (observed)',
			'Other X signals (not fully published)'
		],
		disclosureDuty:
			'Use the “Made with AI” disclosure for synthetically generated content. Regional rules can require a prominent declaration; X’s India guidance requires one for synthetically generated information.',
		confidence: 'medium',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'The Verge — X “Made with AI” labels',
				url: 'https://www.theverge.com/ai-artificial-intelligence/882974/x-is-working-on-made-with-ai-labels'
			},
			{
				label: 'Independent test — X automatic label conditions',
				url: 'https://roboin.io/article/en/2026/03/24/why-x-tags-posts-as-made-with-ai-and-how-to-remove-it-testing-the-conditions/'
			},
			{
				label: 'X Help — Manipulated media policy',
				url: 'https://help.x.com/en/rules-and-policies/manipulated-media'
			}
		]
	},
	facebook: {
		slug: 'facebook',
		labelDisplay: '“AI info”',
		labelKind: 'visible',
		labelSubtext:
			'Generated posts show it on the post; AI-only edits may place it in the menu. Ads can show it in “About this ad.”',
		signalSummary: 'Reads C2PA · IPTC · creator and advertiser signals',
		detectionSummary:
			'Meta reads industry-shared AI indicators, including “AI generated” information in C2PA and IPTC, and labels self-disclosed content. For ads, Meta labels content created or significantly edited with its tools and can automatically detect third-party AI through industry-standard signals.',
		metadataSignals: [
			'C2PA AI assertion',
			'IPTC DigitalSourceType',
			'Creator disclosure',
			'Meta advertising-tool and third-party AI signals'
		],
		disclosureDuty:
			'Self-disclose where required, especially for photorealistic people or events and for advertising.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'Meta — Labeling AI-generated content and manipulated media',
				url: 'https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/'
			},
			{
				label: 'Meta — GenAI transparency in ads',
				url: 'https://about.fb.com/news/2025/02/gen-ai-transparency-metas-ads-products/'
			}
		]
	},
	threads: {
		slug: 'threads',
		labelDisplay: '“AI info”',
		labelKind: 'visible',
		labelSubtext:
			'Meta places generated-content information on the post and AI-edit information in the menu.',
		signalSummary: 'Reads C2PA · IPTC · creator disclosure',
		detectionSummary:
			'Threads uses Meta’s shared provenance-labeling approach: industry-shared C2PA/IPTC AI indicators and creator self-disclosure can produce the “AI info” label.',
		metadataSignals: ['C2PA AI assertion', 'IPTC DigitalSourceType', 'Creator disclosure'],
		disclosureDuty: 'Use Threads’ AI labeling controls before sharing applicable AI content.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'Meta — Labeling AI-generated content and manipulated media',
				url: 'https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/'
			}
		]
	},
	google_search: {
		slug: 'google_search',
		labelDisplay: 'About this image provenance',
		labelKind: 'provenance',
		labelSubtext:
			'When supported data exists, image details can say whether media was camera-captured, AI-created or AI-edited.',
		signalSummary: 'Reads C2PA · SynthID · IPTC',
		detectionSummary:
			'Google image details can surface provenance from C2PA Content Credentials and SynthID, while IPTC fields in the image can also be shown. Google expanded SynthID and Content Credentials verification across Search surfaces in 2026.',
		metadataSignals: ['C2PA Content Credentials', 'SynthID watermark', 'IPTC image metadata'],
		disclosureDuty:
			'Preserve accurate provenance metadata when publishing images for the open web.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'Google Search Help — Find Google Image details',
				url: 'https://support.google.com/websearch/answer/9789430'
			},
			{
				label: 'Google — C2PA transparency in Search',
				url: 'https://blog.google/innovation-and-ai/products/google-gen-ai-content-transparency-c2pa/'
			}
		]
	},
	amazon_kdp: {
		slug: 'amazon_kdp',
		labelDisplay: 'No public reader label',
		labelKind: 'private',
		labelSubtext:
			'Disclosure is made to Amazon in the publishing flow, not as a standard reader badge.',
		signalSummary: 'Publisher disclosure to Amazon',
		detectionSummary:
			'Amazon requires publishers to inform KDP when text, images or translations are AI-generated. AI-assisted editing or refinement does not require the same disclosure. KDP does not document a C2PA/IPTC reader for this duty.',
		metadataSignals: ['Publisher disclosure in the KDP publishing flow'],
		disclosureDuty: 'Tell Amazon when a book contains AI-generated text, images or translations.',
		confidence: 'high',
		lastVerified: LAST_VERIFIED,
		sources: [
			{
				label: 'Amazon KDP — Content guidelines and AI disclosure',
				url: 'https://kdp.amazon.com/en_US/help/topic/G200672390'
			}
		]
	}
};

export function platformLabel(slug: string): PlatformLabelInfo {
	return platformLabelCatalog[slug] ?? platformLabelCatalog.generic;
}
