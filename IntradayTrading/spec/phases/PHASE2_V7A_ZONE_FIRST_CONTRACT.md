# Phase 2 — V7A Zone-First Implementation Contract

Status: DRAFT READY (pending control-thread approval)
Target branch: `phase2-v7-zone-first-20260307`
Target file: `IntradayTrading/pine/PHASE2A_SR_WATCHER_V7A_ZONE_FIRST.pine`

## 1) Objective (V7A only)

Build a deterministic, 1D-first zone pipeline where zones are first-class objects and candles/structure are evidence inputs.

## 2) Hard constraints

- No trigger entries (15m/5m) in V7A.
- No execution/risk lifecycle in V7A.
- No pre-zone hard suppression that can delete high-value evidence.
- Keep existing Foxian metrics, but as evidence channel (not sole discovery path).

## 3) Core objects

## 3.1 Evidence event (first-class input)
Required fields:
- `event_id`
- `event_type` (`STRUCT_BOS_ANCHOR|STRUCT_FLIP_ANCHOR|STRUCT_PROTECTED_LEVEL|BASE_SHELF|BASE_BREAKOUT|FOXIAN_LAUNCH`)
- `tf_tag` (`1D` for V7A)
- `time_open`, `time_close`
- `dir` (`bull|bear|neutral`)
- `top`, `bot`, `mid`
- `evidence_score`
- optional channel scores (`launch_score`, `base_score`, `structure_score`, `local_q`)

## 3.2 Provisional zone (stage object)
Required fields:
- `z_top`, `z_bot`, `z_mid`
- `birth_time`
- `source_mask` (bitset-ish flags by event type)
- `best_bull_evidence`, `best_bear_evidence`
- `best_launch_score`, `best_base_score`, `best_structure_score`
- `avg_local_q`
- `event_count`
- `retest_count`
- `state` (`fresh|active|weakening|broken`)
- `zone_score`
- `zone_class` (`STRUCTURAL_ZONE|TRADEABLE_ZONE`)

## 4) Pipeline stages (must remain explicit)

### Stage A — Event generation
Generate event arrays from 3 channels:
1) Structure events (v3.3 semantics)
2) Base events (shelf/balance detector)
3) Foxian reaction events

### Stage B — Provisional zone build
- Merge event intervals by overlap-first logic.
- Keep direction evidence as zone fields, not permanent zone polarity.
- Only dedupe exact duplicates at this stage.

### Stage C — Zone scoring
Compute zone-level scores (not candle-level pass/fail):
- `structure_score`
- `base_score`
- `launch_score`
- `flip_score`
- `freshness_score`

Default weighted score (V7A map mode):
- 0.30 structure
- 0.25 base
- 0.20 launch
- 0.10 flip
- 0.15 freshness

### Stage D — Classify zone
- `STRUCTURAL_ZONE` if significance is high but tradeability gates fail.
- `TRADEABLE_ZONE` if it also passes width/freshness/display gates.

### Stage E — Select/render
- Apply visible thinning and display ranking after class assignment.
- Structural zones remain visible (lighter visual style).

## 5) Minimum base detector (V7A)

Inputs:
- `baseWindowBars`
- `baseMinOverlapFrac`
- `baseMaxATRSpan`
- `baseMinTouches`
- `baseBreakMinATR`

Outputs:
- `BASE_SHELF` event (`top/bot/mid`, `base_score`)
- `BASE_BREAKOUT` event (`dir`, `break_score`)

## 6) Structure-seed contract (V7A)

Must emit these event types from v3.3-compatible semantics:
- `STRUCT_BOS_ANCHOR`
- `STRUCT_FLIP_ANCHOR`
- `STRUCT_PROTECTED_LEVEL`

Note: in Pine, this is function/library reuse, not cross-study runtime dependency.

## 7) V7A debug panel contract (compact, screenshotable)

Required rows:
1. `Events generated` (counts by event type)
2. `Provisional zones` (count + avg span)
3. `Zone classes` (`structural/tradeable`)
4. `Top reasons for tradeable rejection` (width/freshness/score/etc)
5. `Nearest zone` (mid + class + state + score)
6. `Config digest` (single-line compact)

Optional expanded rows (toggle):
- channel-specific score breakdown
- per-event tape snippets

## 8) Deterministic acceptance checks (V7A)

On BTC/ETH 1D fixtures:
- [ ] Major known shelves are present at least as STRUCTURAL_ZONE.
- [ ] Tradeable set is a strict subset of structural set.
- [ ] Re-running on same chart segment yields identical zone list and classes.
- [ ] No `NO_CLUSTER` paradox for bands where accepted evidence exists.

## 9) Implementation checklist

- [ ] Create new Pine file: `PHASE2A_SR_WATCHER_V7A_ZONE_FIRST.pine`
- [ ] Implement Stage A/B/C/D/E as separate functions
- [ ] Add compact debug table rows listed above
- [ ] Add `mode: MAP|LIVE` guard (V7A can default MAP)
- [ ] Commit with message prefix: `phase2(v7a): ...`

## 10) Handoff outputs

After V7A initial build:
- screenshot pack (BTC/ETH 1D)
- one-page phase handoff using template
- open items for V7B structure parity and V7C base tuning
