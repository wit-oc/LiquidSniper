# Task 15 — Strategy score engine alignment (playbook -> decision payload)

## Goal

Align lecture-derived strategy scoring to deterministic LiquidSniper decision objects without introducing discretionary runtime behavior.

## Deliverables

- Canonical score payload fields:
  - `score_total`
  - bucket breakdown (`regime`, `structure`, `location`, `trigger`, `execution_geometry`)
  - `penalties[]`
- Mapping spec from runbook/playbook logic -> current confluence decisions (`watch_only`, `publish_candidate`, `high_priority`, `reject`).
- Deterministic reason-code table for pass/fail transitions.

## Acceptance criteria

- Score payload is reproducible from identical inputs.
- Decision reasons are machine-readable and replay-safe.
- Existing runbook confluence tests remain valid or are updated with explicit migration notes.
