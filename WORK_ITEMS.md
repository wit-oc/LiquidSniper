# LiquidSniper — Work Items (Phase 1)

This is the project’s **single, repo-native** work tracker.

Conventions:
- Use one checkbox per work item.
- Keep items sized so a single item can usually be completed in **1–2 PRs**.
- Prefer linking to commits/PRs/issues when available.

Status tags:
- **[Now]** actively being worked
- **[Next]** queued for immediate start
- **[Later]** backlog
- **[Blocked]** waiting on a decision/dependency

---

## 0) Decisions (must lock early)

- [ ] **[Next]** Choose storage for MVP: **SQLite** vs JSONL (recommend SQLite for UI + edits; still can export JSONL)
- [ ] **[Next]** Choose Telegram ingestion method: **Bot token polling** vs user session (Telethon)
- [ ] **[Next]** Choose web UI stack: **Streamlit** (fast) vs React/Next.js (more work)

## 1) Data model (cards + trades)

- [ ] **[Next]** Define `cards` table (symbol-centric) + states: `inbox|active|archived`
- [ ] **[Next]** Define `confluences` table: one row per `(card_id, venue, market_type, level_price, side, size_usd, distance_pct, strength, age)`
- [ ] **[Next]** Define `trades` table (manual): `entry`, `stop`, `tp_final`, `rr_best`, `status`, `notes`

## 2) Ingestion service (Telegram → DB)

- [ ] **[Next]** Implement Telegram ingestor (polling) that writes `raw_telegram_messages` rows
- [ ] **[Next]** Implement parser for Mobchart payloads (single-line + batch multiline) → `signal_events`
- [ ] **[Next]** Implement card builder: `signal_event` → upsert `card` + insert `confluence`
- [ ] **[Later]** Add dedupe (message_id + line_index + hash)

## 3) Web app (cards UI)

- [ ] **[Next]** Cards Inbox page (filters by symbol, venue, side, recency)
- [ ] **[Next]** Card detail view: show all confluences grouped by venue/market
- [ ] **[Next]** Actions: **Delete/Archive** card; **Activate** card
- [ ] **[Next]** Active Trades page: list active cards + editable manual trade fields
- [ ] **[Later]** Add “score” stub (computed column) with placeholder logic

## 4) Packaging / Ops

- [ ] **[Next]** Dockerfile + docker-compose (web + ingestor) with shared volume for SQLite
- [ ] **[Next]** Healthcheck endpoints + basic logs
- [ ] **[Later]** Export: CSV/JSONL download from UI

---

## Notes / current MVP target

Phase 1 deliverable: **`docker compose up`** brings up:
- an ingestor reading Telegram and writing a local DB
- a web UI that shows **symbol cards** with **multi-exchange confluences** and an **Active** workflow
