# Simulation → Guarded Pilot Go/No-Go Checklist

## Decision rule

Proceed to guarded pilot only if every **Go Gate** item is checked. Any unchecked **Go Gate** item is an automatic **No-Go**.

## Go Gate

- [ ] **Runtime compatibility is green**
  - Requirement: analysis + diagnostic UI paths run on target runtime (Python **3.11+** baseline).
  - Current status (2026-02-15): baseline policy updated to Python 3.11+; full integration sanity rerun on 3.11+ still required for green gate.
  - Evidence: `specs/08_testing_runbook.md`, `docs/INTEGRATION_SANITY_CHECK_2026-02-15.md`.

- [ ] **Integration sanity test suite is green**
  - Requirement: parser, card engine, simulation mode, and diagnostic UI tests all pass.
  - Current status (2026-02-15): parser/card pass; simulation/UI fail.
  - Evidence: `docs/INTEGRATION_SANITY_CHECK_2026-02-15.md`.

- [x] **Packaging/runbook path is reproducible**
  - Requirement: containerized startup path is defined and validates via compose config.
  - Current status (2026-02-15): **PASS** (`docker-compose.yml` present; `docker compose -f docker-compose.yml config` passes).
  - Evidence: `docs/DOCKER_COMPOSE_VALIDATION_2026-02-15.md`, `specs/08_testing_runbook.md`.

- [ ] **Baseline local quality gate passes**
  - Requirement: clean test run in project virtualenv.
  - Current status (2026-02-15): **PASS** (`./.venv/bin/pytest -q` → 44 passed).
  - Evidence: `docs/DOCKER_COMPOSE_VALIDATION_2026-02-15.md`.

- [ ] **HTF-anchor profile parity + adversarial gates are green**
  - Requirement: at least two anchor profiles (e.g., 1D-anchor and 1H-anchor) pass replay parity checks and two-pass adversarial validation gates.
  - Current status (2026-02-18): pending Tasks 14–17 (`tasks/14_...` to `tasks/17_...`).
  - Evidence target: `docs/AUTOMATED_TRADING_AGENT_ALIGNMENT_V1.md` + adversarial gate artifacts.

## Guarded Pilot Controls (must be true before live capital/risk)

- [ ] Pilot is explicitly in simulation/paper mode for first run window.
- [ ] Operator rollback path is documented (disable ingestion and stop processing quickly).
- [ ] Log capture and daily review cadence are defined for pilot period.
- [ ] Any runtime exceptions trigger immediate pilot pause pending review.

## Current Recommendation (2026-02-15)

**NO-GO** until:
1. Full integration sanity suite is rerun and green on Python 3.11+ baseline runtime.
2. Guarded pilot controls are explicitly checked and operator-owned.
