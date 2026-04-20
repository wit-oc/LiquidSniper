# Daily Swing v1 TV Alpha Scaffold — Implementation Note

Date: 2026-02-26
Repo: LiquidSniper

## Files changed
- `tradingview/indicator/liquidsniper_confluence_indicator_v1_fidelity.pine`
- `tradingview/strategy/liquidsniper_confluence_strategy_v1_fidelity.pine`

## What was added

### Indicator scaffold
- Added reason code constants: `HG`, `BG`, `RG`, `TM`, `SR` (+ `OK`).
- Added deterministic gate pipeline skeleton:
  - `HG-1..HG-5` booleans for long/short
  - `RG` stage currently mapped to session/time gate.
- Switched trigger decision to gate-pass model (`long_gate_pass` / `short_gate_pass`).
- Added diagnostics fields:
  - `decision`
  - `first_fail_reason`
  - `all_reasons`
  - `projected_r` (scaffold placeholder)
  - `flag_tp1/flag_tp2/flag_tp3/flag_be` (indicator placeholders)
- Extended debug table to emit diagnostic fields.
- Included TODO markers where stricter/fully wired signals are pending.

### Strategy scaffold
- Added reason code constants: `HG`, `BG`, `RG`, `TM`, `SR` (+ `OK`).
- Added deterministic gate pipeline skeleton:
  - `HG-1..HG-5` for long/short qualification.
  - `RG` includes time gate + daily risk/cap controls.
- Added daily loss circuit breaker state:
  - `enable_daily_loss_cb`
  - `max_daily_loss_r`
  - per-day `day_realized_r` tracking (scaffold via netprofit delta / entry risk budget).
- Added optional daily trade cap:
  - `enable_daily_trade_cap`
  - `max_daily_trades`
  - per-day trade counting and gating.
- Replaced single-TP exit with TP ladder scaffold:
  - TP1/TP2/TP3 exits (33%/33%/34%)
  - TP1 => break-even activation path
  - explicit flat at TP3 (`TP3_FLAT`) to enforce no runner beyond TP3.
- Added diagnostics fields/emit scaffolding:
  - `decision`, `first_fail_reason`, `all_reasons`, `projected_r`
  - TP hit flags + BE active flag visual emissions.
- Included TODO markers where full behavior/qualification models are not yet wired.

## Local checks run
- `make lint` -> `No linter configured yet`

## Notes
- This is a scaffold pass for TV Alpha code-completeness, not a TradingView compile/validation pass.
- Changes were kept localized to v1 fidelity Pine files for reversibility.
