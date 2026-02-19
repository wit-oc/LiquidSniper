# Task 17 — Two-pass adversarial validation harness

## Goal

Codify two adversarial passes as deterministic gates before any promotion beyond simulation/paper influence.

## Deliverables

- Pass 1 (strategy/microstructure):
  - anchor-profile drift checks,
  - cost-model tail error checks,
  - trigger inflation/overfit checks.
- Pass 2 (systems/governance):
  - policy-version pinning checks,
  - non-bypass contract checks,
  - replay parity and reason-code audit checks.
- Fail/hold actions and reason codes for each failed gate.

## Acceptance criteria

- Both passes produce machine-readable pass/fail artifacts.
- Any failed adversarial gate blocks promotion.
- Gate outputs are linked to go/no-go checklist inputs.
