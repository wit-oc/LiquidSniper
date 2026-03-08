# Phase 2 V7A Geometry/Core/Lifecycle Handoff (2026-03-08)

Status: READY FOR OPERATOR CERT (`#phase-2-watch-engine-certification`)
Scope lock: WATCH/INVALID/EXPIRED support context only (no trigger-entry logic)

## What changed
- Added dual-geometry zone model:
  - Structural envelope: `zStructTop`, `zStructBot`, `zStructMid`
  - Tradeable core: `zCoreTop`, `zCoreBot`, `zCoreMid`, `zCoreWidthPct`, `zCoreScore`
- Tradeable width classing now uses core width (`zCoreWidthPct`) instead of envelope width.
- Rendering now draws envelope (lighter) and core (stronger) separately, midline anchored to core.
- Replaced first-come event caps with family-local ranking and dedupe before cap:
  - family dedupe on price proximity + time proximity + directional equivalence
  - keep best-N per family, then merge under total cap
- Added merge segmentation hardening:
  - regime boundary protection (`zRegimeId`/`eRegimeId`)
  - max event-time distance guard (`maxBarsBetweenEvents`)
  - retained overlap + span controls
- Added lifecycle/first-retest semantics:
  - fields: `hasFirstRetestOccurred`, `firstRetestReactionATR`, `firstRetestFailed`, `timesCleanlyRejected`, `timesClosedThrough`
  - state semantics: `virgin`, `first_touch_ready`, `tested_once`, `spent`, `broken`
  - tradeable gating includes lifecycle quality and first-retest outcome quality
- Base shelf refinement:
  - shelf dedupe by price/time
  - shelf adjacency merge for contiguous shelves
  - stronger edge-touch weighting and breakout-conviction contribution
- Debug contract expanded for cert visibility:
  - family saturation pre/post dedupe
  - envelope vs core telemetry
  - lifecycle distribution
  - first-retest outcome telemetry
  - merge reject reasons (segmentation/span/overlap)

## Known risks
- Core derivation uses strongest-inner evidence heuristic; on very sparse evidence it falls back to a deterministic narrowed envelope.
- Regime protection can reduce merge aggressiveness in chop; may slightly increase structural zone count.
- First-retest outcome quality depends on 1D bar-close behavior and can be conservative on volatile wicks.

## Recommended defaults
- `lookbackBars=1200`
- `maxStructEvents=160`, `maxBaseEvents=120`, `maxFoxianEvents=80`, `maxEventsTotal=360`
- `maxBarsBetweenEvents=220`
- `mergeTolPct=0.004`, `mergeTolATR=0.60`
- `zoneMergeMaxSpanPct=0.090`, `zoneMergeMaxSpanATR=5.00`
- `minStructuralScore=50`, `minTradeableScore=65`
- `maxTradeableWidthPct=0.06`, `maxTradeableRetests=3`

## BTC/ETH 1D operator runbook (exact)
1. Open TradingView on `BTCUSD` and add script `PHASE2A_SR_WATCHER_V7A_ZONE_FIRST`.
2. Set timeframe to `1D`, mode `MAP`, and apply Recommended defaults above.
3. Record debug table rows at current bar and after scrolling ~300 bars left then returning to current bar.
4. Repeat steps 1-3 on `ETHUSD` `1D` with identical settings.
5. Cert checks (must pass on both symbols):
   - Family saturation row shows `raw/dedupe/selected` with dedupe and selected counts not hard-pegged at family caps in normal windows.
   - Envelope/Core row shows `avgCore < avgStruct` and visible core boxes materially narrower than envelopes.
   - Lifecycle distribution row shows non-zero occupancy across at least `first_touch_ready` and one of `tested_once/spent/broken`.
   - First retest row reports deterministic counts (`seen`, `fail`, `avgATR`) with no blank/NA behavior.
   - Merge rejects row reports segmented reasons (`seg/bars/span/ovl`) and no single reason dominates abnormally (>90% of rejects) on both symbols.
   - Visual check: duplicate adjacent shelf clutter reduced vs prior V7A snapshot.

## Before/after metric deltas (cert expectations)
- Event selection behavior:
  - Before: first-come family saturation often hard-pegged.
  - After: `raw > dedupe >= selected` visible per family; fewer cap-pegged families.
- Geometry:
  - Before: one-zone-width model (envelope width used for tradeable gate).
  - After: core width drives tradeable gate; expected `avgCore/avgStruct` ratio < 1.0.
- Lifecycle:
  - Before: coarse fresh/active/weakening/broken proxy.
  - After: behavior-driven first-retest outcomes and explicit lifecycle state set.
- Merge stability:
  - Before: stale-cycle merge risk.
  - After: regime + bar-distance segmentation rejects stale-cycle merges.

## Follow-up tasks (V7B only, after cert pass)
- Add 4H companion map alignment and cross-timeframe zone handshake diagnostics.
- Tune core-derivation weighting per family (structure/base/foxian) with calibrated coefficients.
- Add optional per-family dedupe tolerance inputs for operator tuning in MAP mode.
