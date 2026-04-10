# Phase 2 — Watch Engine Certification Kickoff

Status: READY TO START  
Thread model: dedicated phase thread (`phase-2-watch-engine-certification`)  
Depends on: Phase 1 DONE (`PHASE1_HTF_STRUCTURE_DONE.md`)

## Goal
Certify watch-state logic using only Phase-1 structural outputs.

## Merge-forward architecture notes from the S/R certification lane
These are durable rules recovered from the active Phase 2 S/R thread and should be treated as part of the Phase 2 contract:

- Use a **zone-first** pipeline for S/R discovery and selection.
- Phase 1 v3.3 structure semantics remain mandatory seed evidence.
- Foxian excursion is supporting evidence, not sole discovery logic.
- Distinguish `STRUCTURAL_ZONE` from `TRADEABLE_ZONE`.
- Preserve separate review layers for:
  - `daily_major`
  - `operational_4h`
  - nearest/proximity views
- Preserve `origin_kind` separately from `current_role` so flips do not erase provenance.
- Daily coverage should be evaluated by macro envelope (`zone_low / zone_high / zone_mid`), not only narrowed render cores.
- 4H same-side competition should remain neighborhood-aware.
- `bootstrap_snapshot.json` is the authoritative operator review surface for point-in-time zone-map inspection.
- When selector output looks wrong, improve selector traces / demotion metadata before papering over the problem with generic score tweaks.

## Scope (from baseline plan)
Build and certify:
- `WATCH` / `INVALID` / `EXPIRED` states
- POI mapping + Fib value-zone context
- setup qualification + reaction-evidence gating (without trigger execution)
- no trigger-entry decisions yet (15m trigger stays in Phase 3)

## Required outputs
- `phase2_handoff.md`
- watch-state transition log schema
- point-in-time review snapshot(s) sufficient to inspect selected zones and rejected competitors
- auditable selector-trace / reason metadata for why a zone became tradeable, demoted, invalid, or expired

## Pass criteria
- Watch start/stop align with expected context windows
- 4H context guard prevents impulsive-opposition false watches
- Fib directional policy is enforced correctly (including short premium rule)
- Rejection/invalid reasons are auditable and coherent
- Point-in-time reconstruction is deterministic (no hindsight leakage)

## Proposed implementation slices
1. Watch state contract + schema (`watch_event`, `state_before`, `state_after`, `reason_code`)
2. POI mapper (phase-1 anchor-derived zones)
3. 4H context/stall guard module for setup qualification
4. Fib context calculator (direction-aware premium/discount + invalidation coupling)
5. Reaction-evidence scoring gate (stall/rejection/displacement classification)
6. State transition engine with explicit expiry policy
7. Deterministic replay artifacts for BTC/ETH 1D (point-in-time rebuild)

## Technical questions to resolve at Phase 2 start
1. **Watch-start gate:** BoS-only, CHoCH-only, or either with direction constraints?
2. **4H opposition filter:** what exact definition of “fresh impulsive opposition” blocks WATCH?
3. **Reaction evidence policy:** which minimum signals count (stall, rejection, displacement) before WATCH can arm?
4. **Expiry policy:** bars elapsed, opposite structure event, or hybrid?
5. **POI source priority:** when multiple POIs are valid, what is rank order?
6. **Fib anchor source:** latest structural anchor pair only, or fallback hierarchy when one side stale?
7. **Reason taxonomy lock:** canonical reason codes for INVALID/EXPIRED/no-watch.
8. **Point-in-time audit level:** per-bar event tape only, or full intermediate feature snapshots for replay parity?

## Initial defaults proposal (for approval)
- Cert universe/timeframe: BTC/ETH 1D primary + 4H context feed
- Watch starts on confirmed BoS in active structural direction
- Watch requires 4H non-impulsive-opposition context + minimum reaction evidence
- Watch invalidates on opposing CHoCH close
- Watch expires after fixed bar timeout OR invalidation (whichever first)

## Handoff to control thread
After pass, return with:
- one-page verdict,
- sample transition traces,
- unresolved edge cases (if any),
- recommendation for Phase 3 trigger certification kickoff.
