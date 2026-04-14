# Phase 2 Selector Alignment Implementation Packet — 2026-03-30

Status: proposed implementation packet  
Branch: `phase2-zone-engine-v3`

## 1) Executive summary

Phase 2 no longer needs a broad architecture redesign.

The current state is best described as:
- **architecture mostly accepted**
- **selector implementation partially lagging selector doctrine**
- **4H operational surface still too clustered on same-side levels**
- **authoritative review naming still slightly confusing for human review**

So the next tranche should be a **single-stream selector-alignment implementation**, not a new architecture pass and not a blind tuning sweep.

Primary goal:
- make actual selector behavior match `docs/selector_policy_v2.md`
- especially for **4H operational decluttering** and **provenance-aware same-side neighborhood competition**

Secondary goal:
- remove review-surface naming ambiguity so manual chart validation is easier once the implementation is complete

## 2) Architecture verdict for this tranche

This packet assumes the following are already accepted enough to build on:
- canonical Zone Schema V2 remains the center of gravity
- `zone_engine_v3` remains the shadow-first orchestration seam
- Daily major, 4H operational, and nearest-four stay as **distinct selector surfaces**
- provenance-side role (`origin_kind`) stays separate from review/execution-facing role (`current_role`)
- nearest-four payload continuity remains a guardrail

This tranche is therefore **implementation alignment**, not doctrine replacement.

## 3) Source documents / code anchors

Primary references:
- `docs/selector_policy_v2.md`
- `docs/phase2_zone_engine_v3_steering_packet.md`
- `docs/zone_schema_v2.md`
- `docs/PHASE2_SR_TIMEFRAME_REFINEMENT_CHECKPOINT_2026-03-25.md`

Primary code anchors:
- `liquidsniper/core/zone_selectors.py`
- `liquidsniper/core/zone_engine_v3.py`
- `liquidsniper/core/pair_analytics.py`
- `liquidsniper/web/app.py`
- `liquidsniper/ops/sr_bootstrap.py`

## 4) Current mismatch inventory

## M1) Midpoint-led collapse is still stronger than the selector doctrine

Current code still leans heavily on:
- `zone_rank_key(...)`
- `collapse_zones_by_distance(...)`
- `select_spatially_diverse_zones(...)`

Observed issue:
- midpoint distance is still a major abstraction for deciding whether levels are distinct
- this is too thin relative to selector doctrine, especially for **4H operational**
- nearby same-side levels can survive as separate operator-facing zones even when they read like one local neighborhood

Why this matters:
- the doctrine says selectors should operate on canonical zones by surface-specific usefulness
- current implementation can still produce a scalar-score + midpoint-bucket outcome
- this is a likely cause of the remaining BTC/ETH 4H clustering

## M2) 4H same-side local competition is not strong enough

Current 4H operational logic does have a local-representative path:
- `_select_operational_local_representatives(...)`
- `select_operational_zones(...)`

But the current representative logic still appears too permissive because:
- neighborhoods are still fundamentally midpoint-centered
- same-side levels that should probably be demoted to subordinate/debug members can still survive as co-equal operator levels
- post-neighborhood collapse still relies on generic distance pruning

Observed operator symptom:
- BTC 4H staircase above price
- ETH 4H over-stacked above-price resistance ladder
- same-side overlap / near-overlap can still appear in the authoritative view

## M3) Provenance-aware competition is weaker than it should be

The docs now clearly want:
- structure/base/reaction truth preserved
- provenance used to improve confidence and explainability
- selector outputs that prefer corroborated zones over weaker nearby single-family survivors when possible

Current gap:
- there is some provenance sensitivity on the Daily side
- but 4H same-side competition is still not sufficiently **provenance-aware**
- nearby base-only shelves can survive too easily relative to nearby corroborated structure/reaction blends

## M4) Human review naming is still mildly dangerous

Current authoritative-review grouping uses labels like:
- `below_price`
- `contains_price`
- `above_price`

But `zone_schema_v2.md` defines `relative_position` from the perspective of **price relative to zone**:
- `below` = price is below zone
- `above` = price is above zone

Those are inverse perspectives.

This is not the main engine problem, but it remains a review/confusion problem.

## M5) Selector keep/drop traces are still thinner than the policy wants

`selector_policy_v2.md` explicitly asks for compact but concrete trace fields such as:
- `selector_surface`
- `selector_status`
- `selector_reason`
- `selector_rank`

Current selection output is better than before, but this tranche should improve explicit traceability for:
- why a representative survived
- why nearby same-side zones were demoted into subordinate neighborhood members
- why a kept zone beat a close nearby competitor

## 5) Scope of this tranche

In scope:
1. selector implementation alignment with doctrine
2. 4H same-side neighborhood competition / decluttering
3. provenance-aware representative promotion
4. authoritative-view naming cleanup
5. compact selector traces sufficient for post-run review
6. BTC/ETH rerun and checkpoint refresh after full implementation

Out of scope:
- broad V3 architecture redesign
- full new structure-family doctrine pass
- generic parameter sweeps across the basket
- nearest-four payload shape redesign
- user manual review mid-implementation

## 6) Proposed implementation changes

## P1) Add interval-aware neighborhood primitives

Add reusable utilities in `liquidsniper/core/zone_selectors.py` for same-side neighborhood reasoning.

New helper concepts:
- `zone_interval(...)` -> `(low, high, mid)`
- `edge_gap_bps(a, b)`
- `mid_gap_bps(a, b)`
- `interval_overlap_ratio(a, b)`
- `same_side_neighborhood_key(zone)`
- `group_same_side_neighborhoods(...)`

Core rule:
Two same-side zones should compete in the same local neighborhood when **any** of the following are true:
- intervals overlap materially
- edge gap is below a neighborhood threshold
- midpoint gap is small **and** intervals are directionally adjacent

Important stance:
- midpoint gap becomes a fallback signal, not the primary abstraction
- interval overlap / edge distance / side-of-price relevance become primary

## P2) Rewrite 4H operational selection around neighborhood competition

Target functions:
- `_select_operational_local_representatives(...)`
- `select_operational_zones(...)`

Implementation change:
- build neighborhoods by **role + interval proximity**, not mostly by midpoint center
- within each same-side neighborhood:
  - choose one **primary representative**
  - keep the others as subordinate members in metadata
  - do not render multiple co-equal operator-facing zones unless the neighborhood truly contains more than one doctrinally distinct idea

New representative output fields should include compact cluster metadata such as:
- `selector_surface = operational_4h`
- `selector_status = kept`
- `selector_reason = kept: representative of same-side local neighborhood`
- `local_cluster_contract`
- `local_cluster_role`
- `local_cluster_member_count`
- `local_cluster_member_ids`
- `local_cluster_bounds`
- `local_cluster_demoted_ids`

## P3) Add provenance-aware representative scoring

When same-side zones compete inside one local neighborhood, the winner should not be chosen by scalar score alone.

Add a compact representative scoring layer that considers:
- base selector score / selection score
- structure participation
- multi-family confluence
- arbitration confidence / family count
- width penalty when two candidates are otherwise similar
- current-role clarity / surface fit

Desired bias:
- prefer corroborated nearby zones over weak single-family survivors
- prefer cleaner structure/reaction/base blends over lone shelves when evidence is close
- avoid symbolic or ad hoc exceptions

Output requirement:
- preserve compact reviewable reason fields
- do not bury the choice in opaque score math only

## P4) Preserve nearest-four continuity while benefiting upstream

This tranche should **not** redesign nearest-four.

However:
- if nearest-four consumes better canonical / operational survivors upstream, it may improve naturally
- do not change the nearest-four conceptual payload contract in this pass
- only update diagnostics if needed for review parity

## P5) Tighten authoritative-view naming

Target review surfaces and app rendering paths so human-facing group labels clearly mean:
- **zones below price**
- **zones containing price**
- **zones above price**

Implementation rule:
- schema internals may retain `relative_position`
- operator-facing labels should use one consistent perspective only
- do not let presentation naming imply that provenance changed

This is a clarity fix, not a selector-theory fix.

## P6) Add selector traces for keep/demote outcomes

For selected zones, require compact fields such as:
- `selector_surface`
- `selector_status`
- `selector_reason`
- `selector_rank`

For demoted same-side neighbors, require compact cluster trace fields such as:
- `demotion_reason = too close to stronger same-side representative`
- `competition_basis = interval_overlap | edge_gap | provenance_loss | mixed`

This should make post-run review legible without exploding payload size.

## 7) Single-stream execution sequence

This work should run as **one stream**, in this order.

## T1) Selector doctrine audit -> code mapping

Deliverable:
- short mismatch map between `docs/selector_policy_v2.md` and current `zone_selectors.py`

Required output:
- which current functions remain midpoint-led
- where doctrine expects interval/provenance-aware behavior instead
- which parts are Daily-only vs 4H-only vs shared utilities

Exit condition:
- exact implementation seams are documented before edits start

## T2) Introduce shared neighborhood primitives

Deliverable:
- new helper utilities for interval overlap / edge-gap / same-side neighborhood grouping

Exit condition:
- midpoint-only grouping is no longer the only proximity abstraction available

## T3) Rewrite 4H same-side representative competition

Deliverable:
- updated `_select_operational_local_representatives(...)`
- updated `select_operational_zones(...)`
- cluster metadata for primary representatives

Exit condition:
- same-side 4H levels within one local neighborhood compete for one primary operator-facing slot by default

## T4) Add provenance-aware competition bias

Deliverable:
- representative choice now considers provenance/confluence, not just scalar score + midpoint spacing

Exit condition:
- nearby corroborated zones can beat nearby weak single-family alternatives predictably and explainably

## T5) Authoritative-view naming cleanup

Deliverable:
- review surface labels use one consistent human perspective
- schema internals remain unchanged

Exit condition:
- chart review no longer requires mentally inverting `relative_position` semantics

## T6) Selector trace enrichment

Deliverable:
- compact keep/demote reason fields in selector outputs and review surfaces

Exit condition:
- post-run review can explain why a surviving 4H representative won its neighborhood

## T7) Full integrated rerun + checkpoint refresh

Deliverable:
- full BTC/ETH rerun after all implementation changes are complete
- refreshed checkpoint doc summarizing before/after clutter

User-facing note:
- this is the first point where human validation should resume
- no midstream manual review checkpoint is required before T7

## 8) Acceptance criteria

## A) Behavioral acceptance

1. **No architecture regression**
- no collapse back into hidden tuning
- no selector-side family generation hacks
- nearest-four conceptual contract preserved

2. **4H operational decluttering improves materially**
- same-side local clusters are represented by one primary level by default
- overlapping or near-overlapping same-side zones are not shown as co-equal operator levels unless they are genuinely distinct ideas
- operator-facing 4H outputs become visibly less staircase-like on BTC/ETH

3. **Provenance-aware competition is visible**
- when one nearby zone beats another, the review output can explain whether structure/confluence/provenance contributed

4. **Authoritative review surface becomes easier to read**
- human-facing grouping labels are unambiguous
- provenance fields remain secondary diagnostics, not primary review labels

## B) BTC/ETH specific acceptance gates

These are review gates, not hard doctrine forever.

### BTC 4H
Pass target:
- above-price resistance ladder is materially reduced from the current over-stacked state
- no same-side co-equal 4H representatives remain with clear overlap or near-overlap without an explicit doctrinal justification
- local neighborhoods around ~88k / ~90.5k style crowding collapse to one representative + subordinates where appropriate

### ETH 4H
Pass target:
- above-price resistance ladder is materially reduced from the current ~10-zone feel
- nearby same-side resistances with small edge gaps are demoted into representative clusters unless clearly distinct
- output reads as a usable tactical ladder, not a dense inventory dump

### 1D
Guardrail target:
- do not regress the Daily macro/core refinement work just to clean 4H
- Daily still shows macro envelope + core band when available
- Daily should not become proximity-driven because of the 4H tranche

## C) Traceability acceptance

For kept 4H representatives, the output should make it possible to answer:
- what neighborhood did this zone represent?
- what nearby zones were demoted?
- why did this representative win?

## 9) Validation plan

Automated validation to run **after the full implementation stream completes**:
- `tests/test_pair_analytics.py`
- `tests/test_zone_engine_v3.py`
- `tests/test_sr_authoritative_levels_ui.py`
- `tests/test_sr_shadow_authoritative_view.py`
- any new selector-neighborhood tests added by this tranche

Artifact refresh after full implementation:
- `python3 -m liquidsniper.ops.sr_bootstrap --shadow-v3 --symbols BTCUSDT,ETHUSDT`

Checkpoint refresh deliverables:
- updated authoritative BTC/ETH before/after summary
- refreshed checkpoint doc
- explicit clutter/cluster comparison notes

Human validation policy for this tranche:
- Redact will test **after T7**, once the proposed implementation is fully in place
- avoid pausing for intermediate human review unless a blocker or doctrine conflict appears

## 10) Deliverables

Required deliverables for this stream:
1. selector-alignment code changes in `liquidsniper/core/zone_selectors.py`
2. any supporting review-surface changes in app / analytics layers
3. new or updated tests covering neighborhood competition and decluttering
4. refreshed BTC/ETH artifacts
5. refreshed checkpoint summary
6. concise final implementation summary describing:
   - what changed
   - what clustering remains
   - what should be tested next by the human

## 11) Final recommendation

Use this packet as the sole next-stream guide.

Do **not** split into:
- one architecture stream
- one tuning stream
- one UI-only stream

Instead run one ordered stream:
- selector doctrine audit
- neighborhood primitives
- 4H same-side competition rewrite
- provenance-aware promotion
- naming cleanup
- trace enrichment
- full rerun
- then human test

That is the cleanest way to take the GPT 5.4 Pro feedback into account without reopening solved questions.
