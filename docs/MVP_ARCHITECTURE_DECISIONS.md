# Phase 1 — MVP Architecture Decisions (proposal)

This doc translates the high-level plan into concrete MVP engineering decisions.

## What Phase 1 must do

- Run in Docker.
- Ingest Mobchart Liquidity Screener alerts from Telegram.
- Normalize into a local data store.
- Serve a web app that shows **symbol-centric cards** with cross-exchange confluences.
- Support workflow:
  - Inbox cards
  - Move card to **Active**
  - **Archive/Delete** card
  - Manually enter trade fields (SL/TP/RR/status)

## Proposed MVP topology

Use **docker compose** with two services + a shared data volume:

1) `ingestor`
- Python process
- Connects to Telegram (polling)
- Writes to SQLite

2) `web`
- Python web app
- Reads/writes SQLite
- Serves the “cards” UI

Rationale:
- Separates responsibilities cleanly.
- Easiest to run and debug.
- SQLite is safe/portable for Phase 1.

## Storage decision

### Recommendation: SQLite for MVP

Why:
- We need *mutable state* (card status, manual trade fields, archive) — SQLite handles this naturally.
- Still compatible with append-only principles: keep immutable raw/events tables + mutable card/trade tables.

We can still provide export endpoints to JSONL/CSV.

## Telegram ingestion decision

Two viable options:

A) **Bot token** + polling (recommended if Mobchart can post to a bot-accessible chat)
- simple deployment
- no phone/session

B) **Telethon user session**
- more complex operationally
- but works when bot access isn’t possible

Decision needed: which one matches your Mobchart setup.

## Web app stack decision

### Recommendation: Streamlit for the first online MVP

Why:
- Fastest way to deliver card UI + edit fields + filters.
- Works well inside Docker.

Upgrade path:
- Keep backend DB schema stable.
- Swap UI to Next.js/React later without redoing ingestion.

If you strongly prefer a traditional web app now:
- FastAPI backend + simple React frontend.

## Data model (minimal)

Immutable tables:
- `raw_telegram_messages`
- `signal_events`

Mutable tables:
- `cards` (one row per symbol)
- `confluences` (one row per venue/market/level instance)
- `trades` (one row per card when activated; contains manual trade fields)

## Card semantics

- A **Card** is keyed by `symbol`.
- It aggregates all known confluences for that symbol.
- “Confluence” is initially defined as: a liquidity screener level on a venue/market.

Later we can add confluences from other sources (orderbook, funding, volatility, etc.)

## Workflow

- New signal arrives → upsert card into `inbox` → append confluence.
- User clicks **Activate** → card moves to `active` and a trade row is created (or opened).
- User clicks **Archive/Delete** → card moves to `archived` (or hard delete if we insist).

Recommendation: archive (soft delete) for audit.
