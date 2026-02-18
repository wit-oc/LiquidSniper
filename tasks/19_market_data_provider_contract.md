# Task 19 — Market data provider contract + canonical candle schema

## Goal

Define a deterministic provider abstraction and persistence contract for strategy-grade market data.

## Deliverables

- `MarketDataProvider` contract for OHLCV (+ optional funding/OI hooks).
- Canonical `market_candles` schema and migration.
- Required metadata fields: provider id, venue, symbol, timeframe, open/close ts, ingest ts, dataset/version tags.
- Fail-closed validation rules for malformed/incomplete candles.

## Acceptance criteria

- Provider contract is documented and implemented as a stable interface.
- Candle rows can be persisted/replayed deterministically.
- Schema versioning and integrity expectations are explicit.
