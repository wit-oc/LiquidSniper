# Paper Multi-Strategy + Global Drawdown Circuit Breaker Delivery Plan (v1)

## Scope
This plan delivers two connected capabilities:
1. Strategy-separated paper accounts (`scalp`, `intraday`, `swing`) with paper-only parallel orchestration.
2. Global daily max-drawdown circuit breaker enforced across **all trading modes**.

## Hard invariants
- Parallel multi-strategy orchestration is **paper-mode only**.
- Non-paper modes always run in **single-mode only**.
- Daily drawdown circuit breaker is **mandatory for all modes** (paper + non-paper).
- On missing/corrupt risk state, fail closed for new entries.

## Phase map
- **Phase 0 (P0 Safety Gate):** mode boundary + global drawdown circuit breaker + heavy tests
- **Phase 1:** strategy-account schema/contracts/migration
- **Phase 2:** paper-only parallel orchestrator + per-strategy isolation
- **Phase 3:** observability/debug UX + rollout controls
- **Phase 4:** soak/regression evidence + PR readiness

---

## Task breakdown (ready for initiative runner)

### Epic A — Safety Infrastructure (P0)

1. **A1 / P0**: Mode boundary enforcement (startup + runtime + API guards)
   - Acceptance:
     - parallel flags rejected unless `LIQUIDSNIPER_MODE=paper`
     - non-paper execution path cannot fan-out to strategy lanes
     - guard failures emit deterministic reason code

2. **A2 / P0**: Global daily drawdown circuit-breaker state model
   - Acceptance:
     - configurable threshold (% and absolute) with deterministic precedence
     - tracks realized + unrealized drawdown at day scope
     - state persists across process restarts

3. **A3 / P0**: Circuit-breaker enforcement hook in execution boundary
   - Acceptance:
     - hard-stop new entries when tripped
     - optional exits-only policy path documented and tested
     - fail-closed when risk state unreadable

4. **A4 / P0**: Circuit-breaker test suite (critical)
   - Acceptance:
     - threshold boundary tests (under/at/over)
     - realized-only/unrealized-only/combined scenarios
     - concurrency + restart + corrupt-state tests
     - explicit regression test for previous overtrading pattern with breaker engaged

### Epic B — Strategy Account Isolation + Paper Parallelism

5. **B1 / P1**: Strategy-account schema + migration
   - Acceptance:
     - per-strategy account/config tables with uniqueness constraints
     - backfill maps legacy account to `intraday`
     - scalp/swing default disabled until explicit enable

6. **B2 / P1**: Strategy routing contract enforcement
   - Acceptance:
     - paper order intents require strategy (or temporary controlled fallback)
     - all persisted paper artifacts include strategy id
     - deterministic reject reasons for invalid strategy

7. **B3 / P1**: Paper-only parallel orchestrator
   - Acceptance:
     - fan-out by enabled strategy lanes in paper mode only
     - per-lane throttle/idempotency keys isolated
     - no shared-state race leakage under concurrent runs

8. **B4 / P1**: Per-strategy risk budgets + lane-level drawdown guards
   - Acceptance:
     - strategy-specific caps enforced before execution
     - lane breaker + global breaker arbitration defined
     - events include precise reject source (`lane_limit`, `global_drawdown_trip`, etc.)

### Epic C — Observability, Rollout, and Evidence

9. **C1 / P1**: Extend debug APIs/UI for strategy + breaker visibility
   - Acceptance:
     - strategy cards include breaker/risk status
     - event log exposes breaker transitions and reject reasons
     - snapshot export includes breaker and mode guard state

10. **C2 / P1**: Feature flags + kill switches
    - Acceptance:
      - independent toggles for strategy accounts and paper parallelism
      - emergency stop switch blocks new entries immediately
      - runbook includes rollback drill

11. **C3 / P0**: Soak + regression matrix
    - Acceptance:
      - test matrix: paper single-lane, paper multi-lane, non-paper single-mode
      - confirms no parallel path outside paper mode
      - confirms breaker behavior under sustained/high-frequency conditions

12. **C4 / P1**: PR/evidence pack
    - Acceptance:
      - changelog, migration notes, risk notes, test report artifacts
      - final go/no-go checklist complete

---

## Recommended sequential order
A1 -> A2 -> A3 -> A4 -> B1 -> B2 -> B3 -> B4 -> C1 -> C2 -> C3 -> C4

## Definition of done
- All P0 tasks complete and passing in CI-equivalent local run.
- No code path allows parallel orchestration outside paper mode.
- Drawdown breaker blocks entries consistently in all modes with deterministic telemetry.
- PR includes migration + rollback instructions and evidence artifacts.
