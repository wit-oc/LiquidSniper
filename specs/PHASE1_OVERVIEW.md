# Phase 1 Specs — Overview

Phase 1 delivers a **Docker-run analysis engine** for Mobchart Liquidity Screener Telegram alerts.

## Primary outcome

`docker compose up` brings up:
- a **Telethon ingestor** that reads Mobchart alerts from Telegram and writes to a local DB
- a **web app** that shows symbol-centric **Cards** aggregating cross-exchange confluences

## Non-goals

- no exchange API trading
- no private keys
- no automated entries/exits

## Phase 1 user workflow

1) Mobchart sends Telegram alert(s)
2) Ingestor stores raw messages + parsed events
3) System upserts a symbol **Card** into **Inbox**
4) User reviews Inbox cards
5) User can:
   - **Activate** a card (creates/opens Trade fields)
   - **Archive/Delete** a card (removes it from inbox unless new alerts arrive)
6) User tracks trade manually (SL/TP/RR/Status/Notes)

## Spec index

- `01_architecture.md`
- `02_storage_schema.md`
- `03_telegram_ingestion_telethon.md`
- `04_parsing_mobchart_payloads.md`
- `05_card_engine.md`
- `06_web_ui_streamlit.md`
- `07_docker_ops.md`
- `08_testing_runbook.md`

## Acceptance criteria

- Clean machine: `docker compose up` works with documented setup.
- Ingestor runs continuously and persists state across restarts.
- UI shows:
  - Inbox cards (symbol list)
  - Card detail (confluences)
  - Active page (manual trade fields)
- Actions work:
  - Activate → card moves to active
  - Archive/Delete → card removed from inbox
- Raw messages are stored for audit.
