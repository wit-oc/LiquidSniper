# Spec 03 — Telegram Ingestion (Telethon)

## Goal

Implement ingestion using a Telegram **user session** via Telethon.

## Inputs

- Messages from Mobchart bot chat (DM) and/or group (if later supported)

## Configuration

Environment variables:
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_PHONE`
- `TELEGRAM_SESSION_PATH` (default `/data/telethon.session`)
- `MOBCHART_BOT_USERNAME` (e.g. `mobchart_bot`)
- `DB_PATH` (default `/data/liquidsniper.sqlite`)

## First-run login

- If no session exists, Telethon prompts for login code.
- This must be supported in Docker via:
  - running the ingestor interactively once (`docker compose run ingestor`)
  - or a documented host-run bootstrap step

## Ingest behavior

- Subscribe to `NewMessage` events.
- Filter by sender username == `MOBCHART_BOT_USERNAME` (or chat id once known).
- On message:
  1) write a `raw_telegram_messages` row
  2) pass message text to parser (Spec 04)
  3) write `signal_events`
  4) update cards/confluences (Spec 05)

## Reliability

- On startup, optionally backfill the last N messages (configurable) to avoid missing alerts during downtime.
- Dedupe using `(telegram_chat_id, telegram_message_id)` for raw.
- For events: `(raw_message_id, line_index)` unique.

## Acceptance criteria

- After login, ingestor runs headless and persists session.
- New Mobchart alerts appear in DB within 1–2 seconds.
