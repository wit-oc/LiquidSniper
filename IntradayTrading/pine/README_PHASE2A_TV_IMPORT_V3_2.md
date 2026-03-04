# Phase2A S/R Watcher V3.2 (Reaction Cloud + Expedition) — TradingView Import

## File
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V3_2_REACTION_CLOUD.pine`

## What is new vs V3.1
- Adds an **expedition qualification lane** to capture extreme rejection levels (e.g., 98k/108k style) even when repeat touches are fewer.
- Wider default zone geometry for more realistic bands.
- Adds direct `Zone width multiplier` (single-knob width tuning).
- Adds `Merge across sides (level-is-level)` to reduce clustered duplicates.
- DIAG target controls are decoupled from selection by toggle.
- Adds DIAG cloud-point overlay (dots) so you can inspect raw cloud anchors directly on chart.

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
- Zone width multiplier: `1.25`
- Touch epsilon: `0.05`
- Zone caps: `0.06 pct`, `10 ATR`
- Merge overlap / spacing: `0.50 / 1.80`
- Merge across sides: `ON`
- Expedition lane: ON (defaults)
- DIAG target affects selection: `OFF` (for unbiased baseline)
- DIAG force nearest visible: `OFF` (only turn on when isolating a target)
- DIAG show cloud points: `ON`
- DIAG cloud point mode: `reacted+expedition`
- DIAG show outlier cloud points: `ON`
- Diagnostic target price: `54000`, then `108000`
- Display focus price: match target during diagnosis

## Debug rows to inspect
- `Nearest to target`
- `Target dist %`
- `Nearest Q/U/L/E`
- `Nearest H/moveReq`
- `Seed/React wick / W`
- `Merge/Spacing/xSide`
- `Exp ON / ATR / win / nrv`
- `Cloud mode / max`
- `Cloud T/R/E/O` (touch / reacted / expedition / outlier)
- `Cloud emitted`

## Notes
- Uses `xloc.bar_time` plus right-axis price anchoring (`scale.right`) with a hidden price-scale anchor plot.
- Watcher-only; no trigger/entry logic.
- In `CERT`, diagnostics are suppressed but expedition lane can still contribute to qualification.
