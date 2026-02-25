# TradingView Pine Implementation Guide (LiquidSniper)

## 1) Purpose

This guide defines how to implement, tune, and operate the LiquidSniper TradingView indicator + strategy pair while preserving parity with bot-side policy.

Primary goals:
- Surface actionable regions and watch/trigger opportunities for manual users.
- Backtest a codified version of the same logic on TradingView.
- Keep Pine and bot behavior auditable and versioned.

## 2) Files and Roles

- `tradingview/indicator/liquidsniper_confluence_indicator.pine`
  - Human-facing signal surface.
  - Regions, score states, labels, and alert conditions.
- `tradingview/strategy/liquidsniper_confluence_strategy.pine`
  - Backtesting harness.
  - Signal layer + deterministic entries/exits/risk controls.
- `tradingview/config/liquidsniper_pine_profiles.json`
  - Config mirror for `C` (scalp), `I` (intraday), `S` (swing).

## 3) Input Reference

### 3.1 Metadata
- `ls_version`: semantic version string for the Pine release.
- `config_profile_id`: profile identity (`C`, `I`, `S`) for parity checks.

### 3.2 Mode / Adaptation
- `trade_style`: `Auto | Scalp | Intraday | Swing`
- `enable_tf_auto_adjust`: if true, score thresholds scale by chart context.
  - Scalp: stricter responsiveness (`*0.95` threshold factor).
  - Intraday: neutral (`*1.00`).
  - Swing: stricter quality (`*1.05`).

### 3.3 Core signal controls
- EMA lengths (`ema_fast_len`, `ema_slow_len`) for trend proxy.
- ATR settings (`atr_len`, `atr_zone_mult`) for dynamic region construction.
- Chop gates (`chop_soft_max`, `chop_hard_max`) for volatility quality.
- `watch_threshold`, `trigger_threshold` for state transitions.

### 3.4 Weighted confluence factors
Each factor can be toggled and weighted:
- HTF Regime (`w_htf_regime`)
- SR Retest (`w_sr_retest`)
- LTF Structure Shift (`w_ltf_shift`)
- Volatility Regime (`w_vol_regime`)

Final score is a normalized weighted sum:

`score = sum(factor_score * factor_weight) / sum(active_weights)`

### 3.5 Strategy-only risk controls
- Direction toggles: `allow_longs`, `allow_shorts`
- Risk mode: `ATR` or `Percent`
- `atr_stop_mult`, `rr_take_profit`, `stop_loss_pct`
- `qty_pct` position sizing
- `cooldown_bars` entry throttle

## 4) Algorithms (Current Baseline)

## 4.1 Confluence weighting model
The weighting shape mirrors replay-harness context scoring philosophy:
- HTF regime: 35%
- SR retest: 30%
- LTF structure shift: 20%
- Volatility regime: 15%

Reference formula lineage: `liquidsniper/core/replay_harness.py` (`score_context`).

## 4.2 Profile timeframes and policy gates
Default profile mappings mirror policy defaults:
- `S`: `1D -> 4H -> [1H, 15m]`
- `I`: `4H -> 1H -> [15m, 5m]`
- `C`: `1H -> 15m -> [5m, 1m]`

Reference: `liquidsniper/core/paper_policy.py` and `liquidsniper/core/replay_harness.py`.

## 4.3 Volatility/chop treatment
Current Pine baseline uses a deterministic chop proxy from ATR/range and gates with:
- soft max: quality reduction
- hard max: trigger suppression

This maps conceptually to paper-policy soft/hard HTF chop gates.

## 4.4 Watch vs Trigger states
- **Watch**: score >= watch threshold
- **Trigger**: score >= trigger threshold + trend alignment + chop pass

## 5) How to Use in TradingView

1. Open TradingView chart.
2. Pine Editor -> paste indicator script -> Save -> Add to chart.
3. Configure profile + thresholds.
4. Enable alerts from built-in alert conditions:
   - LS Long/Short Watch
   - LS Long/Short Trigger

For strategy backtesting:
1. Paste strategy script in Pine Editor.
2. Add to chart and open Strategy Tester.
3. Set market/session settings and commission/slippage assumptions.
4. Backtest across symbols/time windows.
5. Record result snapshots under `artifacts/tradingview/`.

## 6) Backtesting Playbook

Recommended baseline runs:
- BTCUSDT, ETHUSDT, SOLUSDT
- 1m/5m/15m/1H/4H/1D (profile-appropriate)
- Rolling windows: 90d, 180d, 365d

Track at minimum:
- Net profit
- Profit factor
- Max drawdown
- Win rate
- Avg trade
- Expectancy per trade
- Trade count (avoid overfitting on tiny N)

## 7) Integration Model (Bot <-> Pine)

## 7.1 Single source of truth contract
Operational rule:
- Bot-side policy/scoring is source-of-truth.
- Pine uses synchronized mirror config + version tags.

When policy changes:
1. Update bot logic/config.
2. Update `tradingview/config/liquidsniper_pine_profiles.json`.
3. Update Pine defaults and bump `ls_version`.
4. Log release notes and parity checks.

## 7.2 Parity checks
For controlled samples, compare:
- inferred trend/bias state
- confluence component states
- watch/trigger classification
- reject reasons (where representable)

## 8) Limitations (Current Skeleton)

- Some factor implementations are intentionally proxy-based and not yet exact mirror of paper-daemon internals.
- Pine cannot directly import Python runtime outputs; parity is process/governance based.
- TradingView strategy fills are simulated and sensitive to slippage/session assumptions.

## 9) Next Hardening Steps

1. Replace proxy factors with exact deterministic formulas where feasible.
2. Add regime/session filters aligned with production policy gates.
3. Add optional `strategy.risk.max_drawdown` style controls.
4. Add one-click profile presets (`C/I/S`) in Pine via grouped defaults.
5. Add artifact template for reproducible backtest reports.

## 10) Source References

- `liquidsniper/core/paper_policy.py`
- `liquidsniper/core/replay_harness.py`
- `docs/TRADING_STRATEGY_RUNBOOK_V1.md`
- `docs/HYBRID_CONFLUENCE_PIPELINE_SPEC.md`
