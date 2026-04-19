# Paper Soak Protocol V1 (Day-1 Baseline Locked)

Date locked: 2026-02-27 (ET)
Scope: paper-only soak for 1–2 weeks under fail-closed risk controls.

## Fixed tuning/evidence cadence

- Every soak day emits exactly one day artifact under `artifacts/paper_soak/daily/YYYY-MM-DD.json`.
- Checkpoints per day:
  - T0 start snapshot
  - T+60m startup stability snapshot
  - T+4h intraday stability snapshot
  - T+24h day-close summary + recommendation
- Tuning changes are only allowed once per day after day-close review and must record rationale.

## Kill criteria (immediate HOLD)

1. Mode mismatch (anything except `paper`).
2. Daily-loss breaker not first policy gate or non-fail-closed behavior.
3. Missing core telemetry for >10m.
4. Three consecutive hard failures in ingest/policy/execution cycle.
5. Any strategy->policy->execution boundary bypass evidence.

## Promotion criteria (soak progression only; no live enablement)

- 7+ consecutive soak days with no kill-criteria triggers.
- Complete checkpoint coverage every day.
- Non-escalating error rate trend over rolling 3-day window.
- Daily-loss breaker behavior remains stable and verified.
- Deterministic day artifacts available for audit/replay.

## Daily evidence append contract

- Source of truth log: `artifacts/paper_soak/SOAK_LOG.md`
- Day artifacts: `artifacts/paper_soak/daily/YYYY-MM-DD.json`
- Required fields:
  - mode
  - policy_gate_order
  - cycle_stats
  - feed_health
  - pipeline_counts
  - errors_by_class
  - circuit_breakers
  - status (`GO` or `HOLD`)
  - next_step

This protocol supersedes ad-hoc soak notes and makes daily comparison deterministic.