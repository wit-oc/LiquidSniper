# LiquidSniper

**LiquidSniper** is a signal-stream + analytics engine for liquidity-level alerts (starting with **Mobchart Liquidity Screener → Telegram notifications**).

The project is intentionally phased:

- **Phase 1 (MVP):** ingest + log a signal stream (no trading, no keys)
- **Phase 2:** enrich signals with additional data streams and compute “trade intent” candidates
- **Phase 3 (future):** isolated execution bot (separate container/process) that consumes trade intents, enforces risk, and places trades

> Design constraint: the analytics engine must be safe to run even on untrusted inputs. It should never hold private keys or have trading privileges.

---

## Why

- Scalping / low-timeframe trading is execution- and risk-discipline-heavy.
- Third-party bots are hard to trust with custody and hard to audit.
- Even good signals can fail in certain regimes; we want **circuit breakers** and **daily loss limits** before automation exists.

LiquidSniper starts by building the *instrumentation and evidence*:
- what signals fired
- when they fired
- what the market did afterwards
- which signal settings seem predictive

---

## High-level architecture

### Components

1) **Signal Ingestor** (Phase 1)
- Input: Telegram messages (Mobchart notifications)
- Output: structured `SignalEvent` records appended to a local data store

2) **Event Store** (Phase 1)
- Append-only storage (start simple: JSONL; optionally SQLite later)
- Guarantees reproducibility: raw message + parsed fields + timestamps

3) **Viewer / Explorer** (Phase 1)
- Small React UI wrapper around the event store
- Table view + filters + search
- Allows manual tagging/notes (optional)

4) **Enrichment Workers** (Phase 2)
- Pull additional context (e.g., price candles, funding, volatility proxies)
- Produce derived metrics (MFE/MAE over time windows, etc.)

5) **Strategy Evaluator** (Phase 2)
- Runs hypothetical rules on historical events
- Outputs reports: hit rate, expectancy, sensitivity to fee/slippage assumptions

6) **Execution Bot** (Phase 3 / intentionally separate)
- Separate container/process with explicit isolation boundaries
- Consumes only signed/validated “TradeIntents”
- Enforces:
  - max risk per trade (e.g., 1%)
  - daily loss cap (halt until next day)
  - max position / max leverage
  - circuit breakers (stale price feed, abnormal slippage, infra issues)

### Separation of concerns

- **Analytics engine:** safe, no keys, no trading endpoints.
- **Execution bot:** dangerous, isolated, least privilege.

---

## MVP scope (Phase 1)

### What it does

- Listen for Telegram messages (Mobchart Liquidity Screener notifications)
- Store:
  - raw message text
  - message metadata (chat, message id, timestamp)
  - parsed fields when possible (symbol, side, level price, size, distance, etc.)
- Provide a UI to browse and export the event stream

### What it explicitly does *not* do

- No order placement
- No wallets / keys
- No exchange/perps connectivity
- No “auto trade” or “auto TP/SL”

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
- `docs/` — architecture, MVP definition, threat model, and later execution-bot contract

---

## Safety / threat model (draft)

- Treat incoming messages as **untrusted input**.
- No secrets in the analytics system.
- Strict separation before any execution exists.
- Prefer sandboxed execution for any future automation.

---

## License

TBD
