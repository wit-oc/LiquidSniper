# Phase2A S/R Watcher V6 (Foxian Excursion/Reversal Model) — TradingView Import

## File
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V6_FOXIAN_EXCURSION_REVERSAL_MODEL.pine`

## Model summary
V6 shifts anchor quality from candle geometry to excursion/reversal behavior:
1) evaluate both sides per bar (`high` for resistance candidate, `low` for support candidate),
2) compute path metrics `E`, `tE`, `R`, `rho=R/max(E,eps)` in ATR units,
3) gate with persistence, revisit, outlier deviation, and `Q` score,
4) compute launch significance (`Q_launch`) and blended `rankScore` for retention ordering,
5) apply deterministic retention with side-aware gap suppression,
6) cluster kept anchors into sparse zones with baseline zone state.

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
Default is `manual`, and manual defaults are mapped to the current `1D cert` baseline so you can tweak directly without profile override confusion.

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

### Launch-aware ranking (V6.8)
New launch inputs:
- `useLaunchRanking`
- `launchHoldMult`
- `launchPreRangeMult`
- `launchERefATR`
- `launchBreakRefATR`
- `launchEdgeFracMax`
- `launchPromoteMinBreakATR`
- `launchBlend`
- `launchRescueGraceQ`
- `launchRescueMinQ`

Behavior:
- Existing score is preserved as local quality (`Q_local`).
- Launch metrics generate `Q_launch` from hold excursion, pre-range breakout, and edge-position quality.
- Retention ranking uses `rankScore` (blended `Q_local` + `Q_launch`) only when launch eligibility passes.
- `minClusterAvgQ` still uses local average (`Q_local`) to avoid broad funnel loosening.
- `4H intraday` profile keeps launch ranking off for near-backward behavior.
- Narrow major rescue is enabled only for `FAIL_SCORE_Q` candidates that satisfy all other gates plus launch thresholds.

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
- key metrics: `E`, `tE`, `R`, `rho`, `persist`, `revisit`, `dev`, `Q_local`, `Q_launch`, `rankScore`, `E_hold`, `breakBeyondATR`, `edgeFrac`
- final reason code after retention stage.

For sharing tuned manual configs back for preset baking, use the bottom rows:
- `Export cfg A`
- `Export cfg B`
- `Export cfg C/D`

Send those row values (or a screenshot including them).

## Manual defaults (mapped to 1D cert baseline)
- `W_move_h = 240`
- `W_reversal_h = 240`
- `W_persist_h = 144`
- `W_revisit_h = 240`
- `W_gap_same_h = 168`
- `W_gap_opp_h = 24`
- `E_min = 3.0`
- `rho_min = 0.24`
- `persist_min = 3`
- `revisitMaxCount = 1`
- `revisitTolATR = 0.20`
- `persistTolATR = 0.60`
- `Q_min = 60`
- `deviationInvalidATR = 3.5`
- `anchorRetentionPercent = 12%`
- `maxAnchorsKept = 180`
- `clusterTolPct = 0.020`
- `clusterTolATR = 1.00`
- `zoneWidthMult = 1.35`
- `minClusterPoints = 3`
- `minClusterScore = 7.0`
- `minClusterAvgQ = 55`
- `maxDisplayZones = 8`
- `visibleMinGapPct = 0.015`
- `visibleMinGapATR = 1.00`
- `useLaunchRanking = true`
- `launchHoldMult = 3.0`
- `launchPreRangeMult = 1.0`
- `launchERefATR = 8.0`
- `launchBreakRefATR = 2.0`
- `launchEdgeFracMax = 0.35`
- `launchPromoteMinBreakATR = 0.25`
- `launchBlend = 0.60`
- `launchRescueGraceQ = 5.0`
- `launchRescueMinQ = 70.0`

## Preset launch defaults
- `1D cert`: launch ranking ON, `hold=3.0`, `pre=1.0`, `Eref=8.0`, `Bref=2.0`, `edgeMax=0.35`, `promoteMinBreak=0.25`, `blend=0.60`, `rescueGrace=5.0`, `rescueMinQ=70.0`.
- `1D recall`: launch ranking ON, `hold=3.0`, `pre=1.0`, `Eref=8.0`, `Bref=1.5`, `edgeMax=0.45`, `promoteMinBreak=0.15`, `blend=0.55`, `rescueGrace=7.0`, `rescueMinQ=65.0`.
- `4H intraday`: launch ranking OFF.
- `1W macro`: launch ranking ON, `hold=4.0`, `blend=0.70` (other launch fields inherit manual unless overridden).

## Notes
- Zone states are baseline placeholders for portability: `candidate`, `active`, `weakening`, `broken`.
- Reversal is measured in a forward window **after** excursion timing (`tE`) to reduce false misses on slower swing reversals.
- `Retest decay` is optional and off by default to keep certification runs easy to compare.
- If you are looking for deviation threshold in UI, the field label is: `deviationInvalidATR (outlier invalid, ATR)`.
- For noisy charts, tune `Q_min`, `anchorRetentionPercent`, `minClusterScore`, and `minClusterAvgQ` before tightening candidate veto.
- Use `Visible-zone min gap` settings to prevent stacked displayed zones in the same price neighborhood.
