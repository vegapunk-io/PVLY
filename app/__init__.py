"""Provenably. AI content provenance & compliance prototype."""

try:
    # Lets every Pillow call (forensics, metadata, previews, removal validation) open HEIC/HEIF.
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:  # pragma: no cover
    pass
