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

This is a deterministic **skeleton baseline**:
- Inputs and structure are production-shaped.
- Some signal factors are placeholders/proxies and should be replaced by exact bot-equivalent formulas where possible.

See `docs/TRADINGVIEW_PINE_IMPLEMENTATION_GUIDE.md` for full details.
