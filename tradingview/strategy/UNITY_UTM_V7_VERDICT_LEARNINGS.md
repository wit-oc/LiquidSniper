# Unity UTM V7 Verdict Learnings

Date: 2026-05-24

## Verdict

Use the current V7 AIO-MSS edge/bias path as the Unity UTM foundation.

Do not promote `alert + mss + strength` to the primary implementation path. Keep the AIO Buy/Sell Trend Alert as telemetry, or at most a low-weight diagnostic, until it shows independent edge across the basket.

The current V7 path is not tradable as-is. It is simply the stronger foundation from this comparison because it preserved more frequency, better basket Profit Factor, and less stop-first behavior than the alert-required path.

## Compared Systems

System A, the current V7 path:

- HTF liquidity sweep/reclaim arms the setup.
- 4H/1D EMA bias grants direction.
- LTF AIO internal MSS confirms structure.
- Oracle Strength confirms momentum.
- AIO BOS/Phase1 remain quality/context signals.
- AIO Buy/Sell Trend Alert is observed but not required.

System B, the alert + MSS + strength path:

- Starts with the same System A ingredients.
- Adds same-side AIO Buy/Sell Trend Alert after MSS.
- Tests that alert both as score credit and as a hard required gate.

## Stoploss Derivation

The tested stops were derived from specific invalidation anchors, not arbitrary rejection rules:

| Stop mode | Anchor | Buffer |
|---|---|---:|
| Sweep Wick | Armed sweep invalidation level | 4 bps |
| MSS Swing | `ta.lowest(low, lookback)` for longs, `ta.highest(high, lookback)` for shorts | 4 bps |
| Retest POI | Retest candle low/high after required retest | 4 bps |

Position sizing was risk-based: equity times active risk percent divided by stop distance, capped by max notional leverage. That means a weak stop anchor affects both trade invalidation and trade size.

## Why The Early Failure Looked So Bad

The initial extreme failures were not a clean verdict against the stop concepts. The verdict harness had a same-bar exit/re-entry state bug: the reset block could clear the newly assigned active stop, take-profit, and max-hold state. That left a new trade unmanaged. The worst visible symptom was ZEC 5m carrying a large open mark-to-market loss from a short that should have been stopped or max-held.

After guarding that reset path and rerunning contaminated rows, the selected export set had:

- 54/54 expected slots selected.
- 0 missing slots.
- 0 invalid full-close rows.
- 0 parent/report trade-count mismatches.

## Basket Result

| System | Stop | Trades | P&L | PF | Win % | Max Row DD % |
|---|---|---:|---:|---:|---:|---:|
| A Current | Sweep Wick | 267 | -3431.96 | 0.824 | 51.3 | 15.13 |
| A Current | MSS Swing | 258 | -4995.43 | 0.757 | 50.0 | 21.94 |
| A Current | Retest POI | 61 | -1166.39 | 0.659 | 52.5 | 12.33 |
| B Alert Score | Sweep Wick | 265 | -4127.30 | 0.812 | 50.9 | 16.67 |
| B Alert Score | MSS Swing | 258 | -5242.65 | 0.770 | 50.0 | 22.59 |
| B Alert Score | Retest POI | 61 | -1406.02 | 0.621 | 52.5 | 13.30 |
| B Alert Required | Sweep Wick | 103 | -3599.77 | 0.592 | 43.7 | 15.15 |
| B Alert Required | MSS Swing | 105 | -3635.50 | 0.613 | 44.8 | 24.94 |
| B Alert Required | Retest POI | 32 | -1223.60 | 0.523 | 37.5 | 11.82 |

## Interpretation

System A Sweep Wick is the best broad foundation by basket Profit Factor, drawdown, frequency, and TP1-first behavior. MSS Swing increased average risk and drawdown versus Sweep Wick. Retest POI reduced drawdown, but mainly by starving the strategy, so it belongs in a separate paper-fidelity retest/POI branch rather than the current implementation path.

Alert-as-score did not add meaningful edge. Alert-required was worse: it cut Sweep Wick trade count from 267 to 103, dropped Profit Factor from 0.824 to 0.592, and shifted the basket toward stop-first outcomes.

## Commit Hygiene

The tracked evidence should be compact summaries and reusable harness tooling. Raw TradingView exports, generated Pine variants, and large JSON telemetry should remain local-only.

Local telemetry copy:

`tradingview/strategy/.telemetry/outputs/v7_verdict/verdict_harness_metrics.json`
