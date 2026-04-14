# Phase 2 Selector Alignment Audit — 2026-03-30

Status: completed audit + implementation map  
Branch: `phase2-zone-engine-v3`

## Purpose

This note closes T1 from `docs/PHASE2_SELECTOR_ALIGNMENT_IMPLEMENTATION_PACKET_2026-03-30.md` by mapping the selector doctrine to the concrete implementation seams that were changed in this tranche.

## Audit summary

The selector doctrine in `docs/selector_policy_v2.md` was stronger than the actual implementation in three main ways:

1. **4H operational competition was still too midpoint-led**
   - prior seams: `collapse_zones_by_distance(...)`, `select_spatially_diverse_zones(...)`, and the original `_select_operational_local_representatives(...)`
   - issue: same-side levels could survive as separate operator-facing zones largely because midpoint spacing was treated as the main signal of distinctness

2. **Same-side local competition was not provenance-aware enough**
   - prior seam: representative choice inside 4H local groups still reduced mostly to scalar rank ordering
   - issue: nearby corroborated zones did not consistently beat nearby weaker single-family survivors

3. **Authoritative review labels were semantically easy to invert**
   - prior seam: human-facing labels such as `below_price` / `above_price` were accurate in code, but the UI phrasing still made the schema-vs-review perspective easy to confuse

## Implementation mapping

## A) New interval / neighborhood primitives

Implemented in `liquidsniper/core/zone_selectors.py`:
- `_zone_interval(...)`
- `_mid_gap_bps(...)`
- `_edge_gap_bps(...)`
- `_interval_overlap_ratio(...)`
- `_neighborhood_envelope(...)`
- `_belongs_to_same_side_neighborhood(...)`

Result:
- midpoint distance is no longer the only proximity abstraction available to selector logic
- overlap and edge-gap can now drive same-side local competition directly

## B) Provenance-aware operational representative ranking

Implemented in `liquidsniper/core/zone_selectors.py`:
- `_sources_for_zone(...)`
- `_operational_provenance_weight(...)`
- `_operational_representative_rank_key(...)`

Result:
- nearby multi-family / structure-backed zones can beat nearby weaker single-family alternatives even when raw scalar scores are close
- the competition outcome is explainable through compact diagnostics instead of hidden tie-break behavior only

## C) 4H local representative rewrite

Updated in `liquidsniper/core/zone_selectors.py`:
- `_select_operational_local_representatives(...)`
- `select_operational_zones(...)`

Result:
- same-side 4H zones are grouped into interval-aware local neighborhoods
- each neighborhood now emits one primary representative by default
- non-winning nearby same-side zones are retained as subordinate metadata instead of surfacing as co-equal operator levels

New representative metadata includes:
- `local_cluster_member_count`
- `local_cluster_member_ids`
- `local_cluster_demoted_ids`
- `local_cluster_demotions`
- `local_cluster_competition_basis`
- `local_cluster_representative_weight`
- `local_cluster_representative_diagnostics`

## D) Selector trace enrichment

Updated in:
- `liquidsniper/core/zone_selectors.py`
- `liquidsniper/core/pair_analytics.py`

Result:
- kept zones now preserve compact selector trace fields into downstream review surfaces:
  - `selector_surface`
  - `selector_status`
  - `selector_reason`
  - `selector_rank`
- authoritative review payloads can now show why a representative survived and what it demoted

## E) Human-facing authoritative naming cleanup

Updated in:
- `liquidsniper/ops/sr_bootstrap.py`
- `liquidsniper/web/app.py`

Result:
- authoritative surfaces now explicitly declare `group_perspective = zone_relative_to_price`
- human-facing titles use explicit phrasing such as:
  - `Zones below current price / support context`
  - `Zones containing current price / active band`
  - `Zones above current price / resistance context`
- 4H authoritative selector surface label is now `operational_4h` for clearer contract alignment

## Doctrine alignment verdict

This tranche does **not** redesign selector doctrine.
It does three narrower things:
- reduces midpoint-only operational behavior
- upgrades same-side local competition into interval/provenance-aware competition
- makes review semantics easier to read without changing the underlying schema split

## Deferred items

Still deferred after this tranche:
- deeper structure-family truth improvements beyond selector competition
- broader basket sweeps / parameter sweeps
- any nearest-four contract redesign

Those should wait until human validation confirms the new 4H decluttering behavior is actually better on chart.
