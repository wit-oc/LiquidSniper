# Phase 2A.2 Fib Context Spec v1

Status: ARCHITECTURE DEFINITION, NOT YET CERTIFIED  
Date: 2026-04-09  
Phase: 2A.2  
Owners: Redact + Wit

## Purpose
This document defines the intended architecture for the **Fib context module** inside the watcher engine.

This phase exists to add direction-aware retracement context to the existing structural and S/R framework without replacing either of them.

Where decisions are not yet truly locked, this spec leaves placeholders instead of pretending certainty.

## Scope
Phase 2A.2 owns:
- selection of Fib anchor pairs from approved HTF structure state
- derivation of premium / discount style context
- direction-aware Fib context for watcher qualification
- coupling between Fib context and setup-quality interpretation

Phase 2A.2 does **not** own:
- raw market structure semantics
- raw S/R zone discovery
- dynamic-level confluence
- full watcher gating threshold policy
- trigger logic
- lifecycle expiry/re-arm
- execution / risk policy

## Role in the broader architecture
Fib context is a **ranking and qualification layer**, not a primary discovery engine.

It should answer questions like:
- is this retracement shallow, moderate, or deep relative to the active HTF move?
- is price currently in a favorable premium/discount region for the active directional thesis?
- does the zone interaction align with the expected retracement geometry of the current structure?

It should **not** answer:
- where the zone is
- what the structure direction is
- whether a trigger has occurred

Those belong to other modules.

## Upstream dependencies
Fib context depends on:
- certified Phase 1 structure state
- approved Phase 2A.1 S/R zones / review surfaces
- current timeframe context being analyzed (at minimum 1D and 4H)

## Downstream consumers
Fib context should feed:
- watcher setup qualification
- later confluence aggregation
- eventual analyst packet context

## Core doctrine

### 1) Structure first
Fib anchors must be selected from structure truth, not from arbitrary local swings chosen for visual convenience.

### 2) S/R remains primary location logic
Fib context can improve or weaken the quality reading of a setup, but it should not override a bad zone or invent a new one.

### 3) Direction-aware interpretation
Fib should be interpreted in the context of the active directional thesis.
A bullish retracement and a bearish retracement are not labeled the same way.

### 4) Point-in-time only
Fib anchors and levels must be reproducible using only information available at that historical bar.
No hindsight-selected swing pairs.

## Inputs
At minimum, the Fib module should consume:
- symbol
- timeframe under analysis
- current price / bar timestamp
- active directional permission from Phase 1
- approved structure anchors or protected-level context
- approved S/R zone map or selected relevant zone

## Outputs
At minimum, the Fib module should produce:
- anchor pair used for the current context
- direction of the retracement interpretation
- Fib levels derived from that pair
- current price location relative to those levels
- qualitative context label for the retracement
- reason metadata explaining why the anchor pair was selected

## High-level workflow

### Step A: obtain directional context
Read the active directional permission and confidence from Phase 1.

### Step B: select eligible structural anchors
Form a candidate set of anchor pairs that are legal under the active structure contract.

### Step C: choose the anchor pair for the current watcher context
Apply the anchor policy to select the pair that best represents the live retracement context.

### Step D: derive Fib levels and regime labels
Compute the retracement levels from the chosen anchor pair.

### Step E: classify the current price context
Map current price relative to the Fib levels into a watcher-useful context label.

### Step F: emit auditable metadata
Record why this anchor pair and this classification were chosen.

## Anchor policy architecture
This is one of the most important parts of the phase and should remain explicit.

### Working direction
The anchor pair should be derived from the active structural leg, not from arbitrary local noise.

### Legal anchor sources
Potential legal anchor sources may include:
- latest confirmed directional impulse leg
- latest confirmed structural continuation leg
- latest valid CHoCH-to-confirmation leg if the direction is now transitional but permitted
- fallback structural pair when one side of the preferred pair is stale or missing

### Anchor policy requirements
Whatever policy is chosen later, it must answer:
- what is the primary source pair?
- what is the fallback hierarchy?
- how do 1D and 4H interact when both are available?
- when does a new structural event invalidate the old anchor pair?

## Fib level interpretation
This spec intentionally avoids locking exact levels until the anchor policy is better settled.

However, the module should support the concept of:
- favorable retracement area
- neutral / mid retracement area
- stretched / degraded retracement area

The exact numeric bands remain an explicit placeholder.

## Direction-aware premium / discount interpretation
The watcher will eventually need a direction-aware answer to:
- is current price attractive for continuation into the active direction?
- is price already too extended or too late in the retracement?

### Placeholder rule shape
For bullish setups, the module should be able to distinguish at least:
- acceptable discount / pullback context
- mid-range context
- premium / late-chase context

For bearish setups, mirror the logic.

### Not yet locked
The exact mapping of Fib ranges to these labels is not locked in this spec.

## Interaction with S/R zones
Fib context should be applied **after** location logic has already identified a relevant zone or setup area.

Questions Fib should help answer:
- does the zone sit inside a favorable retracement pocket?
- is the current interaction happening too shallow / too extended?
- does a structurally valid zone also have acceptable retracement geometry?

Fib should not be used as the sole reason for `WATCH`.

## Interaction with invalidation
Fib context may eventually influence how setup quality is interpreted relative to invalidation distance, but that policy is not yet locked.

Potential relationships to define later:
- whether deeper retracements weaken the setup score
- whether certain retracement bands imply tighter or looser tolerance to invalidation
- whether some Fib contexts should disallow normal-risk watch states

## Required telemetry
When the module is implemented, the watcher should be able to inspect:
- selected anchor pair
- anchor timestamps
- anchor source reason
- computed Fib levels
- current price-relative band
- directional interpretation label
- fallback flag if a non-primary anchor source was used

## Acceptance criteria for this phase
This phase should only pass when:
- anchor selection is deterministic
- anchor choice is explainable from structure state
- bullish / bearish interpretations are symmetric and coherent
- current price classification is stable under replay
- Fib context improves watcher qualification without replacing structure or S/R truth

## Open placeholders / unresolved questions
These are intentionally unresolved until deeper design work happens.

- `TBD-FIB-001`: exact legal primary anchor pair definition for 1D
- `TBD-FIB-002`: exact legal primary anchor pair definition for 4H
- `TBD-FIB-003`: fallback hierarchy when preferred anchors are stale, missing, or structurally ambiguous
- `TBD-FIB-004`: exact Fib levels / bands that map to discount, neutral, and premium context
- `TBD-FIB-005`: whether one unified Fib policy should serve both Daily and 4H, or whether timeframe-specific policy is needed
- `TBD-FIB-006`: whether retracement context should be categorical only or also add a continuous score contribution
- `TBD-FIB-007`: exact coupling rules between Fib context and setup invalidation tolerance

## Non-goals for this spec
This spec does not finalize:
- dynamic-level confluence
- final watch threshold scoring
- lifecycle handling
- trigger behavior
- execution behavior

## Bottom line
Phase 2A.2 should add **structure-derived retracement context** to the watcher.

It should help the watcher answer whether a structurally valid S/R interaction is happening in a favorable part of the retracement, while remaining subordinate to:
- Phase 1 structure truth
- Phase 2A.1 zone truth
- point-in-time replay discipline
