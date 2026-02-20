# Paper Daemon Architecture V1

## Goal
Run LiquidSniper paper trading as a daemonized Docker deployment with persistent state and bankroll accounting.

## Container Topology (MVP)

1. `paper-runner` (long-running)
   - pulls/ingests data
   - runs scoring/policy cycle
   - executes paper-only path
   - writes run artifacts + DB state

2. `scorecard-worker` (scheduled)
   - builds daily and weekly scorecards
   - writes aggregate artifacts

## Persistence Layout

Mounted volume root: `/var/lib/liquidsniper`

- `/var/lib/liquidsniper/db/liquidsniper.sqlite`
- `/var/lib/liquidsniper/artifacts/paper_mvp/runs/*.json`
- `/var/lib/liquidsniper/artifacts/paper_mvp/daily/*.json`
- `/var/lib/liquidsniper/artifacts/paper_mvp/weekly/*.json`
- `/var/lib/liquidsniper/logs/*.log`

## Environment Contract

- `LIQUIDSNIPER_DB_PATH`
- `LIQUIDSNIPER_ARTIFACT_ROOT`
- `LIQUIDSNIPER_MODE=paper`
- `LIQUIDSNIPER_PAPER_BANKROLL_USD` (starting equity)
- `LIQUIDSNIPER_MAX_DAILY_LOSS_USD`
- `LIQUIDSNIPER_MAX_CLUSTER_LOSS_USD`
- `LIQUIDSNIPER_LOOP_SECONDS`

## Safety Invariants

- Runtime must hard-block any non-paper mode.
- Bankroll accounting must update on each lifecycle transition.
- Artifacts must include bankroll snapshot fields.
- Restart must preserve DB and bankroll state.

## Failure Modes

- Data/feed degraded -> no new paper entries; emit health reason codes.
- Bankroll exhausted -> reject with bankroll reason code.
- Persistence unavailable -> fail closed (no execution).

## Promotion Gate

This architecture is paper-only. Any live-mode enablement requires explicit operator approval and separate change control.
