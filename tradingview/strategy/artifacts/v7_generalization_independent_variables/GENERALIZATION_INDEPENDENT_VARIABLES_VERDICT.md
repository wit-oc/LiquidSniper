# V7 Generalization Independent Variables Verdict

Generated: 2026-05-30

## Decision

The current Unity UTM v7 125 bps path is protected and remains viable only as a scoped admitted-symbol implementation. It is not yet a broad all-pairs/all-timeframes implementation.

Carry forward `Quality Score 3` as the only positive independent variable. Reject `ATR Regime Filter` and `Close Confirmed Stop` for this path. Do not combine the rejected variables into the next candidate.

The best next implementation candidate is:

- Baseline: protected v7 125 bps structural control.
- Add: `Quality Score 3` trade-quality filter.
- Keep excluded for now: ATR-regime profile and close-confirmed stop behavior.
- Scope: continue treating `ZEC`, `ADA`, `LINK`, `XRP`, `ARB`, `PYTH`, `SEI`, and now possibly `LTC` as the admitted-candidate set.
- Do not treat `BTC`, `SOL`, `BNB`, `DOGE`, `ETH`, `HYPE.P`, `AERO.P`, or `RENDER.P` as proven broad-deployable under this implementation.

## Protected Baseline

The pre-test candidate was snapshotted in `BASELINE_SNAPSHOT.md` before any variant testing.

| Item | Value |
| --- | --- |
| Protected source | `tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/generated/v7-fixed-stop-structural-control-125bps.pine` |
| Source SHA-256 | `f8e367119e684ec7f3f23460b54927b5e7b7f4a8b02c2cf7c6549484dc3755bb` |
| Branch | `codex/unity-utm-feasibility-spike` |
| HEAD | `f5a58c1045feb7d1600a00729097044daae98851` |

Matrix coverage was complete across all four runs: 16 symbols x 2 timeframes = 32 expected slots per run. No run had missing or failed slots. `Quality Score 3` had one accounted `no_trade_data` slot on BTC 15m.

## Independent Variable Results

| Variant | Trades | P&L | PF | Win % | DD % | Positive Rows | Negative Rows | PF<1 Rows | DD>5 Rows | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Baseline 125bps | 473 | 5106.00 | 1.289 | 56.0 | 14.14 | 21 | 11 | 11 | 6 | Protected control |
| Quality Score 3 | 439 | 5430.79 | 1.328 | 56.9 | 13.38 | 21 | 10 | 10 | 6 | Keep |
| ATR Regime Filter | 476 | 4690.21 | 1.264 | 55.9 | 14.44 | 21 | 11 | 11 | 7 | Reject |
| Close Confirmed Stop | 469 | 4109.55 | 1.213 | 58.6 | 24.52 | 20 | 12 | 12 | 7 | Reject |

Delta ranking versus baseline:

| Variant | Delta P&L | Delta PF | Delta DD % | Improved Slots | Degraded Slots | Improved Symbols | Degraded Symbols | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Quality Score 3 | 324.79 | 0.039 | -0.75 | 8 | 9 | 8 | 5 | 4.02 |
| ATR Regime Filter | -415.79 | -0.025 | 0.30 | 1 | 8 | 1 | 7 | -11.65 |
| Close Confirmed Stop | -996.45 | -0.076 | 10.38 | 4 | 22 | 3 | 9 | -27.95 |

## Scope Read

`Quality Score 3` is the only variable that improved the broad basket while preserving the admitted controls:

- All-symbol P&L improved from `5106.00` to `5430.79`.
- PF improved from `1.289` to `1.328`.
- DD improved from `14.14%` to `13.38%`.
- Prior admitted controls improved from `5952.46` P&L / `2.094` PF / `3.72%` DD to `6141.53` P&L / `2.183` PF / `3.70%` DD.
- Negative timeframe rows dropped from `11` to `10`.
- Negative windows dropped from `17` to `14`.
- `LTC` moved from marginal to pass.

That said, it is not a broad fix:

- Prior failed controls remained structurally bad: `-1302.99` P&L, `0.638` PF, `16.04%` DD.
- Failed-symbol group remained weak: `-966.41` P&L, `0.913` PF, `32.32%` DD.
- Perp route probes were effectively flat: `23.77` P&L, `1.004` PF, `14.79%` DD.
- HYPE, AERO, and RENDER did not become valid broad candidates.

## Rejected Variables

`ATR Regime Filter` should be rejected for this implementation pass. It reduced P&L, reduced PF, slightly worsened drawdown, increased DD>5 rows, and did not change the failed-symbol class set.

`Close Confirmed Stop` should be rejected more strongly. It increased win rate, but at the cost of materially worse drawdown and PF:

- All-symbol DD worsened from `14.14%` to `24.52%`.
- Prior failed controls worsened from `-1405.51` P&L / `0.668` PF / `17.87%` DD to `-1954.96` P&L / `0.610` PF / `24.57%` DD.
- Prior admitted controls lost protection, with DD rising from `3.72%` to `5.49%`.
- ADA and XRP were demoted from pass to marginal.

This suggests that delaying stop exits lets more trades recover, but it also lets failed setups become larger losers. For a drawdown-first model, that is not acceptable.

## Overfit And Generalization Risk

The baseline sanity check still flags overfit/generalization risk. The model is not simply profitable across the matrix. It is profitable in a specific admitted cluster and weak elsewhere.

The biggest issue is not only symbol selection; it is symbol/timeframe interaction:

- DOGE 15m is strongly negative while DOGE 5m is positive.
- HYPE 15m is negative while HYPE 5m is positive.
- AERO 15m is negative while AERO 5m is positive.
- RENDER flips the other way: 15m positive and 5m negative.
- BTC, SOL, BNB, and DOGE remain poor as a failed-control group.

That means the Unity UTM implementation is not yet robust enough to run uniformly across arbitrary coins and both timeframes. The stronger interpretation is: current v7 has a real signal for a subset of mid/liquidity-sensitive alts, but it has not found a uniform implementation shape.

## Recommendation

Adopt `Quality Score 3` as the next candidate refinement, but keep the strategy scoped. The next build should not attempt broad portfolio deployment yet.

Recommended next implementation boundary:

- Implement the quality-score threshold as the only carried-forward logic change.
- Preserve the protected 125 bps baseline as a fallback control.
- Keep admitted-symbol deployment separate from diagnostics on failed controls.
- Continue using broad-matrix telemetry as the acceptance gate.
- Do not add ATR regime or close-confirmed stop behavior unless a future independent test isolates a narrower condition where they help without raising drawdown.

The next question is not "does Unity UTM work everywhere?" The current answer is no. The better next question is: can `Quality Score 3` plus explicit admission rules produce a stable, low-drawdown Unity UTM v7 implementation without pretending the failed controls are tradable?
