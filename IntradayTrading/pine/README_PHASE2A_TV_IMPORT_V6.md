# Phase2A S/R Watcher V6 (Foxian Excursion/Reversal Model) — TradingView Import

## File
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V6_FOXIAN_EXCURSION_REVERSAL_MODEL.pine`

## Model summary
V6 shifts anchor quality from candle geometry to excursion/reversal behavior:
1) evaluate both sides per bar (`high` for resistance candidate, `low` for support candidate),
2) compute path metrics `E`, `tE`, `R`, `rho=R/max(E,eps)` in ATR units,
3) gate with persistence, revisit, outlier deviation, and `Q` score,
4) apply deterministic retention with side-aware gap suppression,
5) cluster kept anchors into sparse zones with baseline zone state.

Candidate filters (`local-extrema`, min range ATR) are soft by default. Use `Strict candidate veto` only when you explicitly want hard blocking for `C_soft=false` bars.

## Core windows (time-normalized)
All windows are set in hours and converted to bars on the active timeframe:
- `W_move_h`
- `W_reversal_h`
- `W_persist_h`
- `W_revisit_h`
- `W_gap_same_h`
- `W_gap_opp_h`

This keeps behavior portable across 1D/1W/lower TF replay.

## Fail reasons and dot colors
Enable `DIAG: show failed anchor dots` to plot failed anchors by reason.

- **Red**: `FAIL_E_MIN`
- **Orange**: `FAIL_R_RATIO`
- **Yellow**: `FAIL_PERSIST`
- **Teal**: `FAIL_REVISIT`
- **Blue**: `FAIL_DEV_OUTLIER`
- **Fuchsia**: `FAIL_SCORE_Q`
- **Gray**: `FAIL_GAP_SUPPRESS`
- **Purple**: `FAIL_RETAIN_DROP`

Kept anchors are plotted in aqua with score-dependent shading.

## Inspect one candle (DIAG)
Use:
- `DIAG: inspect one candle`
- `DIAG inspect candle time`
- `DIAG inspect side`

Debug table shows for each side:
- gate booleans: `C`, `E`, `R`, `P`, `N`, `D`, `Q`, `G`
- key metrics: `E`, `tE`, `R`, `rho`, `persist`, `revisit`, `dev`, `Q`
- final reason code after retention stage.

## Suggested baseline settings (spec start point)
- `W_move_h = 96`
- `W_reversal_h = 96`
- `W_persist_h = 72`
- `W_revisit_h = 96`
- `E_min = 2.5`
- `rho_min = 0.25`
- `persist_min = 4`
- `revisitTolATR = 0.20`
- `persistTolATR = 0.60`
- `Q_min = 58`
- `W_gap_same_h = 120`
- `W_gap_opp_h = 24`
- `anchorRetentionPercent = 25%`
- `maxAnchorsKept = 180`
- `minClusterPoints = 3`
- `minClusterScore = 7.0`
- `clusterTolPct = 0.018`
- `maxDisplayZones = 12`

## Notes
- Zone states are baseline placeholders for portability: `candidate`, `active`, `weakening`, `broken`.
- `Retest decay` is optional and off by default to keep certification runs easy to compare.
- For noisy charts, tune `Q_min`, `anchorRetentionPercent`, and `minClusterScore` before tightening candidate veto.
