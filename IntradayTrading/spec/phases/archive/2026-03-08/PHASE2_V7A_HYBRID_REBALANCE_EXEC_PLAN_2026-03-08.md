# Phase 2 — V7A Hybrid Rebalance Execution Plan (2026-03-08)

Status: DRAFT FOR REVIEW  
Branch: `phase2-v7-zone-first-20260307`  
Primary file: `IntradayTrading/pine/PHASE2A_SR_WATCHER_V7A_ZONE_FIRST.pine`

---

## 1) Scope lock (Phase 2 guardrail)

This plan is for **WATCH support S/R context only**:
- Build/certify POI + Fib context quality for watch-state transitions.
- No trigger-entry logic (15m/5m stays out of scope).
- No execution/risk lifecycle changes.

---

## 2) Why this rebalance is needed now

Current V7A scaffold proved the architecture direction (zone-first), but debug evidence shows hybrid channels are not balanced yet:

- `events=320 zones=17`
- `struct=320 base=0 foxian=0`
- `struct=6 tradeable=0`
- `score=6 width=5 retest=0`

Interpretation:
- Structure channel saturates a single shared event budget.
- Base/Foxian channels are functionally inactive.
- Tradeable classification cannot mature while width governance + retest semantics are placeholders.

---

## 3) Objectives (this execution cycle)

1. Activate true hybrid evidence flow (structure + base + foxian all contribute).  
2. Reduce structural flood/noise while preserving v3.3 intent anchors.  
3. Promote base/shelf geometry into a real source of zones.  
4. Move Foxian from candle-creator toward zone-quality evidence.  
5. Add merge-width governance early (at zone build), not only at final classify.  
6. Make retest/lifecycle semantics real so tradeable classification is meaningful.

---

## 4) Implementation tracks (sequenced)

## Track A — Event pipeline rebalance (V7A.1)

### Changes
- Replace shared `maxEvents` with family budgets:
  - `maxStructEvents`
  - `maxBaseEvents`
  - `maxFoxianEvents`
- Keep aggregate cap optional (`maxEventsTotal`) only as a hard safety cap.
- Add per-family counters in debug digest.

### Acceptance gate
- On BTC/ETH 1D, debug must show all family counts > 0 on normal windows.
- Must never show `struct=all, base=0, foxian=0` under default settings.

---

## Track B — Structure adapter noise control (V7A.2)

### Changes
- Default `structureEmitProtected = false`.
- Seed zones primarily from:
  - `STRUCT_BOS_ANCHOR`
  - `STRUCT_FLIP_ANCHOR`
- If protected levels remain enabled, treat as low-weight context, not first-class seed priority.

### Acceptance gate
- Structure tape still aligns with v3.3 directional backbone.
- Event volume drops materially vs current scaffold while key shelves remain seeded.

---

## Track C — Real base/shelf detector (V7A.3)

### Changes
Replace compression proxy with shelf detector requiring a combination of:
- span compression (`spanATR <= baseMaxATRSpan`)
- overlap persistence (consecutive overlap count)
- edge touches (top/bottom tolerance counts)
- breakout confirmation (`baseBreakMinATR`)

Add diagnostic features:
- `baseOverlapCount`
- `baseTouchCountTop`
- `baseTouchCountBot`
- `baseCompressionScore`
- `baseBreakoutScore`

Emit:
- `BASE_SHELF`
- `BASE_BREAKOUT`

### Acceptance gate
- Known shelf regions appear from base channel without dependence on elite single candles.

---

## Track D — Foxian as zone evidence (V7A.4)

### Changes
- Keep optional Foxian event emission, but cap separately.
- Add zone-level Foxian scoring pass after provisional zones:
  - launch quality
  - persistence
  - break-beyond-range quality
- Prefer scoring existing zones over creating new geometry from impulse candles.

### Acceptance gate
- Removing a single high-rank candle does not erase obvious shelf significance.

---

## Track E — Merge governance + event-time references (V7A.5)

### Changes
- Store per-event ATR reference (`eAtrRef`) at event creation.
- Use event-time ATR in merge tolerance decisions (not only current ATR).
- Add merge-time span controls:
  - `zoneMergeMaxSpanPct`
  - `zoneMergeMaxSpanATR`
  - optional overlap-required merge for structure/base channels

### Acceptance gate
- No repeated “survives pre/post but dies FAIL_WIDTH forever” loop in 72k–75k-like shelves.

---

## Track F — Real retest/lifecycle semantics (V7A.6)

### Changes
- Compute `zRetestCount` from post-birth zone interactions.
- Separate structural existence from tradeability freshness.
- State transitions from actual interactions:
  - `fresh -> active -> weakening -> broken`

### Acceptance gate
- Tradeable count is driven by interaction behavior, not placeholder static defaults.

---

## 5) Debug/telemetry contract updates

Required table rows (compact mode):
1. `Events generated` (family + subtype counts)
2. `Provisional zones` (count + avg span + span cap rejects)
3. `Zone classes` (structural/tradeable)
4. `Tradeable rejects` (score/width/retest)
5. `Retest telemetry` (zones with 0/1/2+ retests)
6. `Nearest visible zone` (class/state/score)
7. `Config digest` (key merge + family budget knobs)

---

## 6) Suggested ACP task packet (post-approval)

- **T1**: Family event budgets + debug counters (Track A)
- **T2**: Structure seed narrowing + protected default off (Track B)
- **T3**: Base shelf detector rewrite + diagnostics (Track C)
- **T4**: Foxian zone-scoring integration (Track D)
- **T5**: `eAtrRef` + merge span governance (Track E)
- **T6**: Retest/lifecycle implementation (Track F)
- **T7**: Deterministic fixture pass on BTC/ETH 1D snapshots
- **T8**: Cert handoff pack (`before/after debug`, shelf coverage notes, unresolved edge cases)

Natural review gates:
- Gate 1 after T2
- Gate 2 after T4
- Gate 3 after T6/T8

---

## 7) Out-of-scope reminder

Still out of scope for this cycle:
- trigger-entry module
- execution policy/risk coupling
- 4H watcher confluence payload finalization (can follow after V7A rebalance gates pass)
