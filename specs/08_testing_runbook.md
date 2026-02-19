# Spec 08 — Testing / Runbook

## Goal

Document how to run, verify, and troubleshoot Phase 1.

## Runtime baseline (required)

- Python **3.11+ only** for local/venv workflows.
- Docker/Compose path is the canonical simulation rollout path.
- Any references to Python 3.9/3.10 are legacy and non-supported for Phase 1 rollout.

## Setup steps

1) Copy `.env.example` → `.env` and fill:
- TELEGRAM_API_ID
- TELEGRAM_API_HASH
- TELEGRAM_PHONE
- MOBCHART_BOT_USERNAME

2) First-run login
- `docker compose run --rm ingestor`
- enter code / 2FA as prompted

3) Start services
- `docker compose up`

## Verification

- Ingestor logs show:
  - connected
  - listening
  - message received
- DB contains rows:
  - `raw_telegram_messages` increasing
  - `signal_events` increasing
  - `cards` created

- UI:
  - Inbox shows new symbols
  - Activate moves to Active
  - Trade fields persist after refresh

## Troubleshooting

- No messages:
  - verify bot username
  - verify Telethon session exists
  - verify Mobchart is sending

- DB locked:
  - ensure both services use WAL mode

## Validation snapshot (2026-02-15)

- Docker engine detected: `docker --version` passed (`29.1.5`).
- Docker Compose detected: `docker compose version` passed (`v5.0.1`).
- Compose file check now passes: `docker compose -f docker-compose.yml config` renders `liquidsniper-ingestor` + `liquidsniper-web` with shared `liquidsniper_data` volume.
- Local validation gate currently passing (Python 3.11+ baseline): `./.venv/bin/pytest -q` → `44 passed`.
- Simulation rollout decision gate tracked in `docs/GO_NO_GO_CHECKLIST.md`.
- Detailed command/output log: `docs/DOCKER_COMPOSE_VALIDATION_2026-02-15.md`.

## Acceptance criteria

- A new contributor can follow this to get a working system.
