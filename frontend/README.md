# Provenably frontend

Production SvelteKit implementation of the founder-approved design in [`../DESIGN.md`](../DESIGN.md).

## Stack

- SvelteKit 3 + Svelte 5 runes
- TypeScript in strict mode
- Vite 8
- Static adapter with Brotli/Gzip precompression
- Self-hosted variable Inter; JetBrains Mono variable is code-split to data-heavy routes
- Custom CSS design tokens/components—no CSS framework or icon runtime
- FastAPI remains the JSON API and, when `frontend/build/` exists, production static host

## Local development

Use Node 22 and npm 11 or newer. This repository currently pins npm 12.2.1 in
`packageManager`; npm 10 can fail while resolving Vitest's optional peer tree.

```bash
npm install
npm run dev
```

The Vite dev server binds to `0.0.0.0:5173` and proxies relative API calls to FastAPI at
`http://127.0.0.1:8000`:

- `/v1/*`
- `/api/*`
- `/demo-assets/*`
- `/health`

Override the proxy target with `PROVENABLY_API_ORIGIN`.

In another terminal, from the repository root:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Verification

```bash
npm run verify
```

That runs Svelte/TypeScript checks, Prettier, ESLint, Vitest, the production build and
`scripts/check-bundle-budget.mjs`.

## Production shape

```bash
npm run build
cd ..
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

FastAPI serves `frontend/build/` for the Svelte routes while preserving `/v1/*`, OpenAPI and
health semantics. The legacy Jinja templates remain as a no-build fallback during migration.

## Performance rules

- Public pages are prerendered; the landing and pricing pages disable client-side routing JS.
- Dynamic reports and registry details use the static fallback and fetch only their own data.
- Route code must stay under the automated bundle budget.
- Do not add Tailwind, a component library, analytics, webfonts from a CDN or decorative images
  without a dated decision in `../DESIGN.md` or `../ARCHITECTURE.md`.
- Motion is limited to progress/loading feedback and must honor `prefers-reduced-motion`.
