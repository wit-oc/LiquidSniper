# V7 System A Displacement Candidate Verdict

Date: 2026-05-27

## Verdict

Continue with **System A + Directional Strength Slope + ATR-normalized Displacement Quality** as the V7 implementation candidate. Stop treating **alert + MSS + strength alone** as the primary Unity Trading Model path.

Do **not** carry forward the ATR regime damp/veto as tested here. It reduced the displacement candidate from positive to negative and increased max row drawdown.

This is not yet a production-quality strategy. It is the best tested implementation direction because it is the only run in this batch that moved the full BTC/ETH/ZEC 15m/5m basket positive while reducing trade count and improving the TP-first/stop-first mix.

## Evidence

All runs used full TradingView history for BTCUSDT, ETHUSDT, and ZECUSDT on 15m and 5m. Coverage was 30/30 expected exports with 0 missing, 0 rejected, 0 invalid full-close rows, and 0 parent/report mismatches.

| System | Trades | P&L | PF | Win % | Max Row DD % | TP1 First % | Stop First % |
|---|---:|---:|---:|---:|---:|---:|---:|
| A Baseline | 271 | -3771.16 | 0.813 | 50.9 | 14.11 | 50.6 | 48.3 |
| Risk Damp 150bps | 271 | -3326.00 | 0.795 | 50.9 | 14.11 | 50.6 | 48.3 |
| Directional Strength Slope | 263 | -2720.19 | 0.859 | 51.7 | 13.57 | 51.3 | 47.9 |
| Displacement Quality | 181 | 311.91 | 1.031 | 55.8 | 12.19 | 55.2 | 44.2 |
| Displacement ATR Regime | 185 | -367.02 | 0.964 | 55.7 | 15.14 | 55.7 | 44.3 |

## What Likely Caused The Prior Path To Fail

Alert + MSS + strength was not rejected out of hand. The test shows it helped only slightly: Directional Strength Slope improved baseline P&L by about 1051 and reduced drawdown a bit, but still remained materially negative.

The bigger issue was trade quality. Low-displacement entries were damaging:

| Entry Range / ATR | Baseline P&L | Directional Strength P&L |
|---|---:|---:|
| <= 1.25 ATR | -2693.65 | -2778.36 |
| 1.25-1.50 ATR | -1275.78 | -1329.84 |
| > 1.50 ATR | 198.27 | 1388.01 |

The profitable pocket was not "more confluence"; it was sufficient displacement. The displacement candidate mostly forced entries into the >1.5 ATR bucket and removed 90 low-quality baseline trades.

## Risk Notes

The candidate is still fragile:

- PF is only 1.031 on the basket, so this is a marginal edge, not a locked strategy.
- BTC remained negative on both 15m and 5m.
- ETH 5m remained negative and worsened under ATR-regime gating.
- The strongest positive contribution came from ZEC and ETH 15m, so symbol/timeframe sensitivity is still high.
- Risk Damp alone did not create edge. It should remain a sizing/risk overlay only, not a signal thesis.

## Implementation Recommendation

Promote **Displacement Quality** as the next V7 candidate:

- Keep System A foundation.
- Keep directional strength slope as a quality component.
- Keep ATR-normalized entry displacement/range quality as the main filter.
- Keep risk damp available as a risk overlay, but do not evaluate it as edge by itself.
- Drop ATR regime veto/damp from the next default candidate.
- Keep BOS/Phase as telemetry until a separate sparse-pocket test proves value.

Next validation should tune only the displacement/risk boundary, not restart broad optimization: compare displacement thresholds around 1.35, 1.50, and 1.75 ATR, plus a risk floor that avoids the `risk<=100` bucket unless it has an independent reason to survive.

## Data Note

TradingView's Strategy Tester UI changed during this run. The visible metrics table was not consistently reachable, so the tracked metrics were derived from exported Strategy Tester list-of-trades CSVs. The aggregator now accepts TradingView's current `Net PnL USDT` column and keeps raw JSON/automation outputs under ignored telemetry paths.
