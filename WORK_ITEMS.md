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

## Integration reconciliation snapshot (2026-02-15)

- [x] **[Done]** Task 09 — analysis run contract + pipeline skeleton
- [x] **[Done]** Task 10 — would-alert simulation mode
- [x] **[Done]** Task 11 — TradingView artifact linking + mount contract
- [x] **[Done]** Task 12 — minimal diagnostic UI updates
- [x] **[Done]** Task 13 — OpenClaw orchestration + rulebook/bootstrap + secrets flow
- [x] **[Done]** Task 05 — Telegram ingestion wiring integration hardening
- [x] **[Done]** Task 06 — Streamlit UI cleanup against diagnostic + card views
- [x] **[Done]** Task 07 — Docker/compose verification with shared artifact mount
- [x] **[Done]** Task 08 — runbook/validation gate update for simulation rollout

---

## Strategy automation alignment snapshot (2026-02-18)

- [x] **[Done]** Added `docs/AUTOMATED_TRADING_AGENT_ALIGNMENT_V1.md` to map proposal -> LiquidSniper docs/tasks/dependencies.
- [x] **[Done]** Upgraded `docs/TRADING_STRATEGY_RUNBOOK_V1.md` to v1.1 with HTF-anchor model and deterministic payload requirements.
- [x] **[Done]** Added canonical paper-MVP sequencing doc: `docs/MVP_PAPER_SEQUENCE_V1.md`.
- [x] **[Done]** Phase 0 dependency default/stub handoff landed: `.env.example` fail-closed placeholders, `docs/OPERATOR_DEPENDENCY_STUBS_V1.md`, and go/no-go stub verification gates.
- [x] **[Done]** Task 14 scaffold contract created: `docs/HTF_ANCHOR_PROFILE_CONTRACT_V1.md` (1D+1H default profiles, deterministic validation constraints).
- [ ] **[Now]** Task 14 implementation kickoff — wire rulebook/schema + regime permission integration against the scaffold contract.
- [ ] **[Now]** Task 15 — map lecture-derived scoring buckets into decision payload fields (`score_total`, bucket breakdown, penalties).
- [ ] **[Next]** Task 16 — dependency threading + strategy/policy/execution non-bypass boundaries.
- [ ] **[Next]** Task 17 — two-pass adversarial validation harness and gate checks.
- [ ] **[Next]** Task 18 — packaging boundary decision (integrated module vs separate execution core).

---

> Note: Sections `0)`-`4)` below are retained as legacy Phase-1 planning detail and may contain stale checkbox state.  
> Canonical active sequencing is now the two snapshots above (`Integration reconciliation` and `Strategy automation alignment`).

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
