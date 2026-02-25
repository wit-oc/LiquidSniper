# TradingView v1 Test Checklist

Use this exact checklist before adopting v1 scripts.

## Artifacts under test
- `tradingview/indicator/liquidsniper_confluence_indicator_v1_fidelity.pine`
- `tradingview/strategy/liquidsniper_confluence_strategy_v1_fidelity.pine`

## 1) Compile + setup checks
- [ ] Open indicator script in TradingView Pine Editor.
- [ ] Confirm compile success (no errors/warnings requiring code edits).
- [ ] Open strategy script in TradingView Pine Editor.
- [ ] Confirm compile success (no errors/warnings requiring code edits).
- [ ] Add indicator to chart and ensure EMA/zone plots render.
- [ ] Add strategy to chart and ensure entries/exits appear.

Required metric:
- **Compile failures = 0**

## 2) Profile matrix checks (C/I/S)
For each profile (C, I, S):
- [ ] Verify TF mapping behavior is sensible for the active chart.
- [ ] Verify watch labels appear only when score >= watch threshold.
- [ ] Verify trigger labels appear only when score >= trigger threshold + chop/candle constraints.
- [ ] Verify debug table values are populated and coherent.

Required metrics:
- **Profile pass count = 3/3**
- **Any broken profile = 0**

## 3) Mentorship-rule behavior checks
- [ ] Confluence stack: score changes when trend/structure/retest/chop conditions change.
- [ ] Structure: BoS/CHoCH events fire on visible break events.
- [ ] First retest: only first armed retest receives retest credit.
- [ ] Chop filter: high-CI/low-ADX windows suppress triggers.
- [ ] Candle-close rule: with toggle ON, intrabar-only setups do not trigger.

Required metrics:
- **Rule checks passed = 5/5**

## 4) Strategy risk-model checks
- [ ] Long stop is placed at structural invalidation fallback-guarded by ATR.
- [ ] Short stop is placed at structural invalidation fallback-guarded by ATR.
- [ ] Single full TP is used (no mandatory partial ladder).
- [ ] Cooldown prevents immediate over-trading re-entry.

Required metrics:
- **Risk checks passed = 4/4**

## 5) Backtest runs (minimum set)
Run both v0 and v1 strategy with matching settings on:
- Symbols: BTCUSDT, ETHUSDT, SOLUSDT
- Timeframes: 15m, 1h, 4h
- Window: last 180 days
- Profiles: C, I, S

Capture per run:
- Net profit %
- Profit factor
- Max drawdown %
- Win rate %
- # trades
- Stop-out ratio (stop exits / trades)

Required aggregate metrics (v1 vs v0):
- [ ] Choppy-window trade count reduced >= 15%
- [ ] Stop-out ratio reduced >= 10%
- [ ] Profit factor >= 95% of v0 (target >= 100%)
- [ ] Max drawdown <= 105% of v0

## 6) Alert plumbing checks
- [ ] Create alert for `LS v1 Long Watch`
- [ ] Create alert for `LS v1 Short Watch`
- [ ] Create alert for `LS v1 Long Trigger`
- [ ] Create alert for `LS v1 Short Trigger`

Required metrics:
- **Alert creation success = 4/4**

## 7) Sign-off block
- Tester:
- Date:
- TradingView account/workspace:
- Result: PASS / FAIL
- Notes / anomalies:
