# Unity UTM V7 System A Foundation Verdict

Date: 2026-05-25

## Verdict

Keep the clean System A baseline as the Unity UTM V7 implementation foundation.

This does not make the strategy tradable as-is. The basket still fails the acceptance lens because Profit Factor is below 1.0 and total closed P&L is negative. The important result is that the clean implementation reproduces the prior verdict-harness System A profile closely enough to lock the implementation path: sweep/reclaim arming, 4H/1D EMA bias, AIO internal MSS, Oracle Strength, Sweep Wick stops, and AIO Buy/Sell Trend Alert as telemetry only.

Do not revive `alert + mss + strength` as a primary candidate unless later telemetry shows the alert has independent predictive value inside this clean System A baseline.

## Validation Run

Command:

```bash
node tradingview/scripts/tv_pine_text_matrix.mjs --cwd /Users/seanplatthy/Documents/Github/LiquidSniper --config tradingview/strategy/artifacts/v7_system_a_foundation/tv_system_a_foundation_runs.json --run v7-system-a-foundation
```

Coverage:

- 6/6 expected BTC/ETH/ZEC 15m/5m slots exported.
- 0 missing slots.
- 0 invalid full-close rows.
- 0 parent/report trade-count mismatches.
- Source mappings applied per symbol/timeframe.
- Strategy Tester date range set to Entire history.

## Basket Metrics

| System | Stop | Rows | Trades | Closed Net | PF | Win % | Max Row DD % | Positive Rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A Current | Sweep Wick | 6 | 264 | -3552.41 | 0.817 | 51.1 | 15.13 | 1 |

## Basket Telemetry

| Parents | TP1 First % | Stop First % | Avg MFE R | Avg MAE R | Avg Risk bps | Avg Alert Age | Avg Strength Slope | Long | Short |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 264 | 50.8 | 48.1 | 0.67 | -0.76 | 155.4 | 0.5 | 0.044 | 142 | 122 |

## Symbol/Timeframe Read

| Symbol | TF | Trades | P&L | PF | Win % | DD % |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 15m | 32 | -709.56 | 0.672 | 50.0 | 9.34 |
| BTCUSDT | 5m | 34 | -682.01 | 0.715 | 58.8 | 14.11 |
| ETHUSDT | 15m | 54 | -1065.84 | 0.700 | 46.3 | 13.52 |
| ETHUSDT | 5m | 41 | -868.49 | 0.706 | 48.8 | 13.57 |
| ZECUSDT | 15m | 47 | -1117.78 | 0.715 | 46.8 | 15.13 |
| ZECUSDT | 5m | 56 | 891.27 | 1.201 | 57.1 | 7.03 |

## Interpretation

The clean baseline is close to the prior verdict-harness System A Sweep Wick result: same max row drawdown, similar PF, similar win rate, similar risk bps, and the same basket conclusion. The small trade-count and P&L drift does not change the verdict.

The failure cluster is not alert absence. The basket loses because five of six symbol/timeframe rows remain negative, and average adverse excursion is larger than average favorable excursion. ZEC 5m is the only positive pocket; BTC and ETH do not validate the foundation by themselves.

The next implementation work should stay on System A and focus on failure reduction, especially:

- reducing stop-first rows without starving trade count;
- isolating BTC/ETH 15m and ETH 5m veto conditions;
- testing whether risk should be damped when average risk bps is large or Phase1 context is contradictory;
- keeping alert as an explanatory telemetry column rather than a gate.

## Evidence Files

- `tradingview/strategy/unity_utm_strategy_v7_system_a_foundation.pine`
- `tradingview/strategy/artifacts/v7_system_a_foundation/system_a_foundation_metrics.md`
- `tradingview/strategy/artifacts/v7_system_a_foundation/tv_system_a_foundation_runs.json`

Local-only telemetry:

- `tradingview/strategy/.telemetry/outputs/v7_system_a_foundation/system_a_foundation_metrics.json`
