# Phase2A S/R Watcher V6 Spec Sheet (Foxian-Aligned, Quant-Grounded)

Date: 2026-03-05
Status: Draft for implementation
Scope: TradingView visual engine now, portable watcher/analytics/trade-engine later

---

## 1) Objective

Build a deterministic Support/Resistance engine that:
- identifies high-quality **reaction anchors** from price behavior,
- clusters anchors into sparse, robust **zones**,
- aligns with Foxian mentorship guidance,
- can be ported with parity from TradingView -> watcher/analytics -> auto-trade engine.

Core policy shift for V6:
- **Excursion + reversal quality is primary.**
- Candle geometry (body/wick, local extrema) is secondary/contextual.

---

## 2) Non-negotiable design principles (from Foxian guidance)

1. **Zones, not precise lines**
   - S/R are approximate regions, not exact prices.
   - Source themes: 59th (~00:10:59+), 12th (~00:53:46+).

2. **Maximum reaction concentration**
   - Map where the most meaningful reactions occur.
   - Source themes: 13th (~00:12:49+), 59th (~00:11:10+).

3. **Top-down process**
   - Start on HTF, refine on lower TF.
   - Source themes: 12th (~00:45:08+).

4. **First retest priority / retest decay**
   - First retest has highest expectancy; repeated retests weaken edge.
   - Source themes: 11th (~00:39:18+), 14th (~00:32:08+), 16th/17th repeated retest discussions.

5. **Keep charts clean (anti-clutter)**
   - Fewer strong zones > many weak zones.
   - Source themes: 14th (~00:09:36+), 59th title/theme.

6. **Handle extreme deviation explicitly**
   - Massive wick/fakeout regimes can invalidate normal deviation logic.
   - Source themes: 59th (~00:28:48+).

---

## 3) Quant/signal basis (methods V6 uses)

- **Path-dependent excursion metrics** (MFE/MAE family logic)
- **Signal prominence & peak quality** (not just local pivot booleans)
- **Dominance suppression (NMS-like)** to avoid anchor spam
- **Density/cluster methods in 1D price space** (DBSCAN/KDE style)
- **ATR/time normalization** for cross-timeframe portability

(Reference links listed in Section 13.)

---

## 4) Architecture for portability

Use the same logical pipeline across all runtimes:

1. **Core deterministic spec** (language-agnostic formulas + reason codes)
2. **TradingView indicator adapter** (visualization + diagnostics)
3. **Watcher/analytics adapter** (incremental state updates + event logs)
4. **Execution adapter** (later) consuming watcher events only

Rule: TradingView is the visual certification surface, not a separate algorithm.

---

## 5) Canonical data contracts

### 5.1 AnchorEvent
- `anchor_id`
- `ts_open`, `ts_close`
- `side` (`resistance` | `support`)
- `anchor_price`
- `atr_ref`
- `excursion_atr` (E)
- `excursion_time_bars` (tE)
- `reversal_atr` (R)
- `reversal_ratio` (rho = R / max(E, eps))
- `persist_count`
- `revisit_count`
- `quality_score` (Q)
- `candidate_flags` (`local_extrema`, `range_ok`, etc)
- `accept`
- `fail_reason_primary`
- `fail_reason_all[]`
- `version` (`v6`)

### 5.2 ZoneEvent
- `zone_id`
- `side_mode` (`merged` | `side-separated`)
- `top`, `bottom`, `mid`
- `touch_count`
- `cluster_score`
- `retest_count`
- `state` (`candidate` | `active` | `weakening` | `broken` | `flipped`)
- `created_ts`, `updated_ts`
- `source_anchor_ids[]`
- `version` (`v6`)

---

## 6) V6 algorithm spec

## 6.1 Time normalization
Inputs in **hours**, converted to bars per timeframe:
- `W_move_h`, `W_reversal_h`, `W_persist_h`, `W_revisit_h`, `W_gap_same_h`, `W_gap_opp_h`

Normalization reference:
- ATR-based magnitude normalization (`ATR(14)` default)
- All excursion/reversal values measured in ATR units.

## 6.2 Candidate stream (anchor universe)
For each historical bar `i`, evaluate both sides:
- resistance candidate price `p_i = high_i`
- support candidate price `p_i = low_i`

Candidate prefilters (optional/soft in V6):
- local-extrema flag
- minimum bar-range ATR flag

Important:
- These **must not hard-veto** high-quality excursion/reversal anchors by default.
- They contribute as score modifiers/diagnostic flags.

## 6.3 Excursion-reversal metrics (primary)
For each candidate and side:

Let `ATR_i = atr(i)`.

### Resistance side
- Away path (down move):
  - `away(k) = (p_i - low_{i+k}) / ATR_i`, `k in [1..W_move]`
- `E = max away(k)`
- `tE = argmax away(k)`
- Reversal after excursion low:
  - `rev(k) = (high_{i+k} - low_{i+tE}) / ATR_i`, `k in [tE+1 .. W_reversal]`
- `R = max rev(k)`

### Support side
- Away path (up move):
  - `away(k) = (high_{i+k} - p_i) / ATR_i`
- `E = max away(k)`
- `tE = argmax away(k)`
- Reversal after excursion high:
  - `rev(k) = (high_{i+tE} - low_{i+k}) / ATR_i`
- `R = max rev(k)`

Common:
- `rho = R / max(E, eps)`

Interpretation:
- High `E` + meaningful `rho` => reaction had both expansion and reversal quality.

## 6.4 Persistence, revisit, and outlier guards
- **Persistence**:
  - Resistance: count closes below `p_i - persistTolATR * ATR_i`
  - Support: count closes above `p_i + persistTolATR * ATR_i`
- **Revisit**:
  - Count closes that cross back beyond anchor tolerance (`revisitTolATR`).
- **Outlier deviation guard**:
  - If overshoot against expected reaction is extreme (`deviationInvalidATR`), mark `OUTLIER_DEV`.
  - This is Foxian-aligned handling for massive wick/fakeout regimes.

## 6.5 Quality score Q (0..100)
Define normalized components:
- `qE`: excursion quality
- `qR`: reversal quality (`rho`)
- `qS`: speed quality (`1 - tE/W_move`)
- `qP`: persistence quality
- `qN`: revisit cleanliness
- `qD`: retest decay factor (`exp(-lambda * prior_retests_at_zone)`) to prioritize early interactions

Score:
- `Q = 100 * (wE*qE + wR*qR + wS*qS + wP*qP + wN*qN) * qD`

Default hard gates:
- `E >= E_min`
- `rho >= rho_min`
- `persist_count >= persist_min`
- `Q >= Q_min`
- `not OUTLIER_DEV`

Candidate prefilter flags modify score slightly but do not block by default.

## 6.6 Retention + dominance suppression
After anchor acceptance:
- sort by `Q` desc (stable tiebreak: older timestamp first)
- apply side-aware temporal gap suppression:
  - same-side gap >= `W_gap_same`
  - opposite-side gap >= `W_gap_opp`
- keep up to `maxAnchorsKept` and/or `retentionPercent`

Goal: sparse dominant anchors, no spam.

## 6.7 Zone clustering from accepted anchors
Cluster in 1D price space using weighted proximity:
- `weight = Q * age_weight`
- tolerance = max(`clusterTolPct * price`, `clusterTolATR * ATR_ref`, `2*tick`)

Implementation options:
- DBSCAN-like density grouping (portable)
- or deterministic greedy weighted merge with same tolerance

Cluster outputs:
- center = weighted median price
- envelope = weighted quantile band (core + optional extreme cap)
- `touch_count` = unique reaction interactions
- `cluster_score` = weighted sum with retest decay penalties

Promotion rules:
- `touch_count >= 3` (Foxian minimum legitimacy)
- `cluster_score >= minClusterScore`
- width <= `maxClusterWidthPct`

## 6.8 Zone lifecycle (for watcher/trade portability)
State machine:
- `candidate` -> `active` -> `weakening` -> `broken` -> optional `flipped`

Transition hints:
- `active`: meets touch/score rules
- `weakening`: repeated retests + shrinking reaction amplitude
- `broken`: confirmed close through zone boundary with buffer
- `flipped`: broken level later acts opposite side (support<->resistance)

---

## 7) TradingView indicator requirements (V6 visual engine)

Visual outputs:
- accepted anchor dots (score-gradient color)
- optional failed-anchor dots by reason code
- zone boxes (core envelope), optional midline
- zone state coloring (candidate/active/weakening/broken/flipped)
- nearest-zone telemetry

Diagnostics required:
- per-gate fail buckets counts
- inspect-one-candle full boolean vector:
  - `C_soft`, `E`, `R`, `P`, `N`, `D`, `Q`, `G` (gap)
- reason chain logging style (single primary + full list)

No repaint policy (portable behavior):
- Anchor finalization only after required future window matures.
- Once finalized, anchor and reason codes are immutable.

---

## 8) Watcher/analytics portability requirements

- Mirror exact formulas and reason codes from indicator spec.
- Incremental processing must match batch replay outputs.
- Persist canonical events (`AnchorEvent`, `ZoneEvent`) for audit.
- Version-lock parameters + reason taxonomy (`v6`).
- Deterministic ordering, no random tie breaks.

---

## 9) Default V6 baseline (certification start)

Suggested initial baseline (BTC 1D cert pass):
- `W_move_h = 96`
- `W_reversal_h = 96`
- `W_persist_h = 72`
- `W_revisit_h = 96`
- `E_min = 2.5 ATR`
- `rho_min = 0.25`
- `persist_min = 4`
- `revisitTolATR = 0.20`
- `persistTolATR = 0.60`
- `Q_min = 58`
- `W_gap_same_h = 120`
- `W_gap_opp_h = 24`
- `retentionPercent = 25%`
- `maxAnchorsKept = 180`
- `minClusterPoints = 3`
- `minClusterScore = 7.0`
- `clusterTolPct = 0.018`
- `maxDisplayZones = 12`

Note: tune by failure bucket, not by aesthetic preference.

---

## 10) Reason code taxonomy (lock for V6)

Anchor-level reasons:
- `FAIL_E_MIN`
- `FAIL_R_RATIO`
- `FAIL_PERSIST`
- `FAIL_REVISIT`
- `FAIL_DEV_OUTLIER`
- `FAIL_SCORE_Q`
- `FAIL_GAP_SUPPRESS`
- `FAIL_RETAIN_DROP`

Zone-level reasons:
- `FAIL_CLUSTER_MIN_POINTS`
- `FAIL_CLUSTER_MIN_SCORE`
- `FAIL_CLUSTER_WIDTH`

State reasons:
- `STATE_WEAKENING_RETEST_DECAY`
- `STATE_BROKEN_CLOSE_CONFIRM`
- `STATE_FLIPPED_RECLAIM`

---

## 11) Certification tests (must pass before V6 freeze)

1. **Contested candle replay test**
   - Reproduce known missed orange-circle candles.
   - Inspect must show full gate booleans + Q decomposition.

2. **Cross-timeframe sanity**
   - BTC 1D, BTC 1W, ETH 1D, one lower TF.
   - Compare anchor density, zone count, nearest-zone stability.

3. **Determinism test**
   - Re-run same dataset => identical anchors/zones/reasons.

4. **Portability parity test**
   - TV replay vs watcher replay parity on anchor and zone events.

---

## 12) Explicit non-goals in this phase

- No auto-entry logic yet.
- No strategy expectancy claims from indicator visuals alone.
- No hidden discretionary overrides.

---

## 13) External references supporting this direction

Excursion / path-dependent metrics:
- https://help.tradestation.com/10_00/eng/tradestationhelp/subsystems/spr_topics/report/maximum_favorable_excursion__strategy_performance_report_.htm
- https://help.tradestation.com/10_00/eng/tradestationhelp/subsystems/spr_topics/report/maximum_adverse_excursion__strategy_performance_report_.htm
- https://mlfinpy.readthedocs.io/en/stable/Labelling.html

Signal extraction / peak quality:
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.peak_prominences.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.peak_widths.html
- https://scikit-image.org/docs/stable/api/skimage.feature.html#skimage.feature.peak_local_max

Clustering / density zones:
- https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
- https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KernelDensity.html

Regime/change segmentation:
- https://centre-borelli.github.io/ruptures-docs/

Normalization / computational TA foundation:
- https://ta-lib.github.io/ta-doc/indicator/ATR.htm
- https://www.nber.org/papers/w7613

---

## 14) Implementation plan (immediate)

Phase V6-A (anchor engine):
- implement Sections 6.1-6.6 + diagnostics
- certify on contested candles and fail buckets

Phase V6-B (zone engine):
- implement Sections 6.7-6.8
- certify zone stability/sparsity

Phase V6-C (portability harness):
- mirror contracts in watcher runtime
- run parity replay and lock v6
