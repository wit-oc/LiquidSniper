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
