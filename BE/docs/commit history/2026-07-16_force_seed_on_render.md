2026-07-16 — Force seed DB on startup for free-plan Render deployments

Summary:
- Modified `BE/scripts/init_db.sh` to always copy `BE/data/localhub_filled.db` to `/data/localhub.db` on container start (overwrites existing DB).
- Updated [BE/docs/RENDER_DEPLOY.md] to document the new behavior and rationale (ensure seed applied on each start under free plan).

Files changed:
- BE/scripts/init_db.sh
- BE/docs/RENDER_DEPLOY.md

Notes:
- This makes seed application idempotent by design for this deployment strategy (always overwritten).
- If you'd prefer an opt-in behavior, we can add an environment variable (e.g., `FORCE_SEED=true`) instead of unconditional overwrite.
