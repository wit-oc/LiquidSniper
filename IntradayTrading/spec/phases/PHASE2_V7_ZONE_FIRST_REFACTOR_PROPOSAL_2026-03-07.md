# Phase 2 V7 Zone-First Refactor Proposal (2026-03-07)

Status: PROPOSED (pending control-thread approval)
Branch: `phase2-v7-zone-first-20260307`
Current fallback baseline: `PHASE2A_SR_WATCHER_V6_2_5_FOXIAN_EXCURSION_REVERSAL_MODEL.pine`

## 1) Why pivot now

Recent diagnostics show repeated evidence that obvious shelves can survive discovery but still fail downstream display gates in ways that are difficult to reason about with candle-first logic.

Observed pattern (v6.2.5 diagnostics):
- anchors accepted/kept in probe band
- probe-band clusters present pre/post finalize
- clusters failing primarily on width governance

Interpretation:
- the engine is still over-indexed on candle/anchor ranking then trying to infer zones,
- while strategy intent is zone-first (battle-area-first) with reaction evidence as support.

## 2) Architectural direction (reconciled)

Not a reset. A reframe:

- Keep Foxian excursion/reaction math as an evidence channel.
- Promote zone as first-class object.
- Make HTF structure seeds mandatory (from Phase 1 v3.3 logic).
- Move hard suppression later (zone selection/display stage), not early (pre-zone discovery).

### Primary unit shift
Old:
- score candles -> suppress anchors -> cluster anchors -> render

New:
- generate evidence events -> build provisional zones -> score zones -> select/render

## 3) Scope boundaries

In scope:
- V7 Pine architecture for zone-first map/watch context
- deterministic event and zone schema
- 1D-first execution slice then 4H integration
- explicit handoff contract for Python trading-bot parity

Out of scope for V7A:
- trigger entries (15m/5m trigger logic)
- execution/risk lifecycle
- optimization sweeps

## 4) V7 phased plan (proposed)

### V7A — Zone-first skeleton (1D)
Goal:
- establish event->zone pipeline with deterministic debug visibility.

Deliverables:
- `PHASE2A_SR_WATCHER_V7A_ZONE_FIRST.pine`
- event/zone objects + debug panel
- structural-vs-tradeable zone class split

Acceptance:
- major historical shelves appear as STRUCTURAL_ZONE even when not TRADEABLE.
- no pre-zone hard suppression deletes key evidence.

### V7B — HTF structure seed integration
Goal:
- seed zones from Phase-1 structure anchors/events as mandatory context.

Deliverables:
- structure adapter functions (from v3.3 logic)
- parity spot-check output for structure events (Pine-only)

Acceptance:
- v7 structure event tape aligns with v3.3 on BTC/ETH 1D sample windows.

### V7C — Base/battle-range geometry engine
Goal:
- make base/shelf detection primary geometry source.

Deliverables:
- base detector (overlap/compression/touch/breakout)
- base events integrated into provisional zone build

Acceptance:
- battle shelves appear without relying on single elite anchor candles.

### V7D — Zone scoring + lifecycle
Goal:
- score zones directly and state them consistently.

Deliverables:
- zone score components (structure/base/launch/flip/freshness)
- state model (`fresh/active/weakening/broken`)

Acceptance:
- state degradation tied to actual retests/invalidations, not proxy anchor density.

### V7E — Display/selection policy
Goal:
- deterministic chart output with meaningful prioritization.

Deliverables:
- tradeable vs structural rendering styles
- suppression/gap policy applied only at selection stage

Acceptance:
- structural zones remain visible (lighter) while tradeable shortlist remains concise.

### V7F — 4H confluence + watcher handoff
Goal:
- align 1D map with 4H context and produce watcher-ready outputs.

Deliverables:
- 1D/4H zone confluence scoring
- handoff payload contract for bot/watch engine

Acceptance:
- deterministic 1D+4H context payloads usable by downstream watcher pipeline.

## 5) Pine and bot mechanism alignment

### Pine role
- visual truth surface + deterministic feature/event tape
- operator validation and tactical diagnostics

### Bot/Python role
- state machine authority for asynchronous watch lifecycle and execution integration
- consumes V7 event/zone contract semantics

Contract principle:
- Pine validates semantics and visual intent first,
- Python ports same objects/rules for scalable universe monitoring.

## 6) Control-thread decision asks

1. Approve V7 pivot from anchor-first to zone-first architecture.
2. Approve phased sequence V7A->V7F under current Phase-2 umbrella.
3. Approve policy that v6.2.5 remains fallback baseline while V7A is built in parallel branch.
4. Approve Pine-first semantic lock before Python/bot parity port.

## 7) Immediate next step after approval

Start V7A implementation contract execution:
- event schema, zone schema, stage pipeline, debug rows, acceptance script.
