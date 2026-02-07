# Spec 08 — Testing / Runbook

## Goal

Document how to run, verify, and troubleshoot Phase 1.

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

## Acceptance criteria

- A new contributor can follow this to get a working system.
