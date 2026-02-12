# Task 10 — "Would alert" simulation mode (no channel send)

## Goal

Implement simulation-only decision output so we can calibrate noise before live channel publishing.

## Deliverables

- Config flags:
  - `ALERTS_ENABLED=false` (default)
  - `ALERTS_SIMULATION=true` (default)
- Pipeline writes decision outcomes to DB but does not post to Discord.
- Metrics view helpers:
  - candidates/day
  - high-priority/day
  - symbol concentration

## Acceptance criteria

- Decisions are persisted and queryable.
- No outbound channel sends occur when disabled.
