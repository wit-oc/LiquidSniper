# LiquidSniper TradingView Foundation

This folder is the PineScript branch-out for LiquidSniper.

## Structure

- `indicator/liquidsniper_confluence_indicator.pine`
  - Manual-trader overlay (regions + watch/trigger labels + alerts).
- `strategy/liquidsniper_confluence_strategy.pine`
  - Backtestable strategy wrapper around the same confluence model.
- `config/liquidsniper_pine_profiles.json`
  - Canonical profile defaults mirror for Pine (`C`, `I`, `S`).

## Design Goal

Keep **bot logic** and **Pine logic** in parallel by:
1. Maintaining profile defaults in a versioned config file.
2. Exposing `ls_version` + `config_profile_id` in Pine inputs.
3. Releasing Pine updates in lock-step with policy/scoring changes in the bot.

## Current Status

This is a deterministic **phase-2 parity baseline**:
- Inputs/structure are production-shaped.
- Score equation, secondary-hit model, profile TF mapping, and chop soft/hard penalty now mirror bot logic closely.
- Remaining gaps (SR-zone DB parity, throttle/idempotency parity) are documented explicitly.

See `docs/TRADINGVIEW_PINE_IMPLEMENTATION_GUIDE.md` for full details.

## Release Notes

### v1-fidelity (new)
- Added versioned mentorship-fidelity scripts (no v0 overwrite):
  - `indicator/liquidsniper_confluence_indicator_v1_fidelity.pine`
  - `strategy/liquidsniper_confluence_strategy_v1_fidelity.pine`
- v1 emphasizes Foxian-aligned behavior: confluence stack scoring, swing-based BoS/CHoCH proxy, first-retest gating, and anti-chop filtering.
- Added validation/governance docs:
  - `docs/TRADINGVIEW_MENTORSHIP_FIDELITY_MAPPING_V1.md`
  - `docs/TRADINGVIEW_V0_RETIREMENT_CRITERIA.md`
  - `docs/TRADINGVIEW_V1_TEST_CHECKLIST.md`

### v1.1 risk-sizing update
- Strategy now supports `sizing_mode` with legacy `percent_of_equity` and new `risk_based` sizing.
- `risk_based` mode sizes entries from invalidation distance (`qty = risk_usd / stop_distance`) with defensive guards for invalid/near-zero stops.
- Added confluence-tiered risk controls:
  - Low confidence default risk = 1%
  - High confidence default risk = 5%
  - Threshold-controlled high-confidence routing.
- Added optional profile risk caps (default C=1%, I=5%, S=5%) plus manual cap override inputs.
