# Task 18 — Execution-core packaging boundary decision

## Goal

Make an explicit, evidence-based decision on whether to keep automated trading logic integrated in LiquidSniper or split into a separate execution-core service.

## Deliverables

- Decision record with criteria:
  - security boundary needs (keys/signers),
  - release cadence divergence,
  - compliance/audit domain separation,
  - replay reliability/dependency complexity.
- Recommended target architecture for current phase.
- Fork triggers and rollback plan if architecture is split later.

## Acceptance criteria

- Decision is documented with concrete yes/no rationale and trigger thresholds.
- Result is reflected in task board and docs.
- Both Blofin and on-chain path implications are addressed.
