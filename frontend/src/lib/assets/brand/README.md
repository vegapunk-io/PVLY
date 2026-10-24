# Provenably primary brand mark

`provenably-mark.png` is the canonical primary Provenably logo and brand icon for the website.
The founder supplied the original artwork on 2026-10-24 and then directed that the website asset
be forced to Provenably's Zapier-derived palette rather than retaining the supplied file's native
orange (DESIGN P-018).

## Source and canonical files

- Untouched supplied source: `source/icons8-checkmark-64.png`
  - Dimensions: 64×64 PNG with transparency
  - Native dominant orange: `#fd7e14`
  - SHA-256: `2062438f3c73049755b95d7c8a4bf2d57948835035cfa05860ab5e628c61e2c6`
- Canonical website asset: `provenably-mark.png`
  - Dimensions: 64×64 PNG with the source alpha channel copied pixel-for-pixel
  - Every RGB pixel is forced to the website primary: `#ff4f00`
  - SHA-256: `ab973904984d028911795bc294a14243a53ff448aa24b7210e12d8d9c832c008`

Only the canonical palette-forced file may be used in the product. Render it through
`frontend/src/lib/components/BrandMark.svelte` for interface lockups and directly as the
production favicon. `app/static/provenably-mark.png` is a byte-identical mirror of the canonical
file for the legacy Jinja fallback. Do not use the native-orange source in the UI.

## Regeneration

Run from this directory:

```bash
convert source/icons8-checkmark-64.png -alpha extract /tmp/provenably-brand-alpha.png
convert -size 64x64 'xc:#FF4F00' /tmp/provenably-brand-alpha.png -alpha off \
  -compose CopyOpacity -composite provenably-mark.png
```

Then copy `provenably-mark.png` to `app/static/provenably-mark.png` and update the canonical
SHA-256 above if the encoder output changes.

Preserve the source geometry, transparent padding, and alpha exactly. Apart from the mandated
`#fd7e14` → `#ff4f00` palette mapping, do not recolor, trace, crop, stretch, mask, outline, add
a background, or place the mark inside the retired orange rounded-square treatment. The check is
a transparent negative-space cut-out, so the surface behind it determines the visible check color.
