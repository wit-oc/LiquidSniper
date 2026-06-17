# Unity UTM V7 System A Profitability Risk Verdict

Date: 2026-05-26

## Verdict

Do not deploy broad System A as-is. The current path is not dead, but the next implementation should be a risk-controlled, regime-specialized System A focused on displacement/range quality rather than more generic confluence.

The tested constraints did not turn the full BTC/ETH/ZEC 15m/5m basket profitable in a broad, defensible way. The strongest evidence says:

1. Risk bps alone is not the root profitability problem.
2. Directional Strength slope helps, but not enough to make the basket viable.
3. Entry range/displacement and ATR regime are the clearest profitability split.

The Unity Trading Model concept is not disproven, but this mechanical translation is incomplete. Sweep + MSS + Strength still admits too many low-energy or wrong-regime entries. A UTM implementation likely needs explicit displacement/regime context, not just another hard confluence gate.

## Validation Coverage

Source metrics: `profitability_risk_metrics.md`

Coverage was complete:

| Expected slots | Selected slots | Missing | Rejected candidates | Invalid full-close rows | Parent/report mismatches |
|---:|---:|---:|---:|---:|---:|
| 30 | 30 | 0 | 0 | 0 | 0 |

Validated profiles:

| Profile | Purpose |
|---|---|
| A Baseline | Clean System A with risk/ATR/range telemetry |
| Risk Veto 175bps | Reject entries above 175 bps stop distance |
| Risk Damp 150bps | Halve risk above 150 bps stop distance |
| Directional Strength Slope | Require Strength slope in trade direction |
| BOS/Phase Agreement | Require same-side AIO BOS or Phase1 CHoCH/BOS |

Basket: BTCUSDT, ETHUSDT, ZECUSDT on 15m and 5m, full TradingView history.

## Basket Results

| System | Trades | P&L | PF | Win % | Max row DD % | Positive rows | NED rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| A Baseline | 268 | -3213.58 | 0.836 | 51.5 | 15.13 | 1 | 0 |
| Risk Veto 175bps | 209 | -2618.32 | 0.828 | 53.1 | 14.11 | 0 | 0 |
| Risk Damp 150bps | 269 | -3010.49 | 0.810 | 51.3 | 14.11 | 1 | 0 |
| Directional Strength Slope | 261 | -2257.85 | 0.880 | 52.1 | 13.57 | 1 | 0 |
| BOS/Phase Agreement | 24 | 14.40 | 1.006 | 54.2 | 12.66 | 2 | 3 |

Risk Damp produced the best practical drawdown control without starving trade count, but it did not improve PF. Directional Strength Slope was the best broad quality improvement, but the basket still lost money. BOS/Phase Agreement was technically profitable, but only with 24 trades and 3 no-edge-detected rows, so it is not a broad implementation candidate.

## Risk Area Findings

### 1. Risk / Stop Geometry

High risk bps was not the core failure.

Baseline risk buckets:

| Risk bucket | Trades | P&L | TP1 first % | Stop first % | Avg risk bps |
|---|---:|---:|---:|---:|---:|
| risk<=100 | 94 | -2235.50 | 51.1 | 47.9 | 63.6 |
| risk100-175 | 97 | -937.04 | 51.5 | 47.4 | 133.0 |
| risk>175 | 77 | -41.04 | 50.6 | 48.1 | 292.4 |

This falsifies the simple assumption that large stop distance is what broke the strategy. The lowest-risk bucket was the worst bucket by P&L.

Risk controls are still useful as damage controls:

| Variant | Result |
|---|---|
| Risk Veto 175bps | Lowered max row DD from 15.13% to 14.11%, but cut trades from 268 to 209 and produced no positive rows |
| Risk Damp 150bps | Lowered max row DD from 15.13% to 14.11% and preserved count, but PF fell from 0.836 to 0.810 |

Recommendation: keep risk damp/cap as a risk overlay, not as the edge source.

### 2. Entry Quality

Directional Strength Slope is the best broad quality filter tested, but not enough alone.

Compared with baseline:

| System | Trades | P&L | PF | Max row DD % |
|---|---:|---:|---:|---:|
| A Baseline | 268 | -3213.58 | 0.836 | 15.13 |
| Directional Strength Slope | 261 | -2257.85 | 0.880 | 13.57 |

The filter improved P&L, PF, and drawdown while preserving trade count. It still left BTC and ETH rows negative and only had one positive symbol/timeframe row. Treat it as a useful component, not a final gate.

BOS/Phase Agreement found a possible 5m pocket:

| Symbol/TF | Trades | P&L | PF | DD % |
|---|---:|---:|---:|---:|
| ETH 5m | 7 | 821.97 | 4.823 | 3.05 |
| ZEC 5m | 5 | 822.04 | 4.417 | 3.11 |

But the full BOS/Phase basket only had 24 trades, and all 15m rows had one trade each. This is too sparse for a broad verdict. It can be isolated as a 5m micro-regime candidate only.

### 3. Regime Concentration

ATR and entry-range/displacement buckets are the clearest failure split.

Baseline ATR buckets:

| ATR bucket | Trades | P&L | TP1 first % | Stop first % | Avg MAE R |
|---|---:|---:|---:|---:|---:|
| atr<=75 | 224 | -1575.91 | 54.0 | 45.1 | -0.74 |
| atr75-150 | 33 | -643.68 | 36.4 | 63.6 | -0.79 |
| atr>150 | 11 | -993.99 | 36.4 | 54.5 | -1.02 |

Medium/high ATR regimes are structurally damaging. They have weaker TP1-first rates and materially worse stop-first behavior.

Baseline entry-range buckets:

| Entry range bucket | Trades | P&L | TP1 first % | Stop first % |
|---|---:|---:|---:|---:|
| range<=40 | 74 | -1849.02 | 51.4 | 48.6 |
| range40-90 | 102 | -1908.56 | 50.0 | 49.0 |
| range>90 | 92 | 544.00 | 52.2 | 45.7 |

The larger entry-range/displacement bucket was the only profitable baseline regime. Directional Strength Slope improved that same bucket to +1049.08 across 94 trades.

This is the strongest next implementation signal: System A needs an explicit displacement/range quality gate, ideally normalized by ATR so the threshold does not become symbol-specific overfit.

## Symbol / Timeframe Concentration

Baseline only had one positive row:

| Symbol/TF | Trades | P&L | PF | DD % |
|---|---:|---:|---:|---:|
| ZEC 5m | 59 | 1148.98 | 1.251 | 6.01 |

Directional Strength preserved the ZEC 5m edge and materially improved ZEC 15m:

| Symbol/TF | Trades | P&L | PF | DD % |
|---|---:|---:|---:|---:|
| ZEC 15m | 44 | -222.76 | 0.932 | 9.84 |
| ZEC 5m | 59 | 1149.98 | 1.246 | 6.54 |

BTC and ETH broad rows remained negative. Do not treat the current basket as a uniform strategy. The evidence supports regime-gating first, then symbol/timeframe inclusion decisions.

## UTM Model Risk

The UTM concept may depend on discretionary qualities that the current System A does not encode:

| Possible missing quality | Evidence |
|---|---|
| Displacement after sweep/MSS | `range>90` was profitable while smaller ranges lost heavily |
| Volatility regime selection | ATR 75-150 and ATR >150 had poor stop-first behavior |
| Context beyond generic confluence | BOS/Phase was high PF only in sparse 5m pockets and starved broad coverage |
| POI/retest/order-block fidelity | Current System A is a reduced mechanical version, so failure here does not fully invalidate UTM |

The core flaw is not obviously "alert + MSS + Strength can never work." The more precise flaw is that alert + MSS + Strength without displacement/regime quality is too permissive.

## Final Recommendation

Continue the System A path only as a regime-specialized implementation:

1. Keep Risk Damp 150bps or a similar cap as a drawdown overlay.
2. Add a displacement/range quality test as the next primary gate, preferably ATR-normalized.
3. Keep Directional Strength Slope as the quality filter most worth carrying forward.
4. Treat BOS/Phase Agreement as a separate 5m micro-regime candidate, not as the broad System A gate.
5. Pause any broad-production implementation until the displacement/regime version is tested.

Concrete next verdict target: test `System A + Directional Strength Slope + ATR-normalized displacement gate + risk damp overlay` against the current baseline and the Directional Strength-only profile. If that does not materially improve drawdown and PF without starving count, stop this branch and revisit UTM spec fidelity before adding more confluence.
