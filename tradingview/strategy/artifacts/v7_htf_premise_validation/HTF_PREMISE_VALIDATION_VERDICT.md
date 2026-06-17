# Unity UTM V7 HTF Premise Validation Verdict

Date: 2026-05-31

## Verdict

Do not promote the current `QS3 + 4H` Unity UTM V7 profile as the implementation path.

The 4H TradingView validation has enough historical coverage to be meaningful, but the strategy did not show a broad, durable edge. Across 17 symbols, TradingView returned 17/17 successful exports, 0 missing slots, and 0 failed slots. Coverage met the one-year gate on every symbol, including multi-year coverage on the long-running majors.

The weakness is not data depth. The weakness is that the raw 4H port barely trades and the trades it does take do not persist across symbols or regimes:

- 0 pass assets.
- 0 fail assets by evidence-count threshold, because no symbol reached 10 trades.
- 5 thin assets: `ADA:thin-negative`, `XRP:thin-positive`, `BTC:thin-negative`, `BNB:thin-positive`, `DOGE:thin-positive`.
- 12 inconclusive assets, including valid no-trade exports for `PYTH`, `HYPE.P`, `AERO.P`, and `VIRTUAL.P`.
- All-symbol basket: 56 trades, 239.88 P&L, 1.092 PF, 53.6% win rate, 7.20% max drawdown.

That is not enough to confirm the HTF premise. It is also not a strong enough rejection of the Unity Trading Model as a paper concept. The right conclusion is narrower: this current alert + MSS + strength / QS3 implementation shape is too sparse and too inconsistent as a standalone 4H entry model.

## TradingView-Only Constraint

Validation must remain in TradingView because the strategy depends on proprietary/input.source metrics from the TradingView chart stack:

- The Oracle AIO internal MSS/BOS and trend-alert outputs.
- The Oracle Strength.
- HTF Phase 1 Structure direction outputs.

No recommendation in this artifact assumes any non-TradingView validator can replace those metrics.

## Validation Run

Command:

```bash
node tradingview/scripts/tv_pine_text_matrix.mjs --cwd /Users/seanplatthy/Documents/Github/LiquidSniper --config tradingview/strategy/artifacts/v7_htf_premise_validation/tv_htf_premise_validation_runs.json --run v7-htf-premise-qs3-4h --settings-committed --strategy-report-date-range "Entire history"
```

Harness:

- Source lineage: current V7 generalization QS3 candidate.
- Test profile: `Displacement Quality`.
- Minimum quality score: `3`.
- Timeframe: `4H`.
- Pine backtest window: disabled.
- Strategy Tester date range: `Entire history` / `All`.
- Source mappings: applied per symbol.
- Threshold tuning: none.

## Coverage Gate

| TF | Required minimum | Rows meeting minimum | Rows capped | Result |
|---|---:|---:|---:|---|
| 4H | 365 days | 17/17 | 0/17 | pass |

The 4H run solved the historical-depth problem that blocked the 5m robustness verdict. BTC and ETH covered `Aug 17, 2017 — May 31, 2026`; BNB covered `Nov 5, 2017 — May 31, 2026`; ADA covered `Apr 17, 2018 — May 31, 2026`.

## Basket Metrics

| Scope | Trades | P&L | PF | Win % | DD % |
|---|---:|---:|---:|---:|---:|
| All 17 symbols | 56 | 239.88 | 1.092 | 53.6 | 7.20 |
| Prior admitted controls | 20 | -115.84 | 0.879 | 50.0 | 3.87 |
| Prior failed controls | 22 | 143.00 | 1.126 | 54.5 | 5.06 |
| Major controls | 13 | 115.88 | 1.224 | 53.8 | 2.56 |
| Perp route probes | 1 | 96.84 | n/a | 100.0 | 0.00 |
| Failed+perp controls | 23 | 239.84 | 1.211 | 56.5 | 5.02 |

## Symbol-Level Interpretation

| Asset | Range | Trades | Result |
|---|---|---:|---|
| ZEC | Mar 21, 2019 to May 31, 2026 | 1 | inconclusive, negative |
| ADA | Apr 17, 2018 to May 31, 2026 | 3 | thin-negative |
| LINK | Jan 16, 2019 to May 31, 2026 | 5 | inconclusive, positive |
| XRP | May 4, 2018 to May 31, 2026 | 5 | thin-positive |
| ARB | Mar 23, 2023 to May 31, 2026 | 5 | inconclusive, positive |
| PYTH | Feb 2, 2024 to May 31, 2026 | 0 | valid no-trade export |
| SEI | Aug 15, 2023 to May 31, 2026 | 1 | inconclusive, negative |
| BTC | Aug 17, 2017 to May 31, 2026 | 9 | thin-negative |
| ETH | Aug 17, 2017 to May 31, 2026 | 7 | inconclusive, positive |
| SOL | Aug 11, 2020 to May 31, 2026 | 2 | inconclusive, negative |
| BNB | Nov 5, 2017 to May 31, 2026 | 8 | thin-positive |
| DOGE | Jul 5, 2019 to May 31, 2026 | 3 | thin-positive |
| LTC | Dec 12, 2017 to May 31, 2026 | 6 | inconclusive, positive |
| HYPE.P | May 30, 2025 to May 31, 2026 | 0 | valid no-trade export |
| AERO.P | Dec 4, 2024 to May 31, 2026 | 0 | valid no-trade export |
| VIRTUAL.P | Dec 10, 2024 to May 31, 2026 | 0 | valid no-trade export |
| RENDER.P | Feb 2, 2023 to May 31, 2026 | 1 | inconclusive, positive |

## Comparison To 5m QS3

The 5m QS3 profile remains directionally stronger but historically shallow:

| Profile | Coverage | Trades | P&L | PF | Win % | DD % | Verdict |
|---|---|---:|---:|---:|---:|---:|---|
| `QS3 + 5m` | Mar 15, 2026 to May 30, 2026 | 196 | 5145.61 | 1.633 | 59.7 | 8.24 | promising, unconfirmed |
| `QS3 + 4H` | full available 4H history | 56 | 239.88 | 1.092 | 53.6 | 7.20 | rejected as standalone HTF path |

If forced to choose which branch has better implementation possibility, the current evidence favors the 5m QS3 execution profile over the raw 4H QS3 entry profile. That is not a final trading-strategy acceptance, because the 5m historical window is still only about 78 days.

## Recommendation

Do not keep optimizing the raw `QS3 + 4H` entry profile.

Keep the current `QS3 + 5m` profile archived as the leading short-window candidate, but do not lock it for implementation until TradingView can provide deeper history for the same proprietary/input.source signal stack.

The next valid work should stay tightly scoped:

1. Attempt TradingView Deep Backtesting or another TradingView-sourced export path for the `QS3 + 5m` candidate.
2. If deeper 5m history remains inaccessible, test whether HTF can act only as a directional context layer for 5m execution, not as the entry timeframe.
3. Do not add new free-form filters until the historical-depth problem is resolved; otherwise we will be tuning against a short recent window.

## Evidence Files

- `tradingview/strategy/artifacts/v7_htf_premise_validation/tv_htf_premise_validation_runs.json`
- `tradingview/strategy/artifacts/v7_htf_premise_validation/htf_premise_validation_metrics.md`
- `tradingview/strategy/artifacts/v7_htf_premise_validation/generate_htf_premise_validation.mjs`
- `tradingview/strategy/artifacts/v7_long_history_robustness/analyze_long_history_robustness.mjs`

Local-only telemetry:

- `tradingview/strategy/.telemetry/outputs/v7_htf_premise_validation/htf_premise_validation_metrics.json`
