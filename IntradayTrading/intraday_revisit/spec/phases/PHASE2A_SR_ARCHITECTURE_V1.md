# PHASE2A — S/R Architecture V1 (WATCH/INVALID/EXPIRED only)

## 0) Scope
Phase 2 watcher-only engine for intraday revisit certification.
- **In scope:** zone lifecycle, retest counting, invalidation decisions, optional expiry hook (disabled by default), reason codes.
- **Out of scope:** entries, triggers, execution, risk, sizing.

Doctrine implemented:
1. S/R are **reaction zones** (not single lines).
2. **First retest** is highest-opportunity (tracked explicitly).
3. Zone width scales with candle/timeframe.
4. Zones are spaced/non-overlapping; keep strongest reaction locus.
5. Zones persist (no age decay). Retest counters reset only on confirmed flip.
6. HTF zones override LTF.
7. Flip confirmation = break close beyond zone + separation + 4–6 candle base + retest-ready.
8. Touches alone never reset counters.

---

## 1) Runtime inputs (Phase 2A)

Minimal required inputs for watcher + TV validator:

```text
inputs:
  symbol: string                 // e.g., BTCUSDT, ETHUSDT
  chartTf: string                // active TV timeframe (e.g., 15m)
  htfList: string[]              // higher TFs to project authority (e.g., ["1h","4h"])
  ohlcv: bar[]                   // timestamp, open, high, low, close, volume
  session:
    timezone: string             // display/ops only
    enableExpiry: bool=false     // default OFF
  sr:
    kAtr: float=0.35
    atrLen: int=14
    minTicks: number|fn(tf)
    maxTicks: number|fn(tf)
    mergeOverlap: float=0.30
    minZoneSpacing: float=1.25
    closeBreakTolK: float=0.05
    sepK: float=0.75
    baseTolK: float=1.00
    baseBarsMin: int=4
    baseBarsMax: int=6
    reclaimK: float=0.25
    flipConfirmWindowBars: int=12
    touchEpsilonK: float=0.02
```

Optional diagnostics inputs:
- pivot sensitivity params
- wick/close weighting for reaction locus
- fixture id + replay start/end

## 2) Core data model

```text
Zone {
  id,
  symbol,               // BTCUSDT, ETHUSDT
  tf,                   // source timeframe (e.g., 15m, 1h, 4h)
  side,                 // SUPPORT | RESISTANCE
  top,
  bottom,
  mid,
  width,
  strengthScore,        // deterministic score from pivot/reaction metrics
  htfRank,              // higher rank = higher timeframe authority

  state,                // ACTIVE | FLIP_CANDIDATE | FLIPPED_ACTIVE | INVALID | EXPIRED (EXPIRED disabled by default)
  retestCount,
  firstRetestSeen,      // bool

  breakCloseBar,        // bar index/time if close beyond zone is confirmed
  separationSeen,       // bool
  baseCount,            // 0..N bars in post-break consolidation window
  flipConfirmed,        // bool

  createdAt,
  lastTouchAt,
  lastStateAt,
  expiresAt             // optional session/timebox expiry
}
```

### Zone width default
For each candidate zone on timeframe `tf`:
- `ATRn = ATR(14)` on same `tf`
- `width = clamp(k_atr * ATRn, minTicks(tf), maxTicks(tf))`
- `top/bottom` centered on selected reaction locus (wick/close blend).

**Defaults:**
- `k_atr = 0.35`
- No per-symbol width presets in v1.
- Use one global formulation first; only add symbol overrides after validation proves persistent outliers.

---

## 2) Detection and normalization rules

1. Build raw pivot/reaction candidates.
2. Convert each to zone band using width rule.
3. Enforce non-overlap/spacing inside same symbol+tf:
   - If overlap ratio > `mergeOverlap`, keep stronger zone; weaker dropped.
   - If distance between mids < `minZoneSpacing * max(widthA,widthB)`, keep stronger.
4. Cross-timeframe precedence:
   - If LTF zone conflicts with HTF zone (overlap + opposite side), HTF zone wins for watcher decisions.
   - LTF can remain stored for diagnostics but not decision-authoritative.

**Defaults**
- `mergeOverlap = 0.30`
- `minZoneSpacing = 1.25`

---

## 3) State machine

```text
ACTIVE
  ├─(touch/reaction)──────────────────────────────> ACTIVE      [increment retestCount]
  ├─(hard invalidation)───────────────────────────> INVALID
  └─(break close beyond zone)─────────────────────> FLIP_CANDIDATE

FLIP_CANDIDATE
  ├─(no separation within window)─────────────────> ACTIVE       [cancel candidate]
  ├─(separation met, base 4–6 bars met)───────────> FLIPPED_ACTIVE [reset retestCount]
  └─(reclaim invalidation before base complete)───> INVALID

FLIPPED_ACTIVE
  ├─(touch/reaction in new role)──────────────────> FLIPPED_ACTIVE [increment retestCount]
  └─(hard invalidation)───────────────────────────> INVALID

[Optional, disabled by default]
ANY_ACTIVE_STATE ─(explicit operator policy only)─> EXPIRED
```

### Event definitions
- **Touch:** bar range intersects zone band.
- **Break close beyond zone:**
  - Support broken: close < `bottom - closeBreakTol`
  - Resistance broken: close > `top + closeBreakTol`
- **Separation:** price extends beyond broken zone by `sepK * width` before reclaim.
- **Base (consolidation):** 4–6 consecutive bars with range contained within `baseTolK * width` around post-break structure.
- **Reclaim invalidation:** close back through original zone boundary by `reclaimK * width` before flip confirmed.

---

## 4) Threshold defaults (v1)

Use these as deterministic starting defaults:

- `k_atr = 0.35` (zone half-band scaling anchor)
- `closeBreakTol = 0.05 * width`
- `sepK = 0.75` (required post-break separation)
- `baseTolK = 1.00` (max base envelope around post-break structure)
- `baseBarsMin = 4`
- `baseBarsMax = 6`
- `reclaimK = 0.25` (reclaim amount to invalidate candidate)
- `flipConfirmWindowBars = 12` (if no full confirmation by then, revert ACTIVE)
- `touchEpsilon = 0.02 * width` (debounce micro-touches)

Notes:
- These defaults are intentionally conservative for watcher stability.
- Tune only via TV validation loop; do not expand scope into signal/entry logic.

---

## 5) Retest counter logic

- On first qualifying touch after zone creation/flip: `retestCount = 1`, `firstRetestSeen = true`.
- Every subsequent qualifying touch increments by +1.
- **No reset** from touch clusters, chop, or simple boundary pokes.
- Reset to 0 **only** when flip is fully confirmed (`break close + separation + base`).

---

## 6) INVALID and EXPIRED policy

### INVALID (structural failure)
Set INVALID when any applies:
1. Reclaim invalidation during `FLIP_CANDIDATE`.
2. HTF contradictory zone fully dominates and local zone no longer decision-valid.
3. Data integrity failure (malformed zone bounds, negative width, etc.).

### EXPIRED (operational hook, default OFF)
Default Phase 2A behavior: **do not expire zones**.
- Zones persist indefinitely unless structurally invalidated or flipped.
- No passive “old zone” decay.

If teams later enable EXPIRED, it must be explicit policy (not automatic age-based logic), e.g. feed halted / operator maintenance mode.

---

## 7) Reason codes (deterministic)

```text
SR_ZONE_CREATED
SR_ZONE_MERGED_STRONGER
SR_ZONE_DROPPED_OVERLAP
SR_ZONE_HTF_OVERRIDDEN

SR_TOUCH_QUALIFIED
SR_TOUCH_DEBOUNCED
SR_FIRST_RETEST
SR_RETEST_INCREMENTED

SR_BREAK_CLOSE_CONFIRMED
SR_FLIP_SEPARATION_MET
SR_FLIP_BASE_PROGRESS
SR_FLIP_CONFIRMED
SR_FLIP_CANDIDATE_CANCELLED

SR_INVALID_RECLAIM
SR_INVALID_HTF_DOMINANCE
SR_INVALID_DATA

SR_EXPIRED_POLICY
SR_EXPIRED_FEED
```

All transitions/events must emit exactly one primary reason code.

---

## 8) Acceptance criteria (Phase 2A)

1. **Deterministic replay:** same candles => identical zone states/reason-code stream.
2. **No-overlap invariant:** authoritative zones for same symbol/tf do not overlap after normalization.
3. **HTF precedence:** conflict tests always resolve to HTF decision path.
4. **Flip strictness:** retest counter resets only after full flip confirmation chain.
5. **Touch resilience:** repeated touches/chop do not reset state.
6. **Watcher-only:** no trigger/entry side effects emitted.
7. **No-expiry default:** no EXPIRED transitions occur unless explicit policy flag is enabled.
8. **Reason completeness:** every state transition has a valid reason code.

---

## 9) Deterministic test fixtures (BTC/ETH first)

Fixture format: OHLCV CSV + expected event log (jsonl).

### BTC fixtures
1. `BTC_15m_first_retest_hold`
   - Scenario: fresh support zone, first revisit reacts, no break.
   - Expect: `ACTIVE`, `retestCount=1`, `SR_FIRST_RETEST`.
2. `BTC_15m_break_sep_base_flip`
   - Scenario: support breaks, separates >= `sepK`, bases 4–6 bars, flips to resistance.
   - Expect: `FLIPPED_ACTIVE`, `retestCount reset`, `SR_FLIP_CONFIRMED`.
3. `BTC_15m_false_break_reclaim_invalid`
   - Scenario: break close occurs, but reclaim exceeds `reclaimK` before base complete.
   - Expect: `INVALID`, `SR_INVALID_RECLAIM`.

### ETH fixtures
4. `ETH_1h_htf_overrides_ltf`
   - Scenario: 1h resistance conflicts with 15m support candidate.
   - Expect: LTF non-authoritative; `SR_ZONE_HTF_OVERRIDDEN`.
5. `ETH_15m_touch_cluster_no_reset`
   - Scenario: multiple rapid touches around band.
   - Expect: increment/debounce behavior, no reset, no flip.
6. `ETH_15m_spacing_overlap_resolution`
   - Scenario: overlapping candidate cluster.
   - Expect: strongest retained, others merged/dropped by deterministic rule.

Pass condition for each fixture:
- exact state sequence match,
- exact reason code sequence match,
- exact retestCount series match.

---

## 10) Persistence model (updated)

Phase 2A does **not** require durable long-term zone persistence.
- Zones are recalculated on-chart from available OHLCV context.
- Runtime may keep a **cache** for performance and audit only.

Recommended cache backends:
- Local JSON (fastest iteration, easy inspect/debug)
- Parquet (better for batch replay + analytics)

Cache contents (suggested):
- computed zones snapshot per bar
- state/reason-code event stream
- retest counter timeline
- HTF override decisions

Cache policy:
- write-through during replay/validation runs
- safe to rebuild from source candles
- no strategy dependency on cache survival

## 11) Implementation notes (non-scope-expanding)
- Keep zone scoring deterministic (no random tie-breaks).
- Tie-break order: `strengthScore desc`, then `htfRank desc`, then earliest `createdAt`.
- Persist raw events in cache for auditability in Phase 2 certification runs.
