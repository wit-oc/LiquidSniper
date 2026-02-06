# LiquidSniper Architecture

This doc expands the README into a more explicit system design.

## Goals

1. **Start safe**: ingest and analyze signals without trading access.
2. **Evidence-first**: measure signal quality before automation.
3. **Separation**: analytics engine and execution bot must be independently deployable.
4. **Reproducibility**: store raw inputs + derived outputs.

## Non-goals (for MVP)

- Not a trading bot.
- Not a backtester for all strategies.
- Not a high-frequency system.

## System boundaries

### Analytics engine boundary

Allowed:
- Receive Telegram messages (Mobchart alerts)
- Parse and store them
- Enrich with public market data
- Compute and display analytics

Forbidden:
- Holding signing keys
- Connecting to trading APIs
- Placing orders

### Execution bot boundary (future)

Allowed:
- Read TradeIntents from analytics output
- Enforce risk limits
- Place orders

Forbidden:
- Accepting raw untrusted messages directly

## Interfaces

### Event ingestion

- Input: Telegram message
- Output: Append-only record to the event store

### Enrichment

- Input: SignalEvent
- Output: EnrichedEvent (signal + market context)

### Evaluation

- Input: EnrichedEvent stream
- Output: Reports (tables + plots + summary)

### Execution contract (future)

- Input: TradeIntent
- Output: ExecutionResult + audit log

TradeIntent should be fully specified:
- instrument
- side
- entry plan
- stop plan
- TP plan
- max slippage
- expiry (time-in-force)
- rationale + references (which signals/events caused this)

## MVP implementation notes

### Storage

Start with **JSONL**:
- easy to append
- easy to diff
- easy to load into pandas/duckdb

Consider SQLite later if:
- event volume becomes large
- we need indexing / relational joins

### Viewer

A minimal React viewer should support:
- list view of events
- filtering by symbol / date / event_type
- full raw message expansion
- export to CSV

## Security considerations

- All incoming messages are untrusted.
- Parser should be strict and defensive.
- Store raw messages for audit.
- Avoid executing URLs or embedded content.

## Open questions

- What does a Mobchart liquidity alert payload look like in Telegram? (need samples)
- Which markets/pairs matter first? (ETH, BTC, SOL)
- What evaluation windows matter for scalping? (30s / 2m / 5m / 15m)
- Which venue will ultimately be used for execution (US constraints)?
