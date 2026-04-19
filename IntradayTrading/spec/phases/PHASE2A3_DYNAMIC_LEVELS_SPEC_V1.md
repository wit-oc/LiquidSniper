# Phase 2A.3 Dynamic Levels Spec v1

Status: ARCHITECTURE DEFINITION, NOT YET CERTIFIED  
Date: 2026-04-13  
Phase: 2A.3  
Owners: Redact + Wit

## Purpose
This document defines the intended architecture for **dynamic levels** inside the Phase 2 watcher.

Phase 2A.3 exists to make the watcher reliably surface **where price currently sits relative to important dynamic levels** so downstream layers can consume those values as raw Surveyor data.

This phase is intentionally narrower than full confluence decisioning.
The watcher should primarily provide a **point-in-time dynamic-level surface contract**, not a heavy scoring or trade-acceptance engine.

## Scope
Phase 2A.3 owns:
- computing the approved dynamic levels for the active symbol / bar / timeframe context
- surfacing where price is relative to each level
- surfacing where the active setup zone is relative to each level
- surfacing technical availability state when a level cannot yet be reconstructed
- preserving candle/feed/provenance metadata so downstream analysis can trust the packet

Phase 2A.3 does **not** own:
- primary structure semantics
- primary S/R discovery
- Fib anchor selection
- final watch qualification policy
- full confluence weighting / ranking
- trigger logic
- lifecycle policy
- execution / risk policy

## Role in the broader architecture
Dynamic levels are a **watcher evidence layer**.

Their job is to answer:
- where is price relative to the important dynamic levels?
- is the active setup area sitting above, below, on, or too close to them?
- are the point-in-time values available, and if not, why not?

Their job is **not** to answer:
- whether a trade should be taken
- whether the setup score is high enough overall
- whether local reaction is sufficient
- whether the watcher should overrule structure, S/R, or Fib

Those heavier judgments belong mostly to the downstream analysis engine and later watch-gating policy.

## Architectural continuity
Phase 2A.3 should remain continuous with the broader Phase 2 watcher build.

### Upstream dependencies
This phase depends on:
- certified Phase 1 structure state
- certified Phase 2A.1 S/R zone context
- certified Phase 2A.2 Fib context where available
- the broader watch-engine candle/feed layer

### Downstream consumers
This phase should feed:
- Phase 2A.4 contract wrapping / normalization
- downstream analysis-engine review / synthesis
- Arbiter, as one raw Surveyor data stream among several
- analyst-facing replay and certification packets

### Provenance coupling
This lane must stay compatible with the sibling structure source-of-truth / Option C work.
Where available, the packet should preserve downstream-facing provenance such as:
- `source_event_id`
- `source_swing_id`
- `source_contract_version`
- selected zone / context identifiers

Do not let dynamic-level telemetry drift into its own isolated provenance model.

## Dynamic levels in scope
The currently approved set is:
- `YVWAP`
- `QVWAP`
- `RYVWAP` (1D only, rolling-year daily-window VWAP)
- `RQVWAP` (1D only, rolling-quarter daily-window VWAP)
- `EMA200`
- `EMA12`

Additional levels should not be introduced casually during this phase.
If the set changes, that should happen through a separate explicit decision.

## Certified timeframe posture
Primary certified dynamic-level timeframes for this phase:
- `1D`
- `4H`

The watcher may eventually maintain additional feed coverage for broader system continuity, but the certified dynamic-level interpretation in this phase is centered on `1D` and `4H`.

## Candle / feed continuity requirement
This phase must not silently invent a separate candle-source contract.

Current planning assumption:
- **OKX is the provisional primary certification feed** unless superseded by control-thread decision.

Minimum eventual watch-owned feed coverage needed for continuity across the broader system:
- `1W`
- `1D`
- `4H`
- `5m`

Dynamic-level certification should therefore preserve explicit candle/feed provenance in its outputs rather than assuming those details can be reconstructed later.

## VWAP price-basis ruling (2026-04-15)
Phase 2A.3 uses **HLC3 / typical price** as the canonical VWAP basis.

That means each VWAP-family surface in Surveyor is computed from:

`((high + low + close) / 3) * volume`

rather than from:

`close * volume`

This decision was made deliberately and should be treated as part of the architecture contract, not an incidental implementation detail.

### Why HLC3 was chosen
- Phase 2A.3 dynamic levels are **supporting context**, not primary trigger logic.
- HLC3 captures the **full bar shape** better than close-only basis.
- HLC3 is less vulnerable to edge-close distortion on large candles or session-boundary-style closes.
- For supporting context, being directionally stable and bar-representative is more important than matching a close-only chart overlay exactly.

### Explicit alternative considered and rejected for canonical Surveyor output
Close-based VWAP was considered because some TradingView / mentorship implementations anchor on close.

We are **not** using close-only basis as the canonical Surveyor output for Phase 2A.3.

Reason:
- close-only basis can place too much weight on where the bar finished,
- while underrepresenting the broader traded range inside the bar,
- which is less desirable for a secondary/supporting evidence layer.

### Operator / research note
Close-based VWAP may still be useful as:
- an external comparison surface,
- a parity check against operator indicators,
- or a future diagnostic/research overlay.

But unless a later decision explicitly changes the contract, the canonical Phase 2A.3 Surveyor VWAP basis is **HLC3**.

## Core doctrine

### 1) The watcher is the map, not the judge
The watcher should mainly surface the dynamic-level landscape.
The analysis engine can do the heavier synthesis about whether that landscape is acceptable for a trade.

### 2) Dynamic levels are a raw Surveyor dataset
Dynamic levels should be surfaced as facts and geometry, not as pre-scored trade context.

### 3) Surface geometry, not judgment
If price is directly below or above important higher-timeframe dynamic levels, the watcher should surface that geometry clearly, but leave the judgment about significance to downstream layers.

### 4) Point-in-time discipline is mandatory
Every surfaced level must be reproducible for the historical bar under review.
No hindsight-selected or forward-aware values.

### 5) No hidden interpretation in Surveyor
Surveyor should not hide Arbiter-facing judgment inside convenient labels. If a field implies trade quality rather than raw geometry, it likely belongs downstream.

## Level role doctrine
To avoid indicator soup, the levels should be thought of in two role buckets.

### Macro / regime context
- `YVWAP`
- `EMA200`

These are the stronger context surfaces.
They matter most when they act as meaningful overhead or underfoot macro friction.

### Flow / operating context
- `QVWAP`
- `RQVWAP` (1D only)
- `EMA12`

These are the lighter local-flow surfaces.
They refine context, but generally should not overrule stronger higher-timeframe contradiction by themselves.

## Inputs
At minimum, the dynamic-level module should consume:
- `symbol`
- `as_of_timestamp`
- active price / bar context
- intended setup direction if available
- active structure permission / state reference
- active zone or selected zone context
- Fib context reference if available
- dynamic-level values for `1D` and `4H`
- candle-source metadata for the bar / timeframe values used

## Outputs
At minimum, the dynamic-level module should emit:
- the dynamic-level values used
- price-relative positioning for each level
- zone-relative positioning for each level
- availability state for each level when data is missing or not yet reconstructable
- provenance and feed metadata needed for replay / audit

## Architecture ruling update (2026-04-14)
This tranche is **raw/descriptive only**.

Surveyor should surface dynamic-level datasets, not trade opinions.
That means Phase 2A.3 may emit:
- raw dynamic-level values
- positional geometry relative to price and zone
- feed/provenance metadata
- technical availability / reconstruction status

That means Phase 2A.3 should **not** emit:
- supportive / neutral / contrary judgments
- macro/local-flow summaries
- confidence or severity hints
- notes that pre-chew meaning for Arbiter

Phase 2A.4 may wrap the contract.
Arbiter is the layer that should synthesize what the data means for trade quality, risk, and execution.

## Required telemetry contract
The watcher should expose a canonical packet with enough truth for later analysis.

### Context header
At minimum:
- `symbol`
- `as_of_ts`
- `intended_direction` (`bullish`, `bearish`, `unknown`) when supplied by upstream context
- `current_price`
- `zone_id` or equivalent selected-zone reference
- `zone_low`
- `zone_high`
- `source_event_id` when available
- `source_swing_id` when available
- `source_contract_version` when available
- `fib_context_id` or Fib reference when available
- `feed_provider`
- `feed_timeframe`
- `feed_bar_ts`
- `feed_provenance_note` or equivalent provenance field

### Per-timeframe dynamic level surface
For each certified timeframe, emit the approved raw level surfaces at minimum:

- `1D`: `YVWAP`, `QVWAP`, `RYVWAP`, `RQVWAP`, `EMA200`, `EMA12`
- `4H`: `YVWAP`, `QVWAP`, `EMA200`, `EMA12`

For each surfaced level, emit at minimum:
- `level_name`
- `timeframe`
- `available`
- `level_value`
- `price_side` (`above`, `below`, `overlapping`)
- `distance_abs`
- `distance_pct`
- `zone_relation` (`above_zone`, `below_zone`, `inside_zone`, `overlapping_zone`, `near_zone`, `far_from_zone`)
- `timeframe_bar_ts`
- `availability_reason` when the value is unavailable

### Explicit non-output for Phase 2A.3
The following are intentionally deferred out of the canonical 2A.3 contract:
- `watcher_label`
- `strength_hint`
- `dynamic_context_label`
- `macro_context_label`
- `local_flow_label`
- `contrary_macro_present`
- `notes_for_analysis_engine`

## Interpretation boundary
Dynamic levels in 2A.3 should stay at the level of **descriptive geometry**.

Allowed examples:
- price is above `1D EMA200`
- price overlaps `4H QVWAP`
- selected zone is near `1D YVWAP`
- `1D RYVWAP` differs from anchored `1D YVWAP` because it is a rolling daily-window surface rather than a calendar anchor
- `QVWAP` unavailable because the quarter anchor history is incomplete

Not allowed examples in this tranche:
- this level is supportive for a long
- macro context is contrary
- dynamic context weakens the setup
- this should downgrade confidence

Those are downstream interpretation concerns for 2A.4 packaging and Arbiter synthesis, not raw Surveyor output.

## Interaction with structure, S/R, and Fib
Dynamic levels should remain subordinate to the already-certified upstream layers.

### Structure
Structure decides directional permission and structural truth.
Dynamic levels do not rewrite structure.

### S/R
S/R decides whether there is a real location worth caring about.
Dynamic levels do not invent the location.

### Fib
Fib describes retracement geometry and pocket quality.
Dynamic levels may strengthen or weaken that context, but should not replace it.

## High-level workflow

### Step A: gather point-in-time level values
Obtain anchored `YVWAP` and `QVWAP` for `1D` and `4H`, plus `RYVWAP` and `RQVWAP` for `1D`, along with `EMA200` and `EMA12`, using the certified candle/feed context.

For all VWAP-family surfaces in this tranche, use **HLC3 / typical price** as the price basis.

### Step B: map current price to each level
Determine where current price sits relative to each level.

### Step C: map active zone to each level
Determine whether the active zone is above, below, overlapping, or near each level.

### Step D: emit descriptive packet fields
Emit raw/descriptive fields only, including availability state, price-side geometry, zone relation, and provenance.

### Step E: defer interpretation downstream
Leave comparative judgment, packaging-level synthesis, and execution implications to Phase 2A.4 and Arbiter.

## Replay and certification requirements
This lane should be certified the same way the adjacent watcher tranches are being certified: via deterministic, point-in-time replay artifacts.

Required certification examples should include:
- BTC replay packet(s)
- ETH replay packet(s)
- at least one packet with all four values available on both certified timeframes
- at least one packet showing an unavailable-value path clearly

Replay packets should show:
- the exact bar under review
- the exact level values used
- current price relative to each level
- active zone relative to each level
- availability state / reason where relevant
- provenance / feed metadata

## Implementation continuity requirement
This phase should preserve continuity with the broader work that spawned it.

That means:
- keep replay-first certification discipline
- keep point-in-time reconstructability
- preserve compatibility with source-of-truth structure threading
- avoid a bespoke sidecar candle contract just for dynamic levels
- keep the watcher packet useful to both Phase 2A.4 and the later analysis engine

Where possible, implementation / replay artifacts should mirror the broader split already used in the project:
- `intraday_revisit/...` research / replay surfaces
- `LiquidSniper/IntradayTrading/...` canonical watcher-implementation surfaces

## Acceptance criteria for this phase
This phase should only pass when:
- dynamic-level values are deterministic and replayable
- `1D` and `4H` level packets are surfaced cleanly and consistently
- price-relative and zone-relative positioning are explicit for every level
- feed and provenance fields are explicit enough for replay/audit
- missing/unavailable values fail clearly rather than silently degrading
- downstream analysis consumers can trust the packet as point-in-time truth without inheriting upstream opinion

## Open placeholders / unresolved questions
The following remain intentionally open.

- `TBD-DYN-001`: exact QVWAP anchor / reset policy
- `TBD-DYN-002`: exact distance thresholds for `near_zone` versus `far_from_zone`
- `TBD-DYN-003`: exact packaging contract for 2A.4 normalization of raw dynamic surfaces
- `TBD-DYN-004`: exact Arbiter-facing contract shape for later synthesis across Surveyor datasets
- `TBD-DYN-005`: whether `1D` and `4H` need any extra non-evaluative metadata beyond the current raw geometry surface

## Non-goals for this spec
This spec does not finalize:
- final watch qualification thresholds
- final no-watch taxonomy
- lifecycle / expiry / re-arm policy
- trigger logic
- execution logic
- full analysis-engine synthesis rules

## Bottom line
Phase 2A.3 should make dynamic levels usable as a **reliable point-in-time surface contract**.

The watcher should mainly tell the truth about:
- where price is,
- where the active zone is,
- where the dynamic levels are,
- whether those values are available,
- and how price/zone are positioned relative to them.

That is enough.
Phase 2A.4 can wrap the contract, and Arbiter can decide what the data means.
