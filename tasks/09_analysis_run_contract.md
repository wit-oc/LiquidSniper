# Task 09 — Analysis run contract + pipeline skeleton

## Goal

Add backend data contracts for score computation and decision tracking.

## Deliverables

- New DB tables + migration(s):
  - `analysis_runs`
  - `candidate_decisions`
  - `screenshot_artifacts`
- Core module skeleton for staged scoring:
  - zone priority
  - context score
  - final score
- Decision enum:
  - `publish_candidate`
  - `watch_only`
  - `reject`

## Acceptance criteria

- End-to-end insertion of one analysis run + decision + zero/one artifact rows
- Unit tests for migration + basic write/read flow
