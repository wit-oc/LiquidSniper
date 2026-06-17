# Unity UTM V7 Verdict

## Verdict

Continue with **System A: Current V7 AIO-MSS Edge/Bias** as the Unity UTM foundation.

Do **not** move forward with `alert + mss + strength` as the primary implementation path. The alert is worth keeping as telemetry and maybe a low-weight diagnostic, but the verdict data does not support making it the core gate.

Reject `Alert Required` as a foundation. It reduced frequency and did not improve basket edge. It had worse TP1-first behavior, worse stop-first behavior, and worse profit factor than System A.

Do not treat the strict `Retest POI` variant as the current foundation either. It reduced drawdown, but mainly by starving the strategy. It is a useful future fidelity test for a more paper-specific POI/retest implementation, not the best current UTM base.

## Redefined Systems

**System A: Current V7 path**

HTF liquidity sweep/reclaim arms the setup; 4H/1D EMA bias grants direction; LTF AIO internal MSS confirms structure; Oracle Strength confirms momentum; AIO BOS/Phase1 are quality/context; AIO Buy/Sell Trend Alert is not required.

**System B: Alert + MSS + Strength path**

Same as System A, but same-side AIO Buy/Sell Trend Alert after MSS is tested two ways: as score credit and as a hard required gate.

## Stoploss Derivation

The stop values were not arbitrary. In the verdict harness:

- `Sweep Wick`: stop anchor is the armed sweep invalidation level, then buffered by 4 bps.
- `MSS Swing`: stop anchor is `ta.lowest(low, mssStopLookbackEff)` for longs or `ta.highest(high, mssStopLookbackEff)` for shorts, then buffered by 4 bps.
- `Retest POI`: stop anchor is the retest candle low/high, then buffered by 4 bps, and the entry requires a retest.

Position size is then risk-based: equity times active risk percent divided by stop distance, capped by max notional leverage. So a bad stop anchor can hurt twice: it changes both invalidation distance and trade size.

## Execution Finding

The original huge failures were not a clean rejection of the stop idea. The verdict harness had a state bug: on same-bar exit/re-entry, the reset block could clear the newly assigned active stop/TP/max-hold state. That left the new trade unmanaged. The worst symptom was ZEC 5m showing huge open mark-to-market loss from a short that should have been stopped or max-held.

I fixed the reset guard and reran the contaminated rows. Final aggregation has:

- 54/54 expected slots selected
- 0 missing slots
- 0 invalid full-close rows
- 0 parent/report trade-count mismatches

## Basket Backtest Summary

| System | Stop | Trades | P&L | PF | Win % | Max Row DD % | Positive Rows |
|---|---|---:|---:|---:|---:|---:|---:|
| A Current | Sweep Wick | 267 | -3431.96 | 0.824 | 51.3 | 15.13 | 1 |
| A Current | MSS Swing | 258 | -4995.43 | 0.757 | 50.0 | 21.94 | 1 |
| A Current | Retest POI | 61 | -1166.39 | 0.659 | 52.5 | 12.33 | 3 |
| B Alert Score | Sweep Wick | 265 | -4127.30 | 0.812 | 50.9 | 16.67 | 1 |
| B Alert Score | MSS Swing | 258 | -5242.65 | 0.770 | 50.0 | 22.59 | 0 |
| B Alert Score | Retest POI | 61 | -1406.02 | 0.621 | 52.5 | 13.30 | 3 |
| B Alert Required | Sweep Wick | 103 | -3599.77 | 0.592 | 43.7 | 15.15 | 0 |
| B Alert Required | MSS Swing | 105 | -3635.50 | 0.613 | 44.8 | 24.94 | 1 |
| B Alert Required | Retest POI | 32 | -1223.60 | 0.523 | 37.5 | 11.82 | 2 |

## Basket Telemetry

| System | Stop | Parents | TP1 First % | Stop First % | Avg MFE R | Avg MAE R | Avg Risk bps |
|---|---|---:|---:|---:|---:|---:|---:|
| A Current | Sweep Wick | 267 | 50.9 | 47.9 | 0.67 | -0.75 | 155.4 |
| A Current | MSS Swing | 258 | 49.6 | 48.8 | 0.67 | -0.77 | 185.7 |
| A Current | Retest POI | 61 | 50.8 | 47.5 | 0.73 | -0.92 | 36.3 |
| B Alert Score | Sweep Wick | 265 | 50.6 | 48.3 | 0.68 | -0.76 | 155.4 |
| B Alert Score | MSS Swing | 258 | 49.6 | 48.8 | 0.67 | -0.77 | 185.7 |
| B Alert Score | Retest POI | 61 | 50.8 | 47.5 | 0.73 | -0.92 | 36.3 |
| B Alert Required | Sweep Wick | 103 | 43.7 | 56.3 | 0.64 | -0.80 | 157.6 |
| B Alert Required | MSS Swing | 105 | 44.8 | 55.2 | 0.63 | -0.78 | 187.1 |
| B Alert Required | Retest POI | 32 | 34.4 | 62.5 | 0.63 | -0.96 | 55.2 |

## Interpretation

System A Sweep Wick is the best broad foundation by basket PF, drawdown, frequency, and TP1-first behavior. It is still not tradable as-is because PF is below 1 and all basket P&L is negative.

Alert-as-Score did not add edge. It was close to System A but slightly worse on sweep and retest, and MSS Swing did not rescue it.

Alert-Required is worse. It cuts trade count from 267 to 103 on sweep, drops PF from 0.824 to 0.592, and flips telemetry from roughly balanced TP/stop behavior to stop-first dominance.

MSS Swing stops did not improve the foundation. They increased average risk bps and worsened drawdown versus Sweep Wick in both System A and Alert Score.

Retest POI is the only path that consistently reduced drawdown, but it did so with too little frequency and did not produce a better basket PF. It should be treated as a future paper-fidelity branch, not the current UTM foundation.

## Final Call

Lock the next implementation focus to **System A Current V7**, not `alert + mss + strength`.

The next productive work should be System A cleanup/fidelity, with alert retained as telemetry only. If we revisit retest/POI, it should be a separate stricter PDF-fidelity implementation, not a continuation of the alert-gated path.
