# Simulation → Guarded Pilot Go/No-Go Checklist

## Decision rule

Proceed to guarded pilot only if every **Go Gate** item is checked. Any unchecked **Go Gate** item is an automatic **No-Go**.

## Go Gate

- [ ] **Runtime compatibility is green**
  - Requirement: analysis + diagnostic UI paths run on target Python runtime.
  - Current status (2026-02-15): **FAIL** on Python 3.9 (`enum.StrEnum` import error).
  - Evidence: `docs/INTEGRATION_SANITY_CHECK_2026-02-15.md`.

- [ ] **Integration sanity test suite is green**
  - Requirement: parser, card engine, simulation mode, and diagnostic UI tests all pass.
  - Current status (2026-02-15): parser/card pass; simulation/UI fail.
  - Evidence: `docs/INTEGRATION_SANITY_CHECK_2026-02-15.md`.

- [ ] **Packaging/runbook path is reproducible**
  - Requirement: containerized startup path is defined and validates via compose config.
  - Current status (2026-02-15): **FAIL** (`docker-compose.yml` missing).
  - Evidence: `docs/DOCKER_COMPOSE_VALIDATION_2026-02-15.md`, `specs/08_testing_runbook.md`.

- [ ] **Baseline local quality gate passes**
  - Requirement: clean test run in project virtualenv.
  - Current status (2026-02-15): **PASS** (`./.venv/bin/pytest -q` → 44 passed).
  - Evidence: `docs/DOCKER_COMPOSE_VALIDATION_2026-02-15.md`.

## Guarded Pilot Controls (must be true before live capital/risk)

- [ ] Pilot is explicitly in simulation/paper mode for first run window.
- [ ] Operator rollback path is documented (disable ingestion and stop processing quickly).
- [ ] Log capture and daily review cadence are defined for pilot period.
- [ ] Any runtime exceptions trigger immediate pilot pause pending review.

## Current Recommendation (2026-02-15)

**NO-GO** until:
1. Python 3.9 compatibility issue (`StrEnum`) is resolved or runtime baseline is raised and documented.
2. `docker-compose.yml` (or replacement container orchestration artifact) exists and passes `docker compose ... config` validation.
3. Full integration sanity suite is green on target runtime.
