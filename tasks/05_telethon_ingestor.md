# Task 05 — Telethon ingestor (Telegram → DB)

## Goal

Implement Telethon ingestion per Spec 03.

## Deliverables

- `liquidsniper/ingestor/main.py` runnable as `python -m liquidsniper.ingestor`
- Writes `raw_telegram_messages`
- Calls parser → writes `signal_events`
- Calls card engine → updates `cards/confluences`
- Dedupe:
  - raw by `(chat_id,message_id)`
  - events by `(raw_message_id,line_index)`
- Optional backfill last N messages
- Tests:
  - unit tests for message → DB write using a mocked message object
  - integration test that runs ingestor loop function against fixtures (no network)

## Acceptance criteria

- First-run login path documented (no code secrets)
- When provided fixture messages, DB is populated correctly
