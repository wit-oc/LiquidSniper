# Program Baseline v2 — Intraday Revisit

Status: ACTIVE BASELINE  
Owner: Redact + Wit

This file is the canonical Phase-0/Phase-1 baseline reference for the intraday program.

## Baseline intent
- Keep a **control-thread-first** operating model.
- Execute one phase at a time in dedicated phase threads.
- Enforce phase boundaries (no cross-phase logic drift).
- Favor deterministic behavior and replay parity before promotion.

## Canonical source docs
- Phase thread conventions:
  - `spec/phases/THREAD_CONVENTION.md`
- Start-to-finish phase sequence:
  - `spec/phases/PLAN_START_TO_FINISH.md`
- Phase handoff template:
  - `spec/templates/PHASE_HANDOFF_TEMPLATE.md`
- Phase gate checklist:
  - `spec/checklists/PHASE_GATE_CHECKLIST.md`
- Wave/structure contract (Phase 0 draft baseline):
  - `spec/phases/PHASE0_WAVE_ENGINE_SPEC.md`
- Phase 1 market structure module spec:
  - `spec/phases/PHASE1_MARKET_STRUCTURE_MODULE_SPEC_V1.md`
- Phase 2A.1 S/R module spec:
  - `spec/phases/PHASE2A1_SR_MODULE_SPEC_V1.md`
- Phase 2A.2 Fib context spec:
  - `spec/phases/PHASE2A2_FIB_CONTEXT_SPEC_V1.md`
- Phase 2A.3 Dynamic levels spec:
  - `spec/phases/PHASE2A3_DYNAMIC_LEVELS_SPEC_V1.md`
- Phase 2A.4 Watch gating spec:
  - `spec/phases/PHASE2A4_WATCH_GATING_SPEC_V1.md`
- MTF strategy architecture (scaling reference):
  - `spec/strategy/MTF_STRATEGY_ARCHITECTURE_V1.md`
- Working roadmap to a backtestable engine:
  - `spec/strategy/BACKTESTABLE_ENGINE_ROADMAP_V1.md`

## Locked process rules
1. Control thread approves transitions; phase threads carry diagnostics.
2. One active phase thread at a time.
3. PASS / CONDITIONAL PASS required before moving to next phase.
4. If FAIL, smallest-fix loop in same phase.
5. Deterministic rerun command + artifact required for each handoff.

## Current phase context
- Phase 0 baseline: complete (spec/process baseline locked).
- Phase 1 HTF Structure/Bias: complete and certified (`v3.3` baseline).
- Phase 2 Watch Engine: in flight (dedicated thread + kickoff pack).
- As of 2026-04-09, Phase 2A.1 S/R has a closeout commit/PR path and appears implementation-complete enough to merge, but broader watcher certification still expects final human review, one broader regression basket, and an explicit lifecycle audit.

## Why this file exists
Earlier references pointed to `program_baseline_v2.md`; this file now serves as the explicit baseline entrypoint and index for the phase docs above.
