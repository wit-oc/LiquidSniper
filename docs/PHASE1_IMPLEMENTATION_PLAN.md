# Phase 1 Implementation Plan (top-down)

This is the concrete build plan to go from “docs” to “running platform”.

## Step 1 — Lock decisions (1 hour)

1) Telegram ingestion method
- bot token polling OR telethon user session

2) Storage
- SQLite (recommended)

3) UI stack
- Streamlit (recommended for MVP)

## Step 2 — Define DB schema (half day)

Create `apps/core/db.py` with migrations (simple versioned SQL files).

Tables:
- `raw_telegram_messages`
- `signal_events`
- `cards`
- `confluences`
- `trades`

## Step 3 — Build ingestor (1–2 days)

- Connect to Telegram
- Store raw messages
- Parse each line (batch aware)
- Insert signal events
- Upsert card + insert confluence

## Step 4 — Build web UI (1–2 days)

Streamlit pages:
- Inbox
- Card detail
- Active trades

Actions:
- Activate
- Archive
- Edit trade fields

## Step 5 — Docker (half day)

- `docker-compose.yml` with `ingestor` + `web`
- Shared volume mounted to `/data/liquidsniper.sqlite`

## Step 6 — “Definition of Done” for Phase 1

- `docker compose up` works on a clean machine
- Ingestor persists events across restarts
- UI shows cards and confluences
- Can activate/archive and edit manual trade fields
- Export CSV/JSONL optional
