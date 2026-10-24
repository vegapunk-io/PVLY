# Platform marks

These destination marks were supplied by the founder on 2026-10-24. The untouched 512×512 PNG
files are retained in `source/`. The web app imports only the 144×144 lossless WebP derivatives in
this directory; they were resized with a Lanczos filter without cropping, recoloring, masking or
changing aspect ratio.

Regenerate a derivative with:

```bash
convert source/<platform>.png -filter Lanczos -resize 144x144 -define webp:lossless=true <platform>.webp
```

## Source checksums

| Platform  | Source SHA-256                                                     |
| --------- | ------------------------------------------------------------------ |
| Facebook  | `162595e670f92c2714566fcd7b788db4777ff2bd4bfe3b950695cd7036e5e09f` |
| Instagram | `3f7fd3ef4fb4e933638c1c6f58a6d2ea893fada278c99088cc5deb6e9cd24268` |
| LinkedIn  | `20601a43f0396c4e662cd07d738c20c54daa5edf3d91e0f31f090cdcda71a512` |
| Pinterest | `7e4d54c91fe30adf5b76ff76cbf5953e204f7b38a5657730ffc746b2cb066d9c` |
| Reddit    | `843cd87bbcdd3b88b365f36e1738da7da82fb5e5df7195a92fbf13bf1e08825d` |
| YouTube   | `f37752d65355141b3aed7fabe6ddd336ef4ee1b7b9482dff15227f9827dacda1` |

Platform names and marks belong to their respective owners. PVLY uses them nominatively to
identify export destinations; their presence does not imply endorsement or partnership.
Destinations without a founder-supplied asset use a neutral PVLY monogram rather than a recreated
trademark.
