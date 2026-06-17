# Unity UTM V7 Long-History Robustness Verdict

Date: 2026-05-30

## Verdict

Do not confirm `QS3 + 5m only` as a robust Unity UTM V7 implementation.

The validation run succeeded mechanically, but it failed the required historical-coverage gate. TradingView returned only `Mar 15, 2026 — May 30, 2026` for every 5m symbol, even after:

- disabling the Pine backtest window;
- setting Strategy Tester date range to `Entire history` / `All`;
- exporting 17/17 requested 5m symbol slots successfully.

That is about 78 calendar days of 5m Strategy Tester coverage, not the required one year or multi-year history. The correct verdict is therefore `not enough historical coverage`, not acceptance or rejection of the trading edge.

## Validation Run

Command:

```bash
node tradingview/scripts/tv_pine_text_matrix.mjs --cwd /Users/seanplatthy/Documents/Github/LiquidSniper --config tradingview/strategy/artifacts/v7_long_history_robustness/tv_long_history_robustness_runs.json --run v7-long-history-qs3-5m --settings-committed --strategy-report-date-range "Entire history"
```

Coverage:

- 17/17 expected 5m slots exported.
- 0 missing slots.
- 0 failed slots.
- Source mappings were applied per symbol.
- Strategy Tester date range selection reported `All`.
- Generated validation Pine has `Minimum Quality Score To Trade = 3`.
- Generated validation Pine has `Enable Backtest Window = false`.

## Historical Coverage Gate

| TF | Required minimum | Rows meeting minimum | Rows capped | Result |
|---|---:|---:|---:|---|
| 5m | 365 days | 0/17 | 17/17 | fail |

All 17 5m rows returned the same report range:

`Mar 15, 2026 — May 30, 2026`

This means the prior promising `QS3 + 5m only` profile is still a short-window hypothesis. It cannot be treated as proven across market cycles, years, or broader historical regimes.

## Short-Window Metrics

These metrics are useful only as short-window context:

| Scope | Trades | P&L | PF | Win % | DD % |
|---|---:|---:|---:|---:|---:|
| All 17 symbols | 196 | 5145.61 | 1.633 | 59.7 | 8.24 |
| Prior admitted controls | 80 | 3878.68 | 2.682 | 72.5 | 3.45 |
| Prior failed controls | 24 | 382.69 | 1.377 | 50.0 | 4.79 |
| Major controls | 14 | 406.85 | 1.533 | 57.1 | 4.25 |
| Perp route probes | 78 | 477.39 | 1.118 | 50.0 | 8.46 |
| Failed+perp controls | 102 | 860.08 | 1.170 | 50.0 | 10.74 |

The short-window result remains directionally positive, but it is not enough evidence. VIRTUAL was materially negative inside the same capped window, and several assets have thin trade counts.

## Comparison To Prior QS3 5m Finding

The prior admission/routing spike found `QS3 + 5m only` at 171 trades, 5422.28 P&L, 1.773 PF, 63.2% win rate, and 7.27% drawdown across the earlier 16-symbol matrix.

This long-history attempt used the same QS3 logic, added VIRTUAL, disabled the Pine backtest window, and selected Strategy Tester `All`. It still returned the same capped 5m range and produced 196 trades, 5145.61 P&L, 1.633 PF, 59.7% win rate, and 8.24% drawdown.

So the short-window profile remains directionally consistent, but the run did not produce the historical depth needed to upgrade the finding from promising to robust.

## Control Decision

The 15m control was not run in this pass because the goal explicitly required aborting the verdict if 5m history was materially capped under one year for most symbols. The primary 5m coverage failed that gate on every symbol.

This does not make 15m attractive. Prior V7 evidence already showed 15m as a weak or destructive surface, and the present goal was to validate the current best 5m candidate rather than revive 15m.

## Recommendation

Do not tune or add filters from this result.

The next valid path is to obtain deeper 5m history inside TradingView before making a final strategy verdict:

1. Use TradingView Deep Backtesting if the account/UI exposes enough 5m history for this strategy and the automation can export it reliably.
2. If Deep Backtesting cannot be automated, use another TradingView-sourced export path that preserves the same proprietary/input.source metrics used by this Pine strategy.
3. For long-running majors like BTC, ETH, SOL, BNB, LTC, XRP, ADA, and DOGE, require multi-year segmentation before calling the strategy authentic.

Until one of those paths produces multi-window evidence, treat `QS3 + 5m only` as promising but unconfirmed.

## Evidence Files

- `tradingview/strategy/artifacts/v7_long_history_robustness/tv_long_history_robustness_runs.json`
- `tradingview/strategy/artifacts/v7_long_history_robustness/long_history_robustness_metrics.md`
- `tradingview/strategy/artifacts/v7_long_history_robustness/generate_long_history_robustness.mjs`
- `tradingview/strategy/artifacts/v7_long_history_robustness/analyze_long_history_robustness.mjs`

Local-only telemetry:

- `tradingview/strategy/.telemetry/outputs/v7_long_history_robustness/long_history_robustness_metrics.json`
