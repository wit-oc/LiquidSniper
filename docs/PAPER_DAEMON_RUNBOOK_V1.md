# Paper Daemon Runbook V1

## Scope
Paper-only daemonized operation for LiquidSniper using `docker-compose.paper.yml`.

## Prereqs
- Docker Desktop / docker engine running
- `cp .env.paper.example .env.paper`
- Keep `LIQUIDSNIPER_MODE=paper`
- Set profile + symbols explicitly for MVP attempts:
  - `LIQUIDSNIPER_PROFILE_MODE=intraday_only`
  - `LIQUIDSNIPER_PROFILE_ID=I` (`S|I|C`)
  - `LIQUIDSNIPER_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,SUIUSDT`
- Gate policy/tuning knobs (profile-parameterized defaults; override only with evidence):
  - `LIQUIDSNIPER_MAX_DAILY_LOSS_USD=500` (**first hard-stop check**; trading halts when daily loss breaches this cap)
  - `LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE=true`
  - `LIQUIDSNIPER_HTF_CHOP_MAX=50`
  - `LIQUIDSNIPER_MIN_SECONDARY_HITS=2`
  - `LIQUIDSNIPER_COOLDOWN_SECONDS=900`
  - `LIQUIDSNIPER_DAILY_MAX_TRADES=4`
  - `LIQUIDSNIPER_MAX_ACTIVE_RISK_POSITIONS=2`
- Ensure artifact root points to persistent volume path:
  - `LS_ARTIFACT_ROOT=/var/lib/liquidsniper/artifacts`
- Ensure DB path is writable for SR Engine V2 zone persistence:
  - `LIQUIDSNIPER_DB_PATH=/var/lib/liquidsniper/data/liquidsniper.sqlite`

## Startup
- (After code changes) rebuild images:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper build paper-runner scorecard-worker`
- Start long-running paper runner:
  - `make paper-daemon-up`
- Run scorecard aggregation once (daily/weekly artifacts):
  - `make paper-scorecard-once`

## Stop
- `make paper-daemon-down`

## State maintenance
- Backup current paper artifacts/logs before cleanup:
  - `make paper-backup-state`
- Reset paper run state (runs/daily/weekly/throttle/logs):
  - `make paper-reset-state`
  - then bring services back up via Startup steps

## Health checks
- Container status:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper ps`
- Runner health file (includes profile/symbols + attempted/executed/blocked):
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner cat /var/lib/liquidsniper/logs/paper_runner.health.json`
- Persistent throttle state (idempotency/cooldown/daily-cap/BE-aware active-risk cap):
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner cat /var/lib/liquidsniper/artifacts/paper_mvp/state/execution_throttle_state.json`
- Scorecard worker health file:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper run --rm scorecard-worker cat /var/lib/liquidsniper/logs/scorecard_worker.health.json`

## Daily review
- Per-run artifacts:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner ls -1 /var/lib/liquidsniper/artifacts/paper_mvp/runs | tail`
- Gate trace inspection (per run):
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner sh -lc 'f=$(ls -1 /var/lib/liquidsniper/artifacts/paper_mvp/runs | tail -n 1); cat /var/lib/liquidsniper/artifacts/paper_mvp/runs/$f'`
  - verify `gate_checks`, `gate_trail`, `bias_snapshot`, `sr_context`, `position_state_before/after`, `decision_reason_codes`, `policy_snapshot`, and `candle_timestamp` are present
  - verify `sr_context` includes `sr_anchor_tf`, `sr_eligible_tfs`, nearest support/resistance zone payloads (`zone_id`, `tf`, `bounds`, `first_retest_status`) and SR gate reason codes
- Daily scorecard:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner cat /var/lib/liquidsniper/artifacts/paper_mvp/daily/$(date -u +%F).json`
- Weekly rollup:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner cat /var/lib/liquidsniper/artifacts/paper_mvp/weekly/$(date -u +%G-W%V).json`

## Debug UI/API (optional profile)
- Enable debug service only when needed:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper --profile debug-ui up -d paper-debug-ui`
- Open UI locally:
  - `http://127.0.0.1:${LIQUIDSNIPER_DEBUG_PORT:-8787}/ui`
- API base:
  - `http://127.0.0.1:${LIQUIDSNIPER_DEBUG_PORT:-8787}/api/v1/debug`
- Snapshot export endpoint:
  - `GET /api/v1/debug/snapshot?strategy=<scalp|intraday|swing>&run_id=<id>&test_id=<id>&event_hours=24`
- List pagination params (`orders|positions|events`):
  - `page=<n>` (default `1`)
  - `page_size=<n>` (default `200`, max `1000`)
- Event retention window:
  - default from `LIQUIDSNIPER_EVENT_RETENTION_HOURS` (default `24`)
  - override per request with `event_hours=<n>`
- Auth guard (configure one):
  - Bearer token: set `LIQUIDSNIPER_DEBUG_TOKEN`, then send `Authorization: Bearer <token>`
  - Basic auth: set `LIQUIDSNIPER_DEBUG_USER` + `LIQUIDSNIPER_DEBUG_PASS`

## Operator validation checklist (debug v1)
- [ ] `paper-debug-ui` starts only when `--profile debug-ui` is passed.
- [ ] Service bind/port matches configured exposure (`LIQUIDSNIPER_DEBUG_BIND` + `LIQUIDSNIPER_DEBUG_PORT`).
- [ ] `POST /api/v1/debug/orders` returns `405 READ_ONLY_MODE`.
- [ ] `GET /api/v1/debug/strategies` returns strategy summary cards.
- [ ] `GET /api/v1/debug/orders` and `/positions` render data in UI tables.
- [ ] `GET /api/v1/debug/events` shows gate/reject/feed reason codes.
- [ ] UI snapshot export downloads JSON successfully.

## Troubleshooting
- If `paper-runner` unhealthy: check logs
  - `make paper-daemon-logs`
- If scorecards are stale: rerun worker
  - `make paper-scorecard-once`
- If debug UI returns `401 UNAUTHORIZED`, verify token/basic-auth env values in `.env.paper` and request headers.
- If debug UI is blank, verify artifacts exist:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper exec -T paper-runner ls -1 /var/lib/liquidsniper/artifacts/paper_mvp/runs | tail`
- If bankroll-related blocks appear (`BANKROLL_EXHAUSTED`), reduce risk sizing or increase `LIQUIDSNIPER_PAPER_BANKROLL_USD` in `.env.paper` for paper simulations.
- If gate rejects spike, inspect `decision_reason_codes` and tune one knob at a time:
  - `RISK_DAILY_LOSS_CAP_BREACH` -> **hard stop triggered first**; halt remains until next trading day (or cap reset) to avoid trading into adverse regime
  - `CANDLE_NOT_CLOSED` -> verify scheduler timing / candle-close source
  - `HTF_CHOP_BLOCKED` -> profile too strict for regime; reassess `LIQUIDSNIPER_HTF_CHOP_MAX`
  - `CONFLUENCE_TOO_WEAK` -> confluence matcher drift or `LIQUIDSNIPER_MIN_SECONDARY_HITS` too high
  - `IDEMPOTENCY_DUPLICATE` -> duplicate cycle inputs/candle timestamps
  - `COOLDOWN_ACTIVE` / `DAILY_CAP_REACHED` / `ACTIVE_RISK_CAP_REACHED` -> expected overtrading protections
  - `BIAS_NOT_PERMITTED` -> HTF bias engine returned neutral/opposite; inspect BoS/CHoCH + profile
- Smoke validation (daemon remains down):
  - `./.venv/bin/pytest -q tests/test_paper_daemon_smoke.py`
  - pass condition: execution-rate bounded (not zero, not hyperactive) with blocked attempts observed
- Persistence check after restart:
  - `docker compose -f docker-compose.paper.yml --env-file .env.paper restart paper-runner`
  - verify artifact files still exist under `/var/lib/liquidsniper/artifacts/paper_mvp/`
