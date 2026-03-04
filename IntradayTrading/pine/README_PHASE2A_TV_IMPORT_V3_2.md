# Phase2A S/R Watcher V3.2 (Reaction Cloud + Expedition) — TradingView Import

## File
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V3_2_REACTION_CLOUD.pine`

## What is new vs V3.1
- Adds an **expedition qualification lane** to capture extreme rejection levels (e.g., 98k/108k style) even when repeat touches are fewer.
- Wider default zone geometry for more realistic bands.

## New expedition inputs
- `Allow expedition qualification lane`
- `Expedition min move (ATR)`
- `Expedition window bars`
- `Expedition no-revisit bars`
- `Expedition score weight`

## Recommended first test (DIAG)
- Operating mode: `DIAG`
- Lookback bars: `3500` (for broad historical corroboration)
- Seed/Reaction wick bias: `0.60 / 0.65`
- Touch epsilon: `0.05`
- Zone caps: `0.06 pct`, `10 ATR`
- Expedition lane: ON (defaults)
- Diagnostic target price: `54000`, then `108000`
- Display focus price: match target during diagnosis

## Debug rows to inspect
- `Nearest to target`
- `Target dist %`
- `Nearest Q/U/L/E`
- `Nearest H/moveReq`
- `Exp lane on / ATR / win`

## Notes
- Uses `xloc.bar_time` plus right-axis price anchoring (`scale.right`) with a hidden price-scale anchor plot.
- Watcher-only; no trigger/entry logic.
- In `CERT`, diagnostics are suppressed but expedition lane can still contribute to qualification.
