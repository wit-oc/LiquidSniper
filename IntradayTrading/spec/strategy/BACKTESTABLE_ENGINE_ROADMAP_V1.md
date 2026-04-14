# Backtestable Engine Roadmap v1

Status: ACTIVE ROADMAP  
Date: 2026-04-09

## Purpose
This document captures the remaining path from the current project state to a **working engine that can be backtested honestly**.

It preserves the intended architecture split:
- **Market Structure Module** determines directional truth.
- **Watcher Engine** tracks qualified setup context.
- **Analyst Engine** evaluates trigger confirmation.
- **Risk/Execution Simulation Layer** produces backtestable trade outcomes.

Live execution remains out of scope.

## Current state

### Done
- Phase 1 market structure module exists and is documented as certified.
- TradingView and Python artifacts for Phase 1 are already recorded in the repo.
- The Phase 2 watcher architecture has been tightened around:
  - point-in-time reconstruction
  - 1D directional permission
  - 1D/4H setup context
  - 15m trigger role as a later phase
  - 5m refinement-only posture

### Nearly done
- Phase 2A.1 S/R appears implementation-complete and now has a closeout commit/PR path, but is not fully signed off yet.
- Remaining known closeout items:
  1. final human live-map review
  2. one broader regression basket beyond BTC/ETH
  3. explicit lifecycle audit before claiming broader watcher completion
  4. review/merge of the closeout branch

## What counts as “backtestable engine”
The engine becomes meaningfully backtestable only when all of the following are true:
1. structure state is deterministic
2. watcher context is deterministic and point-in-time reconstructable
3. trigger decisions are separated from watcher decisions
4. candidate trades carry explicit invalidation / reason data
5. a simulation layer can turn those packets into a reproducible trade ledger

That milestone lands at **Phase 4**, not at Phase 2.

## Architecture to preserve

### Phase 1: Market Structure Module
Owns:
- BoS / CHoCH / protected-level truth
- directional permission
- structural seed evidence for downstream modules

### Phase 2: Watcher Engine
Owns:
- S/R zones
- Fib context
- dynamic-level confluence
- reaction evidence
- `WATCH / INVALID / EXPIRED` eventually

### Phase 3: Analyst Engine
Owns:
- 15m trigger confirmation
- optional 5m refinement after valid 15m context
- candidate trade packet creation

### Phase 4: Risk/Execution Simulation Layer
Owns:
- entry / stop / target simulation
- partial / move-to-BE policy
- portfolio rules and breakers
- deterministic performance outputs

## Remaining roadmap

### Phase 2.0 — Contracts / telemetry lock
Needed outputs:
- watch-state event schema
- reason-code taxonomy
- review snapshot contract

### Phase 2A.1 — S/R module certification
Needed outcomes:
- close remaining review / regression / lifecycle-closeout items
- preserve structure-seeded zone-first doctrine
- preserve selector-trace and authoritative review surfaces

### Phase 2A.2 — Fib context
Needed outcomes:
- structure-derived anchor policy
- retracement interpretation
- premium / discount context

### Phase 2A.3 — Dynamic levels
Needed outcomes:
- confluence-only integration for QVWAP / YVWAP / EMA12 / EMA200
- alignment and contradiction rules

### Phase 2A.4 — Watch gating
Needed outcomes:
- combine structure, S/R, Fib, dynamic levels, and reaction evidence into watch qualification logic

### Phase 2B — Lifecycle certification
Needed outcomes:
- `WATCH / INVALID / EXPIRED / re-arm`
- deterministic transitions

### Phase 2C — UI v1
Needed outcomes:
- operator-facing review surfaces that faithfully represent watcher truth

### Phase 2D — Watcher-to-analyst handoff
Needed outcomes:
- formal packet for downstream trigger logic
- exact allowed fields and semantics

### Phase 3A — Trigger engine
Needed outcomes:
- 15m trigger contract
- trigger-quality explanation
- local invalidation references

### Phase 3B — Retest ordinal
Needed outcomes:
- first-touch / later-touch distinction
- degradation logic

### Phase 3C — Score calibration
Needed outcomes:
- analyst scoring calibration
- false-positive control

### Phase 4 — Risk / execution simulation
Needed outcomes:
- deterministic trade ledger
- stop / target / management rules
- portfolio breaker logic
- backtest outputs that can be rerun honestly

### Phase 5 — Config-only tuning
Needed outcomes:
- tuning after core contracts exist

### Phase 6 — Promotion + parity
Needed outcomes:
- promotion checklist
- parity / regression proof after tuning or refactor changes

## Hard guardrail
Every layer must remain **point-in-time reconstructable**.

If any layer cheats with hindsight-selected zones, hindsight-selected anchors, or future-aware trigger context, the backtest will look better than the real engine and the result will be junk.

## Bottom line
The project already has:
- a real market structure baseline
- a real S/R module direction
- a real watcher architecture direction

What remains is to:
1. finish the watcher cleanly
2. build the analyst layer cleanly
3. build the simulation layer honestly

That is the real path from “good chart logic” to “working engine we can backtest.”
