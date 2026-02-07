# Spec 01 — Phase 1 Architecture

## Goal

Define the Phase 1 runtime architecture: processes, boundaries, and interfaces.

## Decisions

- Ingestion method: **Telethon user session** (Telegram user client)
- Storage: **SQLite**
- Web UI: **Streamlit** (Phase 1)

## Services

### 1) `ingestor`

Responsibilities:
- Connect to Telegram as a user session.
- Subscribe to messages from Mobchart bot chat.
- Persist raw messages.
- Parse messages into `signal_events`.
- Update derived state: `cards`, `confluences`, `trades`.

### 2) `web`

Responsibilities:
- Serve Streamlit UI.
- Query card/confluence/trade data.
- Provide user actions (activate/archive/edit trade fields).

## Boundaries

- Ingestor and web must **share only the DB file**.
- No service holds trading API keys or connects to exchanges.
- Parser treats inbound text as untrusted.

## Deployment

- `docker-compose.yml` with:
  - `liquidsniper-ingestor`
  - `liquidsniper-web`
- **Shared persistent volume** mounted at `/data` containing:
  - `liquidsniper.sqlite` (SQLite DB)
  - `telethon.session` (Telethon user session)

Rationale:
- Phase 1 requires **mutable** state (cards/trades) and Telethon requires a durable session.
- Both must survive container restarts.

## Observability

- Both services log to stdout.
- Provide simple health indicator:
  - ingestor: logs last message time
  - web: shows DB status + last ingested ts

## Acceptance criteria

- Services can start independently.
- DB schema version is readable from either service.
