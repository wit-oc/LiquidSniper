# Phase 2A.3 Dynamic Levels Spec v1

Status: ARCHITECTURE DEFINITION, NOT YET CERTIFIED  
Date: 2026-04-09  
Phase: 2A.3  
Owners: Redact + Wit

## Purpose
This document defines the intended architecture for **dynamic levels** as a watcher-engine confluence layer.

This phase exists to make dynamic context usable without letting it hijack the system into indicator soup.

## Scope
Phase 2A.3 owns:
- normalization of selected dynamic levels
- interpretation of those levels as confluence inputs
- directional alignment logic for dynamic levels
- watcher-facing metadata showing how dynamic context strengthens or weakens setup quality

Phase 2A.3 does **not** own:
- primary structure semantics
- primary S/R discovery
- Fib anchor selection
- full watcher gating thresholds
- trigger logic
- lifecycle policy
- execution / risk policy

## Candidate dynamic levels in scope
The currently intended set includes:
- `QVWAP`
- `YVWAP`
- `EMA12`
- `EMA200`

Additional dynamic levels should not be added casually during this phase without a separate decision.

## Role in the broader architecture
Dynamic levels are **confluence inputs only**.

They may influence:
- setup ranking
- confidence adjustments
- no-trade filters in obviously contradictory conditions

They should not become:
- the main reason a setup exists
- a replacement for structure
- a replacement for S/R zones
- a replacement for Fib context

## Core doctrine

### 1) Dynamic levels are supporting evidence
The system should still be able to explain a setup without saying “because EMA did something.”

### 2) Alignment matters more than raw touches
The important question is not merely whether price is near a dynamic level.
The question is whether that level aligns coherently with:
- active direction
- HTF structure
- selected S/R zone
- retracement context

### 3) Contradiction matters too
Dynamic levels should also be able to say when a setup is being asked to fight obviously poor context.

### 4) Point-in-time discipline still applies
Dynamic-level values must be reproducible at the historical bar under review.

## Inputs
At minimum, this module should consume:
- current symbol / timeframe context
- current price / as-of timestamp
- active directional permission
- approved S/R setup context
- Fib context, if already available
- current values for each dynamic level in scope

## Outputs
At minimum, this module should emit:
- dynamic-level values used for the current bar
- alignment flags by level
- contradiction flags by level
- a compact confluence summary for the watcher
- audit metadata explaining which levels materially affected the interpretation

## High-level workflow

### Step A: gather level values
Obtain the selected dynamic-level values for the current symbol / timeframe / bar.

### Step B: map level relationship to price and zone
Determine whether the level is:
- inside / overlapping the active zone
- just outside the zone but supportive
- far away and irrelevant
- contradictory to the intended setup

### Step C: apply direction-aware interpretation
Interpret the level relative to the active directional thesis.
What is supportive for a bullish setup is not identical to what is supportive for a bearish one.

### Step D: emit confluence summary
Produce watcher-usable metadata that says whether the dynamic context:
- supports the setup
- is neutral / irrelevant
- weakens the setup
- blocks the setup under later watcher-gating policy

## Level-by-level design intent

### QVWAP
Intended role:
- session / quality-weighted mean context
- useful as a structure-alignment and “are we fighting the operating mean too hard?” check

Not yet locked:
- exact anchor and reset policy

### YVWAP
Intended role:
- broader benchmark / macro participation context
- useful for checking whether the setup is leaning with or against a larger reference mean

Not yet locked:
- exact interpretation priority relative to QVWAP and HTF zones

### EMA12
Intended role:
- short-horizon operating flow / short-term directional texture
- useful for detecting whether the local move is stalling or accelerating into the zone

Not yet locked:
- whether EMA12 should ever materially boost a setup versus only act as a weak confirmer

### EMA200
Intended role:
- major trend / macro dynamic support-resistance context
- useful as a high-level confluence or contradiction check

Not yet locked:
- whether EMA200 can create a hard blocker on its own or only modify quality

## Interaction with structure and S/R
Dynamic levels should be applied after the system already knows:
- the active structure direction
- the relevant S/R zone or zone cluster

Dynamic levels should answer questions like:
- is the zone also aligned with a meaningful moving or weighted mean?
- is price reclaiming or rejecting the level in a way that supports the setup?
- is the intended setup fighting a major dynamic barrier?

## Interaction with Fib context
Once Fib is available, dynamic levels can help answer:
- does the retracement pocket also align with meaningful dynamic support/resistance?
- is the zone a confluence cluster or just a single reason setup?

But dynamic levels must remain subordinate to:
- structure
- S/R
- retracement context

## Recommended confluence posture
The safest design posture is:
- dynamic levels add **small to moderate** quality adjustments
- only obviously strong contradiction should become a later no-trade input

This avoids indicator-stack overfitting.

## Required telemetry
When implemented, the module should expose at least:
- each dynamic level value used
- price distance to each level
- whether each level overlaps / supports / contradicts the active zone
- any summary weight or categorical interpretation
- explanation text or reason codes suitable for watcher review

## Acceptance criteria for this phase
This phase should only pass when:
- dynamic-level values are deterministic and replayable
- supportive vs contradictory interpretations are coherent and symmetric by direction
- dynamic levels improve explanation quality without becoming the main discovery logic
- operator review can clearly see whether a level helped, hurt, or did nothing

## Open placeholders / unresolved questions
The following remain explicitly open.

- `TBD-DYN-001`: exact anchor / reset policy for QVWAP
- `TBD-DYN-002`: exact weighting or precedence between QVWAP and YVWAP
- `TBD-DYN-003`: whether dynamic-level confluence is categorical only or partly numeric
- `TBD-DYN-004`: exact hard-block conditions, if any, for contradiction against EMA200 or VWAP context
- `TBD-DYN-005`: exact distance / overlap thresholds that define “aligned” versus merely “nearby”
- `TBD-DYN-006`: whether all levels should be computed on the same timeframe context or mixed across HTF and operational frames

## Non-goals for this spec
This spec does not finalize:
- watch-state thresholds
- lifecycle rules
- UI design details
- analyst handoff packet
- trigger / execution logic

## Bottom line
Phase 2A.3 should make dynamic levels useful as **disciplined confluence**, not as a replacement worldview.

The watcher should be able to say:
- this setup is structurally valid
- the S/R context is real
- the Fib context is favorable or not
- the dynamic levels support, weaken, or contradict the setup

That is enough for this phase.
