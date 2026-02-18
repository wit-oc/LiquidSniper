# Task 20 — CCXT OHLCV backfill + incremental scheduler

## Goal

Implement CCXT-first canonical OHLCV ingestion for strategy timeframes.

## Deliverables

- `CcxtMarketDataProvider` implementation.
- Backfill command for seeded history by symbol/timeframe.
- Incremental candle-close scheduler for ongoing updates.
- Symbol/timeframe staggering and batch policy.

## Acceptance criteria

- Required timeframes (`1m`, `5m`, `15m`, `1H`, `4H`, `1D`, `1W`) are ingestible for target symbols.
- 429/5xx handling uses bounded retries with backoff/jitter.
- Ingest runs produce deterministic persistence and observable run summaries.
