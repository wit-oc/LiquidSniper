# Phase 2 V7A Hybrid Rebalance Handoff (2026-03-08)

## Scope + outcome
This handoff covers Phase 2 watch-engine S/R context only (`WATCH/INVALID/EXPIRED` support path), with no trigger-entry logic added.

Primary implementation file:
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V7A_ZONE_FIRST.pine`

## What changed
1. Event budget governance (T1/T2)
- Replaced single shared event budget with split caps:
  - `maxStructEvents`
  - `maxBaseEvents`
  - `maxFoxianEvents`
  - plus hard ceiling `maxEventsTotal`.
- Added family-aware insertion gating in `f_can_add_event`.
- Set `structureEmitProtected=false` by default.
- Reduced protected-event weight so protected seeds are optional and secondary; primary structure seeds remain `STRUCT_BOS_ANCHOR` and `STRUCT_FLIP_ANCHOR`.

2. Base channel shelf detector rewrite (T3)
- Replaced compression proxy with shelf logic using:
  - overlap persistence
  - edge touch counts
  - breakout confirmation bars
- Added required diagnostics fields in code path:
  - `baseOverlapCount`
  - `baseTouchCountTop`
  - `baseTouchCountBot`
  - `baseCompressionScore`
  - `baseBreakoutScore`
- Emits both `BASE_SHELF` and `BASE_BREAKOUT` with diagnostics attached.

3. Foxian secondary evidence uplift (T4)
- Added Foxian quality dimensions:
  - launch quality
  - persistence proxy
  - break-beyond-range quality
- Mapped quality into zone-level scoring so Foxian can contribute even at low direct event count.

4. Merge governance + event-time ATR refs (T5)
- Stored `eAtrRef` per event.
- Merge tolerance now uses event-time ATR references.
- Added merge span controls:
  - `zoneMergeMaxSpanPct`
  - `zoneMergeMaxSpanATR`
  - `zoneMergeRequireOverlapSB` for structure/base overlap-required merges.

5. Retest + lifecycle implementation (T6)
- Added deterministic post-birth revisit counting into `zRetestCount`.
- Lifecycle driven by interactions:
  - `fresh`
  - `active`
  - `weakening`
  - `broken`
- Tradeable classing now includes lifecycle gating (fresh/active allowed).

6. Debug contract refresh (T7)
- Compact panel now includes:
  - events generated (family + subtype)
  - provisional zone stats (count + avg span + span rejects)
  - zone classes
  - tradeable reject reasons
  - retest telemetry summary
  - nearest visible zone
  - config digest

## Remaining gaps / risks
- Base shelf thresholds (`baseTouchTolATR`, `baseBreakConfirmBars`) are calibrated heuristically and may need symbol/timeframe tuning.
- Lifecycle break rule currently infers directional break from best bull/bear evidence; mixed-bias zones may still need a stricter break discriminator.
- Merge reject counters are deterministic but global per recalculation; on very large lookbacks they may require interpretation alongside event totals.

## Redact chart validation steps (exact)
1. Load `PHASE2A_SR_WATCHER_V7A_ZONE_FIRST.pine` on BTCUSD 1D, then ETHUSD 1D.
2. Keep defaults first pass (`mode=MAP`, `structureEmitProtected=false`).
3. Confirm event split caps in debug row `Events generated` do not show structure monopolizing total budget.
4. Confirm base channel emits non-zero `BASE_SHELF` and `BASE_BREAKOUT` on both symbols.
5. Confirm provisional row shows span reject telemetry (`rejects[pct/atr/ovl]`) changing when tightening merge span inputs.
6. Confirm lifecycle behavior by inspecting visible zones:
  - fresh -> active after revisits,
  - weakening with higher revisit counts,
  - broken when directional break condition is met.
7. Confirm tradeable rejects include `state=` reason when lifecycle disqualifies a zone.
8. Capture before/after screenshots of debug panel for default settings and one tightened-merge profile.

## Evidence list
Files changed:
- `IntradayTrading/pine/PHASE2A_SR_WATCHER_V7A_ZONE_FIRST.pine`
- `IntradayTrading/spec/phases/PHASE2_V7A_HYBRID_REBALANCE_HANDOFF_2026-03-08.md`

Commit hashes:
- `7f0cc47` — T1/T2 event caps split + structure noise posture
- `b5df998` — T3/T4 base shelf rewrite + Foxian quality scoring
- `235ae6c` — T5/T6 ATR merge governance + lifecycle/retest
- `0a15c23` — T7 debug contract refresh

Before/after debug deltas:
- Before: family totals only, no subtype split, no merge span reject counters, no lifecycle telemetry summary.
- After: subtype counts per family, provisional span reject counters (`pct/atr/ovl`), retest telemetry (`avg/max/broken`), and state-based tradeable reject visibility.
