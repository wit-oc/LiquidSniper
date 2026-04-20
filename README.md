# LiquidSniper

**Current direction:** this repo is being refocused around **Surveyor** and **Arbiter**.

- **Surveyor** = descriptive market-state assembly
- **Arbiter** = interpretation / decision layer
- **Execution** = separate future boundary, not the current repo center

The current active goal is to:
- ingest a canonical market-data feed,
- persist an auditable candle store,
- assemble a multi-timeframe market-state packet,
- inspect that packet in an operator UI,
- and use that packet for replay / simulation / backtesting.

> Important: older LiquidSniper surfaces still exist in the repo during cleanup, including ingestion, paper-runtime, and TradingView-heavy lanes. Treat those as **legacy / in refactor**, not the primary product identity.

Primary architecture references:
- `docs/INTRADAY_REVISIT_SURVEYOR_ARBITER_ARCHITECTURE_V1.md`
- `docs/SURVEYOR_ARBITER_REPO_REFOCUS_PLAN_2026-04-19.md`

---

## Current architecture

### Core layers

1) **Canonical feed ingestion**
- current checkpoint source: OKX via CCXT
- persists into canonical SQLite tables such as `market_candles`, `feed_checkpoints`, and `feed_health_events`

2) **Surveyor packet assembly**
- builds a descriptive multi-timeframe packet for `1W`, `1D`, `4H`, and `5m`
- combines candle availability/freshness, structure context, authoritative S/R surfaces, Fib context, dynamic levels, and provenance

3) **Operator UI**
- Streamlit inspection surface for reviewing Surveyor packet state
- intended to make packet freshness, completeness, and traceability visible before downstream interpretation

4) **Arbiter (next boundary)**
- future explicit interpretation layer that consumes Surveyor output
- responsible for deciding whether the evidence is strong enough for watch/reject/candidate flows

### Separation of concerns

- **Surveyor:** descriptive only
- **Arbiter:** interpretation / decision logic
- **Execution:** intentionally downstream and separate

---

## Current scope

### What the repo is actively optimizing for now

- canonical OHLCV ingestion
- deterministic market-state packet assembly
- operator-facing packet inspection
- robust replay / simulation / backtesting on top of the canonical packet

### What is no longer the primary repo identity

- Telegram/Mobchart ingestion as the center of the system
- paper-trading runtime behavior as the center of the system
- TradingView automation as the center of the system

Those surfaces may still remain temporarily for reference or migration, but they are no longer the headline architecture.

---

## Data model (draft)

We’ll start with a minimal schema and extend.

### `RawTelegramMessage`
- `source`: `"telegram"`
- `ts_ingested`: ISO timestamp
- `chat_id`
- `message_id`
- `text`
- `entities` (optional)
- `attachments` (optional)

### `SignalEvent` (derived)
- `source`: `"mobchart"`
- `ts_alert`: ISO timestamp (from message if present; else receive time)
- `symbol` (e.g., `ETH/USDT`)
- `side` (`bid` | `ask` | `unknown`)
- `event_type` (e.g., `liquidity_level_approaching`, `liquidity_touch`)
- `level_price` (optional)
- `distance_pct` (optional)
- `size_usd` (optional)
- `strength` (optional)
- `lifespan_min` (optional)
- `raw_ref`: pointer back to `RawTelegramMessage`

---

## Roadmap

- [ ] Collect sample Mobchart alerts (verbatim) and finalize the parser
- [ ] Define the **trading universe** (Phase 1: Top 100 by market cap, USDT pairs) and enforce it upstream (Mobchart whitelist) + in ingest (safety net)
- [ ] Implement ingestion → JSONL event store
- [ ] Implement React table viewer
- [ ] Add enrichment hooks (price candles, etc.)
- [ ] Add evaluator reports
- [ ] Only then: design execution bot interface and risk engine

---

## Repo layout (proposed)

- `apps/ingestor/` — telegram ingestion service (Phase 1)
- `apps/viewer/` — React UI (Phase 1)
- `packages/core/` — shared types + parsing + storage helpers
- `docs/` — architecture, MVP definition, threat model, universe selection, and later execution-bot contract

---

## Safety / threat model (draft)

- Treat incoming messages as **untrusted input**.
- No secrets in the analytics system.
- Strict separation before any execution exists.
- Prefer sandboxed execution for any future automation.

---

## Developer workflow

- Local environment setup: `docs/dev_setup.md`
- Paper daemon operations: `docs/PAPER_DAEMON_RUNBOOK_V1.md`
- Pre-merge quality gate: `docs/PRE_MERGE_CHECKLIST.md`
- Codex on Mac mini runbook: `docs/CODEX_CLI_RUNBOOK.md`

## License

TBD
