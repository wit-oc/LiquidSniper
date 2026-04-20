# First Archive Pass (2026-04-19)

This archive bucket contains the first real repo-refocus move after the Surveyor / Arbiter boundary was declared.

Intent:
- remove obviously non-core legacy docs from the top-level `docs/` surface
- preserve them in-place under explicit archive buckets
- avoid breaking live code paths that still depend on legacy code or artifact directory names

## Buckets

### `telegram-mobchart/`
Historical docs from the older Telegram / Mobchart-centered repo identity.

### `paper-runtime/`
Historical docs from the older paper-runtime / paper-daemon / execution-control lane.

### `tradingview/`
Historical docs from the older TradingView-heavy parity and Pine branch-out lane.

## Important constraint

This archive pass is intentionally **non-destructive for live code paths**.
Several legacy code and artifact surfaces still exist in-place because tests, tooling, or modules still reference their current paths.
See:
- `docs/LEGACY_SURFACES_STATUS_2026-04-19.md`
