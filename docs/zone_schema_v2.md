# Zone Schema V2

Status: draft for Phase 2 shadow-mode migration  
Branch: `phase2-zone-engine-v3`

## 1) Purpose

Zone Schema V2 defines the canonical merged-zone object for Zone Engine V3 shadow mode.

It exists to solve four problems cleanly:
- represent **structure**, **base**, and **reaction** candidates in one schema
- preserve a single canonical zone object through generation, arbitration, scoring, and selection
- make lifecycle and diagnostics explicit instead of inferred from score alone
- keep **MAP-safe** fields separate from **LIVE-safe** fields so analytical richness does not leak unsafe execution assumptions downstream

This schema is designed for **shadow-first migration**.
It must be expressive enough to compare V3 against the current baseline while preserving the current nearest-four execution payload concept.

## 2) Design principles

1. **One canonical zone, many source families**  
   The merged zone is the durable record. Family-specific generators may vary.

2. **Bounds before scores**  
   A zone is first a price region with provenance and lifecycle, not a score blob.

3. **Diagnostics are first-class**  
   Arbitration, selector keep/drop reasons, and shadow-vs-baseline comparisons must be inspectable.

4. **Selection is downstream policy**  
   The schema must support Daily-major, 4H-operational, and nearest-four selectors without baking those policies into the object definition.

5. **MAP-safe and LIVE-safe fields are not the same thing**  
   Rich analysis fields are useful for review and shadow comparison; execution-facing fields must remain small, stable, and safe.

## 3) Canonical object model

A Zone Schema V2 object has six layers:
- **identity**
- **structural bounds**
- **source-family provenance**
- **lifecycle state**
- **selection/scoring metadata**
- **diagnostics / shadow comparison payloads**

### 3.1 Identity fields

Required:
- `zone_id: str` — canonical id for the candidate or merged zone
- `symbol: str` — market symbol
- `tf: str` — governing timeframe for the zone record (`1D`, `4H`, etc.)
- `zone_kind: str` — `support` or `resistance`

Recommended:
- `engine_contract: str` — versioned contract marker for the producing engine surface
- `source_version: str | null` — source generator version when applicable
- `generated_at: str | null` — ISO timestamp for generation
- `as_of_candle_time: str | null` — candle timestamp anchoring the record
- `origin_kind: str` — canonical/provenance-side role inherited from the zone's source doctrine; defaults to `zone_kind`
- `current_role: str | null` — execution-facing interpretation at the current review price (`support`, `resistance`, `containing`, `neutral`)
- `relative_position: str | null` — relationship between price and zone bounds (`below`, `inside`, `above`, `unknown`)
- `role_semantics_contract: str | null` — explicit version marker for the derived role-semantics adapter

### 3.2 Structural bounds fields

Required:
- `zone_low: float`
- `zone_high: float`
- `zone_mid: float`

Rules:
- `zone_low <= zone_high`
- `zone_mid` should equal the midpoint unless a documented anchor rule overrides it
- bounds are the canonical price definition of the zone

Derived but strongly recommended:
- `zone_width: float` — absolute width
- `zone_width_bps: float | null` — width normalized in basis points
- `zone_width_atr: float | null` — width normalized by local ATR
- `price_anchor: object | null` — compact record describing the anchor used by downstream consumers

### 3.3 Core bounds vs structural bounds

Zone Schema V2 separates the **outer structural envelope** from the **core tradeable band**.

Structural envelope:
- `zone_low`
- `zone_high`
- `zone_mid`

Optional core band:
- `core_low: float | null`
- `core_high: float | null`
- `core_mid: float | null`
- `core_definition: str | null`

Intent:
- structural bounds answer: "what is the broader meaningful region?"
- core bounds answer: "what is the tighter inner band most relevant for touch/reaction/operational use?"

Rules:
- core bounds are optional in Phase 2 shadow mode
- if present, core bounds must lie inside the outer structural envelope unless explicitly marked otherwise
- selectors may use structural or core bounds depending on policy, but they must state which one they used
- **1D refinement doctrine:** the outer `zone_low/zone_high` remains the macro-truth envelope; `core_low/core_high` is the narrower operator-facing anchor band extracted inside that envelope rather than a replacement for it
- **1D surfacing rule:** when a Daily zone carries core bounds, authoritative/operator views should render both the macro band and the core band so reviewers can validate macro context separately from the narrower actionable center
- `core_definition` should name the narrowing rule used (for example `overlap_density_core`, `midpoint_narrowed_core`, or `active_containing_core`) so operator review can distinguish structural truth from presentation refinement

## 4) Source family model

Every zone must preserve source-family provenance.

### 4.1 Candidate family

Required on generated candidates, recommended on merged zones:
- `candidate_family: str`

Allowed Phase 2 values:
- `structure`
- `base`
- `reaction`

### 4.2 Source provenance

Recommended:
- `source_family: str` — concrete generator family/path (`reaction_family`, `base_shelf_v3b`, etc.)
- `source_version: str | null`
- `candidate_sources: list[str]` — all families represented in the merged zone
- `merged_from_zone_ids: list[str]` — canonical member ids merged into this zone
- `merge_candidate_count: int`
- `merge_family_count: int`

Interpretation:
- `candidate_family` describes doctrinal role
- `source_family` describes actual generator implementation
- `candidate_sources` and `merge_family_count` describe confluence after arbitration

## 5) Lifecycle state model

A zone needs lifecycle semantics independent of raw score.

### 5.0 Role semantics split (new Phase 2 contract clarification)

`zone_kind` / `origin_kind` answer: **what kind of zone did the engine generate?**
They are provenance fields and should remain stable across review surfaces.

`relative_position` answers: **where is price relative to this zone right now?**
Allowed values for the current branch:
- `below` — price is below the zone
- `inside` — price is inside/contained by the zone
- `above` — price is above the zone
- `unknown` — no reference price was supplied

`current_role` answers: **how should the zone be interpreted on the current review/execution surface?**
Default derived mapping for Phase 2:
- `below` -> `resistance`
- `above` -> `support`
- `inside` -> `containing`
- `unknown` -> `neutral`

Critical rule:
- **do not overwrite origin/provenance semantics with review-time role semantics**
- a resistance-origin zone that price has already moved above still keeps `origin_kind=resistance`, but may surface as `current_role=support`
- a support-origin zone that currently contains price should surface as `current_role=containing`, not be mislabeled as static support just because of provenance

### 5.1 Zone status

Required:
- `status: str`

Phase 2 allowed values:
- `candidate` — generated but not yet arbitration-confirmed
- `confirmed` — accepted as a valid candidate/merged zone in the canonical set
- `invalidated` — structurally broken or rejected for live consideration
- `archived` — retained for comparison/history only

### 5.2 Interaction lifecycle

Recommended:
- `first_touch_state: str | null`
- `interaction_buy: object | null`
- `interaction_sell: object | null`

Typical interaction states:
- `virgin`
- `first_touch`
- `retest`
- `deep_test`
- `broken`
- `counter_side`

Rule:
- lifecycle state describes how price has interacted with the zone, not whether the zone belongs in a specific selector output.

## 6) Scoring and selector metadata

Scores are allowed, but they are not the schema's center of gravity.

Recommended scalar fields:
- `strength_score: float | null`
- `selection_score: float | null`
- `reaction_score: float | null`
- `reaction_efficiency_score: float | null`
- `carry_score: float | null`
- `body_respect_score: float | null`
- `family_confluence_bonus: float | null`
- `atr_local: float | null`

Selector trace fields:
- `selector_surface: str | null` — e.g. `daily_major`, `operational_4h`, `nearest_four`
- `selector_status: str | null` — `kept`, `dropped`, `shadow_only`, etc.
- `selector_reason: str | null` — compact human-readable explanation
- `selector_rank: int | null`

Rule:
- A zone may exist with no selector assignment.
- Selection outcomes should be recorded as trace metadata, not as permanent doctrinal truth.

## 7) Diagnostics payload

Diagnostics are mandatory for shadow-mode review.

### 7.1 Arbitration diagnostics

Recommended object:
- `arbitration_diagnostics: object | null`

Suggested shape:
- `cluster_size: int`
- `families: list[str]`
- `kept_zone_id: str | null`
- `kept_source_family: str | null`
- `family_confluence_bonus: float`
- `score_components: object`
- `candidates: list[object]`

Each candidate row should retain at least:
- zone id
- family
- source family
- tf
- low/high/mid
- base score / major score components
- whether it was kept
- kept/drop reason

### 7.2 Shadow comparison diagnostics

Recommended object:
- `shadow_comparison: object | null`

Suggested fields:
- `baseline_contract: str | null`
- `baseline_zone_id: str | null`
- `baseline_relation: str | null` — `matched`, `split`, `merged`, `missing`, `extra`
- `nearest_four_delta: object | null`
- `daily_major_delta: object | null`
- `operational_delta: object | null`

Purpose:
- make V3-vs-baseline disagreement visible without requiring forensic reconstruction later

## 8) MAP-safe vs LIVE-safe separation

This distinction is non-optional.

### 8.1 MAP-safe fields

MAP-safe fields are allowed in diagnostics, notebooks, docs, and shadow-review surfaces.
They may be verbose and explain *why* a zone exists.

Examples:
- family provenance fields
- arbitration candidate tables
- score breakdowns
- selector reasons
- shadow comparison deltas
- lifecycle/interactions for both sides
- raw structural/core bounds plus helper normalization fields

### 8.2 LIVE-safe fields

LIVE-safe fields are the minimal fields suitable for downstream execution-adjacent payloads.
They must remain stable and easy to reason about.

Required LIVE-safe minimum:
- `zone_id`
- `symbol`
- `tf`
- `zone_kind`
- `zone_low`
- `zone_high`
- `zone_mid`

Recommended LIVE-safe additions when already part of the current payload concept:
- `selection_score`
- `status`
- compact proximity/side classification
- compact source/confluence marker if it does not bloat the payload contract

### 8.3 Separation rule

- MAP-safe records may contain LIVE-safe subsets.
- LIVE-safe payloads must not require consumers to interpret bulky diagnostics.
- Nearest-four migration work must preserve the current execution payload concept even if MAP-safe records become richer.

## 9) Minimal JSON-style reference shape

```json
{
  "zone_id": "BTCUSDT:4H:merged:123",
  "symbol": "BTCUSDT",
  "tf": "4H",
  "zone_kind": "support",
  "origin_kind": "support",
  "current_role": "support",
  "relative_position": "above",
  "role_semantics_contract": "zone_role_semantics_v1",
  "status": "confirmed",
  "engine_contract": "zone_engine_v3d",
  "candidate_family": "reaction",
  "source_family": "reaction_family",
  "source_version": "sr_engine_v2_reaction_family",
  "candidate_sources": ["reaction", "base"],
  "merged_from_zone_ids": ["a", "b"],
  "merge_candidate_count": 2,
  "merge_family_count": 2,
  "zone_low": 61234.0,
  "zone_high": 61520.0,
  "zone_mid": 61377.0,
  "core_low": 61280.0,
  "core_high": 61460.0,
  "core_mid": 61370.0,
  "core_definition": "inner_reaction_band",
  "zone_width_bps": 46.6,
  "zone_width_atr": 0.82,
  "atr_local": 348.2,
  "strength_score": 77.4,
  "selection_score": 81.2,
  "reaction_score": 73.0,
  "reaction_efficiency_score": 71.5,
  "carry_score": 62.0,
  "family_confluence_bonus": 4.0,
  "first_touch_state": "virgin",
  "price_anchor": {
    "kind": "merged_zone_mid",
    "zone_mid": 61377.0,
    "zone_low": 61234.0,
    "zone_high": 61520.0
  },
  "arbitration_diagnostics": {
    "cluster_size": 2,
    "families": ["base", "reaction"],
    "kept_zone_id": "a"
  },
  "shadow_comparison": {
    "baseline_contract": "sr_engine_v2",
    "baseline_relation": "matched"
  }
}
```

## 10) Validation rules for Phase 2

A valid V2 zone record should satisfy all of the following:
- identity fields present
- `zone_low`, `zone_high`, and `zone_mid` present and numerically coherent
- `zone_kind` is support or resistance
- provenance is explicit enough to tell which family/families produced the zone
- status is explicit
- diagnostics are optional for transport but required for shadow-review artifacts
- MAP-safe and LIVE-safe exports are generated as separate views, not by consumer guesswork

## 11) What this schema does not decide

This schema deliberately does **not** decide:
- how Daily major zones are selected
- how many 4H operational zones are kept
- exact nearest-four ranking logic
- score weights
- whether core bounds should override structural bounds in any selector

Those belong in selector policy and acceptance test docs, not in the schema itself.

## 12) Phase 2 implementation guidance

For the current branch, the practical target is:
- keep using the existing nearest-four execution payload concept
- enrich the canonical map object with family provenance and diagnostics
- allow shadow artifacts to compare baseline and V3 cleanly
- avoid adding selector-specific hacks into the schema layer

If there is tension between richness and stability, prefer:
- rich **MAP-safe** records for review
- small **LIVE-safe** records for downstream execution continuity
