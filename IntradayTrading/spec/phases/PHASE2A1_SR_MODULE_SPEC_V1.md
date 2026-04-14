# Phase 2A.1 S/R Module Spec v1

Status: WORKING MODEL EXISTS, CERTIFICATION CLOSEOUT PENDING  
Date: 2026-04-09  
Phase: 2A.1  
Owners: Redact + Wit

## Purpose
This document is the canonical Phase 2A.1 spec for the **support/resistance module** inside the watcher-engine program.

It records the logic and workflow that appear to be working now, while separating proven design choices from areas that still need explicit certification or refinement.

This spec is written to avoid two failures:
1. forgetting the durable lessons from the long S/R thread
2. silently overcommitting to details that were never truly decided

## Repo evidence already present
The repo already contains meaningful S/R documentation and implementation artifacts, but they are fragmented across redesign packets, review bundles, and execution docs.
Relevant artifacts include:
- `IntradayTrading/spec/phases/PHASE2_PYTHON_SR_PLATFORM_SPEC_2026-03-08.md`
- `IntradayTrading/spec/phases/PHASE2_V7_ZONE_FIRST_REFACTOR_PROPOSAL_2026-03-07.md`
- `IntradayTrading/spec/phases/PHASE2_V7A_ZONE_FIRST_CONTRACT.md`
- `IntradayTrading/spec/phases/PHASE2_SR_V3_REDESIGN_PROPOSAL_2026-03-15.md`
- `docs/PHASE2_SR_PROMOTION_GATE_2026-03-16.md`
- `docs/PHASE2_SR_GATEC_SELECTOR_DOCTRINE_COMPARISON_2026-03-16.md`
- `liquidsniper/core/zone_engine_v3.py`
- `liquidsniper/core/zone_selectors.py`
- `tests/test_zone_engine_v3.py`

## Current status
The current best read is:
- an S/R model is working well enough to be treated as a **real Phase 2A.1 module**, not just an idea
- the module appears near-closeout after multiple redesign passes
- the remaining work is closeout / certification discipline, not a return to square one

Known remaining closeout / certification items:
1. final human live-map review
2. one small regression basket beyond BTC/ETH
3. explicit `WATCH / INVALID / EXPIRED` lifecycle audit before calling broader Phase 2 complete
4. merge the closeout branch back cleanly after review

## Scope
Phase 2A.1 owns:
- HTF support/resistance zone discovery
- zone merging and provenance retention
- zone role semantics for operator-facing views
- zone selection surfaces for watcher review
- point-in-time zone snapshots for certification/review

Phase 2A.1 does **not** own:
- Fib context
- dynamic levels
- full watcher gating logic
- lifecycle certification beyond what is minimally needed to interpret zone state
- 15m trigger logic
- risk/execution behavior

## Core doctrine
The S/R engine should be treated as a **zone-first** system with structure-seeded evidence.

That means:
- zones are first-class objects
- candles/events are evidence inputs, not the final product
- structure truth is upstream of S/R, not subordinate to it
- operator review surfaces must preserve truth instead of collapsing everything into a single generic score

## Relationship to Phase 1 market structure
Phase 1 remains the source-of-truth structure layer.
Phase 2A.1 uses that output as mandatory seed evidence.

The S/R module should not invent its own incompatible structural worldview.
Instead, it should consume:
- directional context
- BoS / CHoCH lineage
- protected-level / anchor semantics
- seed events for structure-driven zone generation

## Evidence families
The working design assumes S/R discovery may use multiple evidence families.
At minimum, the current architecture recognizes:
- **structure family**
- **base / shelf family**
- **reaction / launch family**

### Structure family
Structure-derived candidates are generated from certified structural events.
This is the highest-trust family for aligning zones with the broader market-structure framework.

### Base / shelf family
Base-like price balance or shelf behavior may generate candidates that capture persistence and repeated acceptance/rejection behavior.

### Reaction / launch family
Reaction logic and Foxian-style excursion behavior can contribute useful evidence.
But this family should remain supporting evidence, not the sole discovery path.

## Core objects

### 1) Candidate zone
A candidate zone is a pre-merge zone interval with family-specific provenance.

A candidate should be able to say:
- what family generated it?
- what bounds did it propose?
- what evidence or quality fields were attached?

### 2) Canonical / merged zone
Merged zones are the main working objects after arbitration.
They should retain:
- merged interval bounds
- provenance by family
- source version info
- diagnostics explaining which candidate was kept as representative and why

### 3) Review-surface zone
A zone as shown to the operator is not just a raw merged object.
It is also interpreted through:
- current price-relative role
- current selector surface
- neighborhood / ladder context

## Zone classes
The module should preserve the distinction between:
- `STRUCTURAL_ZONE`
- `TRADEABLE_ZONE`

### Structural zone
A structurally important location that deserves to remain visible/auditable, even if it is not currently the best execution-facing context.

### Tradeable zone
A structural zone that also passes the additional quality / width / freshness / usability rules required for watcher and later analyst use.

## Merge and provenance workflow
The current doctrine expects the following flow.

### Step A: generate family-specific candidates
Produce zone candidates separately from structure, base, and reaction families.

### Step B: cluster overlapping / near-overlapping candidates
Candidates that represent the same underlying price neighborhood should be merged into a canonical cluster.

### Step C: keep provenance instead of flattening history
After merge, the resulting zone should preserve:
- contributing family list
- family-specific provenance
- representative selection details
- any family-confluence bonus / arbitration diagnostics

### Step D: preserve family truth into selection
Selector layers should know whether a zone is:
- pure-base only
- structure corroborated
- multi-family corroborated

This is important because the engine already appears to prefer corroborated structure participation over pure-base-only candidates when those are otherwise close.

## Role semantics doctrine
This was one of the major painful lessons from the Phase 2 S/R work.

The engine must separate:
- `origin_kind`
- `current_role`
- `relative_position`

### origin_kind
How the zone was originally formed or historically classified.
Examples:
- support-origin
- resistance-origin
- flip-origin

### current_role
What the zone means **now**, relative to current price and execution-facing interpretation.
Examples:
- support
- resistance
- containing

### relative_position
Where the zone sits relative to price.
Examples:
- below current price
- above current price
- containing current price

### Hard rule
Operator-facing surfaces should use **current_role** and price-relative grouping as the primary truth.
`origin_kind` remains provenance / diagnostics.

This prevents the false and confusing outputs that look like:
- resistance below price
- support above price

## Selector surfaces
The module should preserve multiple distinct review surfaces rather than flattening all answers into one universal nearest list.

The durable separation to preserve is:
- `daily_major`
- `operational_4h`
- nearest / proximity ladders

### daily_major
Used to preserve the higher-timeframe major map.
This surface should preserve macro truth and not let generic proximity logic erase key daily levels.

### operational_4h
Used for actionable context on the 4H operating frame.
This can be more selective and more interaction-oriented than daily majors.

### nearest / proximity ladders
These answer convenience questions such as nearest support/resistance or next support/resistance.
They should not silently redefine what the major map actually is.

## Daily coverage doctrine
Daily coverage should be classified by macro envelope rather than by a narrowed display core alone.

Useful envelope labels include:
- `zone_low`
- `zone_high`
- `zone_mid`

A narrowed core may still be useful for display or precision, but it should not replace the broader macro pocket truth.

## Same-side competition doctrine
Same-side competition should remain neighborhood-aware.

That means the selector should not always let a generic top score wipe out nearby same-side levels that belong to the same meaningful operating neighborhood.

This is especially important on 4H and on the nearest ladder.

## Review / operator workflow

### Step 1: build point-in-time snapshot
The module should emit a point-in-time zone snapshot for a specific symbol, timeframe, and bar.

### Step 2: inspect authoritative view
The operator should be able to inspect:
- below price
- containing price
- above price
for both Daily and 4H review surfaces.

### Step 3: inspect selector traces when something looks wrong
If a level is missing or a wrong one is surfaced, the review path should answer:
- did the level exist in raw candidates?
- did merge remove it?
- did selection remove it?
- what won instead, and why?

### Step 4: compare with chart truth
The operator should then compare the surfaced levels against chart-marked truth and classify them as:
- good
- borderline
- wrong

## Authoritative review surface
`bootstrap_snapshot.json` is currently the best durable candidate for the authoritative review surface.

The point is not the filename itself.
The point is that there must be a single review artifact where the operator can inspect the real point-in-time zone map without reverse-engineering internal code.

## Current implementation-direction truths worth preserving
These appear durable enough to preserve in the canonical spec:
- the architecture is **not** back at square one
- native structure participation matters materially
- role semantics needed to be separated from provenance
- selector surfaces need to preserve major-map truth separately from nearest convenience
- selector traces matter more than generic score nudging when truth looks wrong

## Validation and certification expectations
To formally close 2A.1, the module should have:
- a clean operator-facing authoritative view
- replayable point-in-time snapshots
- selector traces for BTC/ETH truth loss points
- one broader regression basket beyond BTC/ETH
- explicit documentation of what remains outside 2A.1

## Open placeholders / unresolved questions
The following should remain explicit until separately decided.

- `TBD-SR-001`: exact thresholds for candidate clustering / overlap / neighborhood grouping
- `TBD-SR-002`: final weighting policy between structure, base, reaction, freshness, and retest quality
- `TBD-SR-003`: exact promotion rules from `STRUCTURAL_ZONE` to `TRADEABLE_ZONE`
- `TBD-SR-004`: final operator-facing rules for how containing bands should interact with nearest ladders
- `TBD-SR-005`: final lifecycle vocabulary for zone exhaustion, re-arm, and deep-test handling once lifecycle work is formalized
- `TBD-SR-006`: exact multi-timeframe arbitration rules when Daily and 4H disagree on apparent nearest importance

## Non-goals for this spec
This spec does not finalize:
- Fib anchor policy
- dynamic-level scoring policy
- watcher gating thresholds
- lifecycle expiry/re-arm rules
- watcher-to-analyst packet schema

Those belong to later phase specs.

## Bottom line
Phase 2A.1 now has a real S/R model and a real doctrine.

The canonical truths to preserve are:
- zone-first architecture
- structure-seeded discovery
- provenance retention
- role-semantics separation
- distinct review surfaces
- point-in-time operator review

What remains is mostly certification discipline and later-phase integration, not rediscovering what the S/R engine is supposed to be.
