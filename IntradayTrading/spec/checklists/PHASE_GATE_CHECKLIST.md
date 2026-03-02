# Phase Gate Checklist (Control Thread)

Use this checklist before approving phase transition.

## Global gates (every phase)
- [ ] Scope stayed inside phase boundary.
- [ ] Handoff file completed from template.
- [ ] Deterministic rerun command provided.
- [ ] No unresolved blocker hidden as pass.
- [ ] Knob gating/guardrails updated if needed.

## Phase 1 — HTF Bias Certification
- [ ] Persistent bullish/bearish regime implemented.
- [ ] CHoCH candidate + BoS confirmation flip implemented.
- [ ] No neutral fallback used for active trade direction.
- [ ] Parity check artifacts present.

## Phase 2 — Watch Engine (split allowed)
- [ ] Watch start conditions explicit.
- [ ] Watch invalid/expired conditions explicit.
- [ ] Fib directional policy enforced correctly.
- [ ] Watch telemetry reasons audited.

## Phase 3 — Trigger Engine (split allowed)
- [ ] Trigger requires certified watch context.
- [ ] Candle confirmation scoring is discriminative (not saturated).
- [ ] Retest ordinal weighting validated.
- [ ] Trigger miss behavior documented (no chase).

## Phase 4 — Risk/Execution
- [ ] Risk tiers map to confidence policy.
- [ ] TP/BE/stop lifecycle deterministic.
- [ ] Breaker behavior verified.

## Phase 5 — Tuning (config-only)
- [ ] Logic hash frozen.
- [ ] One knob family at a time.
- [ ] Dead-knob detection run and respected.

## Phase 6 — Promotion/Parity
- [ ] Pine/Python parity report complete.
- [ ] Promotion memo includes failure modes.
- [ ] Operator runbook updated.
