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

## Preset profiles (new)
Use `Preset profile` to switch between bundled tuning sets without manually editing every knob.
Default is `auto`.

- `manual` → use all raw inputs exactly as entered.
- `auto` → auto-selects by current chart timeframe:
  - `>= ~1W` -> `1W macro`
  - `>= ~1D` -> `1D cert`
  - lower -> `4H intraday`
- `1D cert` -> production/clean-chart profile (longer windows, stronger dedupe, tighter retention, avgQ + visible-gap thinning).
- `1D recall` -> permissive recovery profile for missed swing anchors.
- `4H intraday` -> tighter intraday windows.
- `1W macro` -> broad regime windows.

Debug table row `Mode / profile` shows the active profile. Rows `W ...`, `E/rho/P/Q/dev`, `Retention...`, and `Cluster ...` show manual -> effective values where applicable.
Additional diagnostics include visible-zone suppression count and accepted/kept age-bucket splits.

## Fail reasons and dot colors
Enable `DIAG: show failed anchor dots` to plot failed anchors by reason.
If this is too dense, use:
- `DIAG failed-dot scope` = `date-window` or `inspect-only`
- optionally enable `DIAG: use date window for failed dots` with `DIAG window start/end`

## Runtime safety (new)
If TradingView shows `Loop takes too long (> 500 ms)`, reduce workload using:
- `Compute budget: max bars scanned` (default 1200)
- `Compute budget: candidate stride bars` (set 2 or 3 for quick diagnostics)

Debug row `Lookback raw/safe/req` shows the effective scan size.

- **Red**: `FAIL_E_MIN`
- **Orange**: `FAIL_R_RATIO`
- **Yellow**: `FAIL_PERSIST`
- **Teal**: `FAIL_REVISIT`
- **Blue**: `FAIL_DEV_OUTLIER`
- **Fuchsia**: `FAIL_SCORE_Q`
- **Gray**: `FAIL_GAP_SUPPRESS`
- **Purple**: `FAIL_RETAIN_DROP`

Kept anchors are plotted in aqua with score-dependent shading.

Note: accepted (aqua) and failed-dot budgets are decoupled, so changing failed-dot scope should not reduce aqua-dot count anymore.

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
- `deviationInvalidATR = 2.5`
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
- Reversal is measured in a forward window **after** excursion timing (`tE`) to reduce false misses on slower swing reversals.
- `Retest decay` is optional and off by default to keep certification runs easy to compare.
- If you are looking for deviation threshold in UI, the field label is: `deviationInvalidATR (outlier invalid, ATR)`.
- For noisy charts, tune `Q_min`, `anchorRetentionPercent`, `minClusterScore`, and `minClusterAvgQ` before tightening candidate veto.
- Use `Visible-zone min gap` settings to prevent stacked displayed zones in the same price neighborhood.
