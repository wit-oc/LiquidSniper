# Paper Daemon Runbook V1

## Scope
Paper-only daemonized operation for LiquidSniper using `docker-compose.paper.yml`.

## Prereqs
- Docker Desktop / docker engine running
- `cp .env.paper.example .env.paper`
- Keep `LIQUIDSNIPER_MODE=paper`
- Set profile + symbols explicitly for MVP attempts:
  - `LIQUIDSNIPER_PROFILE_MODE=intraday_only`
  - `LIQUIDSNIPER_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,SUIUSDT`
- Ensure artifact root points to persistent volume path:
  - `LS_ARTIFACT_ROOT=/var/lib/liquidsniper/artifacts`

## Startup
- (After code changes) rebuild images:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper build paper-runner scorecard-worker`
- Start long-running paper runner:
  - `make paper-daemon-up`
- Run scorecard aggregation once (daily/weekly artifacts):
  - `make paper-scorecard-once`

## Stop
- `make paper-daemon-down`

## Health checks
- Container status:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper ps`
- Runner health file (includes profile/symbols + attempted/executed/blocked):
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner cat /var/lib/liquidsniper/logs/paper_runner.health.json`
- Scorecard worker health file:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper run --rm scorecard-worker cat /var/lib/liquidsniper/logs/scorecard_worker.health.json`

## Daily review
- Per-run artifacts:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner ls -1 /var/lib/liquidsniper/artifacts/paper_mvp/runs | tail`
- Daily scorecard:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner cat /var/lib/liquidsniper/artifacts/paper_mvp/daily/$(date -u +%F).json`
- Weekly rollup:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner cat /var/lib/liquidsniper/artifacts/paper_mvp/weekly/$(date -u +%G-W%V).json`

## Troubleshooting
- If `paper-runner` unhealthy: check logs
  - `make paper-daemon-logs`
- If scorecards are stale: rerun worker
  - `make paper-scorecard-once`
- If bankroll-related blocks appear (`BANKROLL_EXHAUSTED`), reduce risk sizing or increase `LIQUIDSNIPER_PAPER_BANKROLL_USD` in `.env.paper` for paper simulations.
- Persistence check after restart:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper restart paper-runner`
  - verify artifact files still exist under `/var/lib/liquidsniper/artifacts/paper_mvp/`
