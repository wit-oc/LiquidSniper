# V7 Stop Engine Robustness Verdict

## Scope

This pass tested stop-engine robustness only. Entry logic stayed fixed on the V7 System A Displacement Quality profile. The matrix covered BTCUSDT, ETHUSDT, and ZECUSDT on 15m and 5m across six stop variants.

Coverage was complete: 36 expected exports, 36 selected exports, 0 missing slots, 0 rejected candidates. The original baseline run hit a TradingView strategy panel UI failure on ZEC 15m, so the baseline was rerun and the complete rerun was used for aggregation.

## Basket Results

| Variant | Trades | P&L | PF | Win % | Max Row DD % | Positive Rows |
|---|---:|---:|---:|---:|---:|---:|
| Current stop baseline | 176 | 789.15 | 1.082 | 57.4 | 12.19 | 3/6 |
| 75bps floor | 155 | 914.34 | 1.111 | 56.8 | 10.75 | 3/6 |
| 100bps floor | 138 | 1798.94 | 1.300 | 59.4 | 4.91 | 4/6 |
| 125bps floor | 114 | 1803.79 | 1.428 | 57.9 | 4.52 | 4/6 |
| 100bps floor + 20bps buffer | 144 | -312.35 | 0.959 | 54.2 | 10.56 | 3/6 |
| 100bps floor + close-confirmed stop | 132 | 1461.23 | 1.220 | 61.4 | 8.52 | 4/6 |

## Findings

1. Stop-distance floors are real, but the edge starts near 100bps.

The 100bps and 125bps floors both cleared the credible bar, while 75bps remained weak. This argues against the 100bps result being a single exact-value accident, but it also says the boundary is not "any modest floor." The useful behavior is minimum distance large enough to avoid low-distance wick noise.

125bps had the best PF and drawdown, but it cut trade count to 114. The 100bps floor kept more trades while still holding PF 1.300 and DD 4.91%. The practical candidate remains the 100-125bps hard floor family, with 100bps as the more liquid/live-tradeable default and 125bps as a drawdown-first contender.

2. Simple sweep tolerance did not help.

The 20bps structural buffer failed outright: PF 0.959, negative P&L, and DD back above 10%. That rejects the idea that the issue is solved by simply widening the wick buffer.

Close-confirmed invalidation was useful diagnostically but not better than the hard 100bps stop. It produced PF 1.220 and higher win rate, but DD worsened to 8.52% and MAE expanded. This suggests some wick stop-outs are recoverable, but waiting for close confirmation adds enough adverse excursion to weaken the risk profile.

3. The candidate is not broad-market. ZEC carries the edge.

Grouped by symbol:

| Variant | BTC P&L / PF | ETH P&L / PF | ZEC P&L / PF |
|---|---:|---:|---:|
| Current baseline | -739.54 / 0.729 | -65.14 / 0.983 | 1593.83 / 1.533 |
| 100bps floor | -463.24 / 0.642 | 367.31 / 1.150 | 1894.87 / 1.846 |
| 125bps floor | -192.72 / 0.757 | -55.65 / 0.967 | 2052.16 / 2.175 |
| Wide buffer | -1179.50 / 0.429 | 279.62 / 1.107 | 587.53 / 1.194 |
| Close confirmed | -937.88 / 0.483 | 633.12 / 1.267 | 1765.99 / 1.720 |

BTC is consistently unprofitable across all stop engines. ETH is mixed and only clearly positive under 100bps hard stop or close-confirmed diagnostic. ZEC is the only symbol that is consistently strong and is responsible for most of the basket edge.

## UTM Implication

This does not invalidate the Unity Trading Model idea outright. It does expose a core flaw in the current System A implementation: alert + MSS + strength plus displacement is not enough to be a broad strategy. The model is highly regime and symbol sensitive, and without a liquidity/regime gate it will include BTC/low-edge environments that dilute or reverse the alt edge.

The stop behavior also says structural stops cannot be treated as raw wick invalidation on low timeframes. However, the successful fix was not arbitrary sweep tolerance; it was enforcing a minimum risk distance large enough to avoid tight-stop noise while keeping the entry/TP geometry intact.

## Verdict

Continue System A only as a regime-specialized candidate.

Do not broad-deploy alert + MSS + strength. Do not pivot away from System A yet, because the 100-125bps floor family is robust enough to justify one more implementation pass. The next implementation should lock the entry profile, use a hard minimum stop floor in the 100-125bps range, and add a symbol/regime gate before any further stop optimization.

Recommended build direction:

- Default to 100bps hard stop floor for trade count and continuity with the prior candidate.
- Keep 125bps as the drawdown-first profile to compare during implementation.
- Exclude BTC or require a separate BTC parameterization before inclusion.
- Treat ZEC as evidence of an alt/regime edge, but not proof of a durable multi-symbol strategy.
- Reject the 20bps wide-buffer stop.
- Treat close-confirmed stops as diagnostic telemetry, not the primary live execution model.

Next pass should test whether a simple regime gate can preserve ZEC/ETH behavior while excluding BTC-like low-edge contexts. If that fails, System A should stop and the build should pivot back to stricter UTM fidelity around POI/OB/FVG/retest.
