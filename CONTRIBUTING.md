# Contributing

1. Branch off `main`; never commit directly to `main`.
2. Run the full suite before proposing a change: `pytest -q` and
   `(cd frontend && npm run verify)`.
3. New behavior needs tests (smoke conclusion test for pipeline, surface test
   for routes).
4. Keep README, AGENTS.md, ARCHITECTURE.md, DESIGN.md consistent; record
   decisions in the Decision Log.
5. No secrets or `data/`/`demo_assets/` files in commits.