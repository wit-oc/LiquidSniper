# Phase 2 — Watch Engine Certification Kickoff

Status: READY TO START  
Thread model: dedicated phase thread (`phase-2-watch-engine-certification`)  
Depends on: Phase 1 DONE (`PHASE1_HTF_STRUCTURE_DONE.md`)

## Goal
Certify watch-state logic using only Phase-1 structural outputs.

## Scope (from baseline plan)
Build and certify:
- `WATCH` / `INVALID` / `EXPIRED` states
- POI mapping + Fib value-zone context
- no trigger-entry decisions yet

## Required outputs
- `phase2_handoff.md`
- watch-state transition log schema

## Pass criteria
- Watch start/stop align with expected context windows
- Fib directional policy is enforced correctly (including short premium rule)
- Rejection/invalid reasons are auditable and coherent

## Proposed implementation slices
1. Watch state contract + schema (`watch_event`, `state_before`, `state_after`, `reason_code`)
2. POI mapper (phase-1 anchor-derived zones)
3. Fib context calculator (direction-aware premium/discount + invalidation coupling)
4. State transition engine with explicit expiry policy
5. Deterministic replay artifacts for BTC/ETH 1D

## Technical questions to resolve at Phase 2 start
1. **Watch start trigger:** exact event gate?
   - On BoS only?
   - On CHoCH only?
   - On either with direction constraints?
2. **Expiry policy:** should watch expire by:
   - bars elapsed,
   - opposite structure event,
   - both?
3. **POI source priority:** when multiple POIs are valid, what is rank order?
4. **Fib anchor source:** use latest structural anchor pair only, or allow fallback when one side stale?
5. **Reason taxonomy lock:** list canonical reason codes for INVALID/EXPIRED and no-watch.
6. **Cross-timeframe policy:** stay single timeframe for phase cert (1D), or ingest HTF/LTF blend now?

## Initial defaults proposal (for approval)
- Cert timeframe: 1D only (BTC/ETH)
- Watch starts on confirmed BoS in active structural direction
- Watch invalidates on opposing CHoCH close
- Watch expires after fixed bar timeout (configurable), whichever comes first with invalidation

## Handoff to control thread
After pass, return with:
- one-page verdict,
- sample transition traces,
- unresolved edge cases (if any),
- recommendation for Phase 3 trigger certification kickoff.
