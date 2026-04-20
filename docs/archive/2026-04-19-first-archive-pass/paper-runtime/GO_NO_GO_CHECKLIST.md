# Simulation → Guarded Pilot Go/No-Go Checklist

## Decision rule

Proceed to guarded pilot only if every **Go Gate** item is checked. Any unchecked **Go Gate** item is an automatic **No-Go**.

**Fail-closed progression rule:** if any operator dependency stub is unresolved (Blofin credentials not provisioned, egress unverified, on-chain allowlist unresolved, or operator sign-off absent), progression is locked to paper/simulation only.

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

- [ ] **Canonical OHLCV feed baseline is green**
  - Requirement: canonical candle feed coverage/quality gates pass for required symbols/timeframes (`1m`,`5m`,`15m`,`1H`,`4H`,`1D`,`1W`) and strategy path is not trigger-feed dependent.
  - Current status (2026-02-18): pending Tasks 19–22 (`tasks/19_...` to `tasks/22_...`).
  - Evidence target: `docs/DATA_FEED_STRATEGY_V1.md` + feed health artifacts.

- [ ] **HTF-anchor profile parity + adversarial gates are green**
  - Requirement: at least two anchor profiles (e.g., 1D-anchor and 1H-anchor) pass replay parity checks and two-pass adversarial validation gates.
  - Current status (2026-02-18): pending Tasks 14–17 (`tasks/14_...` to `tasks/17_...`).
  - Evidence target: `docs/AUTOMATED_TRADING_AGENT_ALIGNMENT_V1.md` + adversarial gate artifacts.

- [ ] **Operator dependency stubs are verified or explicitly blocking progression**
  - Requirement: fail-closed defaults/stubs remain intact and unresolved dependencies are treated as hard blockers.
  - Verification checklist:
    - [ ] `.env.example` still enforces paper/sim defaults and disabled live paths.
    - [ ] `docs/OPERATOR_DEPENDENCY_STUBS_V1.md` stage gates are acknowledged by operator owner.
    - [ ] Blofin credential state is either absent/disabled (paper) or formally approved for next stage.
    - [ ] Egress posture is marked verified before any non-paper progression.
    - [ ] On-chain allowlist scope is explicitly approved before enabling any on-chain path.
    - [ ] Operator sign-off artifact exists for any stage transition.
  - Evidence: `LiquidSniper/.env.example`, `docs/OPERATOR_DEPENDENCY_STUBS_V1.md`, operator sign-off note/artifact.

## Guarded Pilot Controls (must be true before live capital/risk)

- [ ] Pilot is explicitly in simulation/paper mode for first run window.
- [ ] No progression beyond paper/simulation occurs while any operator dependency remains unresolved.
- [ ] Blofin API egress isolation is confirmed (static/dedicated egress preferred; no shared/rotating VPN requirement bypass).
- [ ] Main-account and bot-account network/API credentials are segregated (no egress reuse for main account sessions).
- [ ] Operator rollback path is documented (disable ingestion and stop processing quickly).
- [ ] Log capture and daily review cadence are defined for pilot period.
- [ ] Any runtime exceptions trigger immediate pilot pause pending review.

## Current Recommendation (2026-02-15)

**NO-GO** until:
1. Full integration sanity suite is rerun and green on Python 3.11+ baseline runtime.
2. Guarded pilot controls are explicitly checked and operator-owned.
