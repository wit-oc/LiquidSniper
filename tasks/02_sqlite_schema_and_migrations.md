# Task 02 — SQLite schema + migrations

## Goal

Implement the SQLite schema from Spec 02 with migrations.

## Deliverables

- `liquidsniper/core/db.py`:
  - connect helper
  - WAL mode
  - migration runner
- `liquidsniper/core/migrations/` SQL files
- Unit tests:
  - migrations apply cleanly
  - tables exist
  - unique constraints behave as expected

## Acceptance criteria

- Fresh DB can be created and migrated automatically
- Second run is idempotent
