# V7 Perp Route Probe Verdict

## Scope

This is a targeted rerun of the prior unresolved HYPE, AERO, and RNDR/RENDER slots using Binance perpetual routes:

- `BINANCE:HYPEUSDT.P`
- `BINANCE:AEROUSDT.P`
- `BINANCE:RENDERUSDT.P`

The probe reused the v7 fixed-stop structural-control 125 bps profile and tested both 15m and 5m over TradingView's entire available history for each chart.

## Coverage Finding

The `.P` route resolved the suspicious no-result/export issue from the spot-route attempt.

| Expected slots | Exported slots | Missing | Failed | Rejected |
| --- | ---: | ---: | ---: | ---: |
| 6 | 6 | 0 | 0 | 0 |

All three symbols took trades on both timeframes. The available report ranges were:

| Asset | TF | Report range | Trades |
| --- | --- | --- | ---: |
| HYPE | 15m | Oct 31, 2025 to May 29, 2026 | 24 |
| HYPE | 5m | Mar 15, 2026 to May 29, 2026 | 22 |
| AERO | 15m | Oct 31, 2025 to May 29, 2026 | 24 |
| AERO | 5m | Mar 15, 2026 to May 29, 2026 | 19 |
| RENDER | 15m | Oct 31, 2025 to May 29, 2026 | 25 |
| RENDER | 5m | Mar 15, 2026 to May 29, 2026 | 17 |

## Strategy Result

The route fix did not turn these into admitted candidates under the current gates.

| Asset | Trades | P&L | PF | Win % | DD % | Classification | Primary issue |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| AERO | 43 | -98.04 | 0.948 | 53.5 | 6.51 | fail | Latest window degraded sharply and stop-first rate was high. |
| HYPE | 46 | 332.05 | 1.144 | 52.2 | 6.86 | fail | Positive total P&L, but 15m and early-window performance failed. |
| RENDER | 42 | -28.75 | 0.984 | 52.4 | 8.43 | fail | 15m worked, 5m failed, and early-window drawdown was too high. |

Combined result across the six slots:

| Trades | P&L | PF | Win % | DD % | TP1 first % | Stop first % |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 131 | 205.26 | 1.034 | 52.7 | 14.79 | 45.8 | 54.2 |

## Interpretation

The original "no trades" concern was a routing/data problem for the spot symbols, not a true strategy behavior. Binance `.P` charts produced complete exports and real trade samples.

The strategy verdict remains negative for these three as an expansion set. The issue is not trade discovery; it is quality and robustness:

- HYPE has useful signal on 5m, but 15m loses enough to keep the combined symbol below gate quality.
- AERO shows the clearest regime instability: the early window was strong, the latest window was poor, and the aggregate PF fell below 1.0.
- RENDER had a strong 15m profile and poor 5m profile, so timeframe selection is doing too much work.

The generic analyzer label of `insufficient data` is not the decision here. That label comes from running only this isolated three-symbol probe without the broader admitted-control set. The actionable result is that `.P` fixes coverage, while the current 125 bps v7 profile does not admit HYPE, AERO, or RENDER as robust candidates.

## Recommendation

Do not add HYPE, AERO, or RENDER to the admitted Unity UTM set based on this pass. Keep the prior admitted candidate set intact and treat these results as evidence that lower-liquidity/perp availability alone is not enough; any follow-up should test a single independent variable such as timeframe gating, volatility/risk floor adaptation, or symbol-specific admission filters rather than broadening the basket.
