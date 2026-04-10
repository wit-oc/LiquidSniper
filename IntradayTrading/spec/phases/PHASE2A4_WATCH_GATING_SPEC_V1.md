# Phase 2A.4 Watch Gating Spec v1

Status: ARCHITECTURE DEFINITION, NOT YET CERTIFIED  
Date: 2026-04-09  
Phase: 2A.4  
Owners: Redact + Wit

## Purpose
This document defines the intended architecture for **watch gating**, the point where the watcher combines structure, S/R, Fib, dynamic levels, and reaction evidence into a coherent setup-state decision.

This phase is where the watcher stops being a collection of modules and becomes a real upstream decision layer.

## Scope
Phase 2A.4 owns:
- setup qualification logic
- combination of approved upstream signals into watcher-ready context
- decision policy for whether a context becomes `WATCH`-eligible
- no-watch / rejection reasoning
- watcher-state evidence packet at the moment of watch qualification

Phase 2A.4 does **not** fully own yet:
- lifecycle expiry / re-arm policy
- UI certification
- final watcher-to-analyst handoff schema
- 15m trigger logic
- trade execution / risk logic

## Inputs
By the time this phase runs, the watcher should already have access to:
- Phase 1 structural permission and event state
- certified S/R zone context
- certified Fib context
- certified dynamic-level confluence context
- reaction evidence at the zone

## Output
The main output of this phase is not a trade.
It is a **watch qualification decision** and its evidence.

At minimum, the watcher should be able to emit:
- `WATCH_ELIGIBLE` or `NO_WATCH`
- reason codes explaining the decision
- the qualified zone / context packet used
- the structural and retracement context at decision time
- reaction-evidence summary

## Core doctrine

### 1) WATCH is a setup-state, not an entry
`WATCH` means:
- the system has enough HTF and setup-context evidence to care
- the analyst engine may now wait for trigger confirmation later

It does **not** mean:
- buy now
- sell now
- trigger confirmed

### 2) WATCH must be explainable
The system should be able to answer:
- why did this become watchable?
- why did this similar-looking thing not become watchable?

### 3) HTF quality still dominates
A low-quality or contradictory HTF context should not be rescued by one pretty local clue.

### 4) Watch gating must remain point-in-time
All decisions must be reconstructable from the data available at that historical bar.

## High-level workflow

### Step A: directional permission check
Read Phase 1 state and determine whether the intended setup direction is allowed.

If direction is not allowed, the watcher should reject early.

### Step B: setup-location check
Confirm that price is interacting with a valid qualified zone or zone cluster from the S/R layer.

If there is no valid location, reject.

### Step C: retracement-context check
Use Fib context to determine whether the setup is happening in a favorable, neutral, or degraded part of the retracement.

### Step D: dynamic-confluence check
Determine whether dynamic levels are supportive, neutral, or contradictory.

### Step E: reaction-evidence check
Confirm that the zone interaction is not just passive overlap, but shows meaningful reaction evidence.

### Step F: watch qualification decision
Combine the above into a final decision:
- `WATCH_ELIGIBLE`
- or `NO_WATCH`

### Step G: emit evidence packet
Record the decision and its reasons so the watcher can later be audited and the analyst can understand the setup context.

## Minimal gating dimensions
The watcher should at least evaluate these dimensions.

### 1) Directional permission
Questions:
- is the setup aligned with the current structural direction?
- is the regime confirmed or transitional?
- if transitional, is reduced-confidence watch ever allowed?

The last question remains open.

### 2) Setup location quality
Questions:
- is price actually interacting with a qualified zone?
- is the zone `STRUCTURAL_ZONE` only, or `TRADEABLE_ZONE`?
- is the zone fresh enough to care about?

### 3) Retracement quality
Questions:
- is the interaction happening in a favorable retracement pocket?
- is the setup too shallow, too late, or too extended?

### 4) Dynamic confluence quality
Questions:
- do dynamic levels support the zone interaction?
- are they neutral?
- are they materially contradictory?

### 5) Reaction evidence quality
Questions:
- is there stall, rejection, displacement, or opposing-momentum loss at the zone?
- is the interaction passive / noisy / low-signal?

## Reaction evidence doctrine
Reaction evidence is important because it stops the watcher from becoming a pure “price is near a level” engine.

The watcher should distinguish between:
- mere touch / overlap
- meaningful reaction
- strong rejection / displacement

The exact scoring is not locked in this spec, but the distinction must exist.

## No-watch doctrine
The watcher should have explicit no-watch reasoning.

Typical categories may include:
- direction not allowed
- no qualified zone
- zone degraded or too spent
- Fib context unfavorable
- dynamic context contradictory
- reaction evidence insufficient
- unresolved regime / ambiguity

Exact reason taxonomy remains to be finalized.

## Relationship to lifecycle
This spec deliberately stops before full lifecycle design.

This phase should define **what makes a context watchable**, but it should not pretend to fully settle:
- expiry policy
- invalidation policy
- re-arm behavior

Those belong to the dedicated lifecycle phase.

## Relationship to the analyst engine
This phase should prepare the watcher to hand a clean context to the analyst later.

At a high level, the analyst should receive enough information to know:
- which zone / context is in play
- what directional permission existed
- why the watcher cared
- what the setup invalidation reference is likely to be

But the full watcher-to-analyst packet remains a later formalization.

## Required telemetry
At minimum, the watch-gating layer should emit:
- watch decision
- reason codes or reason fields
- selected zone identifier / selected zone surface
- directional context snapshot
- Fib context label
- dynamic confluence label
- reaction-evidence label
- timestamp / as-of bar context

## Acceptance criteria for this phase
This phase should only pass when:
- watch decisions are deterministic and replayable
- watch decisions are explainable to a human reviewer
- no-watch outcomes are also explainable
- the watcher can distinguish genuinely qualified contexts from generic level proximity
- the output is stable enough to serve as the future upstream input to the analyst engine

## Open placeholders / unresolved questions
These remain intentionally open.

- `TBD-WATCH-001`: exact gating model, score-based versus rule-stack versus hybrid
- `TBD-WATCH-002`: whether transitional regimes may produce reduced-confidence watch states or must hard-reject
- `TBD-WATCH-003`: exact minimum reaction-evidence requirement before `WATCH`
- `TBD-WATCH-004`: exact interaction between degraded zone freshness and otherwise strong confluence
- `TBD-WATCH-005`: whether `STRUCTURAL_ZONE` may ever become watch-eligible directly, or only `TRADEABLE_ZONE`
- `TBD-WATCH-006`: exact field contract for the evidence packet that later flows to the analyst engine
- `TBD-WATCH-007`: exact reason-code taxonomy for no-watch outcomes

## Non-goals for this spec
This spec does not finalize:
- expiry / invalidation / re-arm lifecycle rules
- UI display rules
- watcher-to-analyst packet schema
- 15m trigger rules
- risk / execution simulation

## Bottom line
Phase 2A.4 is the phase where the watcher becomes a real decision layer.

Its job is to say:
- direction is allowed or not
- the zone interaction is worth caring about or not
- the retracement and confluence context help or hurt
- the reaction is meaningful or not
- therefore this is or is not a `WATCH` candidate

That is the right stopping point before lifecycle and analyst-handoff work.
