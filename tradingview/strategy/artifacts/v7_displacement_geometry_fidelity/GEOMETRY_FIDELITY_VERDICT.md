# V7 Displacement Geometry Fidelity Verdict

Date: 2026-05-27

## Verdict

Continue System A only as a **regime-specialized Displacement Quality + 100bps minimum stop-distance floor** candidate.

Do not promote broad Displacement Quality as the Unity Trading Model implementation yet. Do not spend more cycles on pure `alert + MSS + strength` or simple displacement-threshold tuning. The only variant that cleared the decision bar was the 100bps risk floor: PF 1.294, max row DD 4.91%, 134 trades, and 4/6 positive symbol-timeframe rows.

This is enough to avoid abandoning System A outright, but it is not enough to call it a broad implementation. BTC remained negative on both timeframes, and the basket is heavily carried by ZEC, especially ZEC 5m. The right next step is a lock-in pass around the 100bps floor with symbol/timeframe gating, not broad optimization.

## Evidence

All runs used TradingView full history for BTCUSDT, ETHUSDT, and ZECUSDT on 15m and 5m. The Strategy Tester UI metrics were unreliable, so metrics were derived from exported Strategy Tester CSVs.

Coverage: 48/48 expected slots selected, 0 missing, 0 rejected candidates, 0 invalid full-close rows, 0 parent/report mismatches.

| Variant | Trades | P&L | PF | Win % | Max Row DD % | Positive Rows | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| Displacement 1.50 Current | 187 | -103.56 | 0.990 | 56.1 | 12.19 | 3 | Fails |
| Exit TP1 1.5R | 160 | -51.93 | 0.995 | 44.4 | 12.43 | 3 | Fails |
| Risk Floor 100bps | 134 | 1752.76 | 1.294 | 58.2 | 4.91 | 4 | Passes, regime-specialized |
| Stop Floor 2ATR | 174 | 373.47 | 1.039 | 56.3 | 12.90 | 3 | Fails |
| Displacement 1.35 | 204 | -187.58 | 0.983 | 55.9 | 15.60 | 3 | Fails |
| Displacement 1.75 | 138 | 329.89 | 1.045 | 52.9 | 11.13 | 4 | Fails |
| Displacement 2.00 | 115 | 671.71 | 1.117 | 57.4 | 8.23 | 3 | Near, below bar |
| Retest Fidelity | 29 | -53.84 | 0.974 | 55.2 | 5.25 | 3 | Fails, too sparse |

Decision bar was PF > 1.15 with drawdown not worse than current Displacement Quality; strong bar was PF >= 1.25 with acceptable trade count and evidence beyond one symbol/timeframe. The 100bps floor is the only variant that passes the strong basket bar.

## What We Learned

Exit geometry was not the main fix. Moving TP1 from 1.0R to 1.5R improved average MFE capture but dropped win rate to 44.4%, increased stop-first outcomes, and kept PF below 1.0.

The damaging pocket is still low effective stop distance / low-risk trades. The baseline `risk<=100` bucket lost -1854.00. A simple 100bps minimum stop-distance floor removed that bucket and turned the basket into the only strong candidate.

Displacement threshold tuning alone is not enough. Raising Entry Range/ATR from 1.35 to 2.0 improved PF monotonically, but even the strictest 2.0 threshold only reached PF 1.117 and cut trade count to 115.

The first UTM retest/fidelity variant is not viable as implemented. It reduced the basket to 29 trades and still produced PF 0.974. A richer POI/OB/FVG retest model may still be worth testing later, but this simple Pine-accessible retest gate does not beat the risk-floor displacement candidate.

## Unity UTM Risk

The Unity Trading Model thesis is not disproven, but the broad Pine/vendor-signal implementation has clear flaws:

- Alert + MSS + strength does not create sufficient expectancy by itself.
- Confluence can preserve win rate while still leaving weak PF if stop geometry admits poor low-risk entries.
- A simple retest requirement can starve trade count without improving expectancy.
- The current edge is symbol/regime sensitive; ZEC carries the result while BTC remains structurally negative.

## Recommendation

Lock in one more tightly scoped implementation pass around **Displacement Quality + 100bps floor**:

- Treat BTC as excluded or gated until it proves positive under the same floor.
- Keep ETH and ZEC as the candidate validation set, with ZEC marked as the primary contributor.
- Retest only a small neighborhood around the floor, such as 75bps, 100bps, and 125bps.
- Keep threshold at 1.50 initially; only compare 1.75/2.0 if the floor result remains robust.
- Add telemetry for the removed low-risk bucket so we can prove the floor is removing bad trades rather than overfitting one symbol.

Final call: **continue regime-specialized System A**, not broad System A, and do not pivot fully to UTM fidelity yet. Pivot only if the risk-floor candidate fails the lock-in pass or cannot generalize beyond the current ZEC-led pocket.
