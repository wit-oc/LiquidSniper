# Task 19 Provider Contract Implementation Brief

Status: Draft for implementation (2026-02-18)  
Owner: Redact + Wit  
Depends on: `docs/DATA_FEED_STRATEGY_V1.md`, `docs/EXECUTION_CORE_COMMAND_CONTRACT_V1.md`

---

## 1) Purpose

Define the deterministic market-data provider contract and canonical candle persistence schema used by strategy scoring/execution gates. This task hardens interface and data guarantees; it does not implement scheduling (Task 20) or quality-gate policy logic (Task 21).

---

## 2) In scope

1. `MarketDataProvider` contract (OHLCV required; funding/OI optional hooks).
2. Canonical `market_candles` schema (with uniqueness + integrity constraints).
3. Deterministic validation and normalized reason codes for malformed payloads.
4. Provider-health contract surface consumed by orchestration and policy gates.

Out of scope:
- Candle-close scheduler/backfill orchestration (Task 20).
- Aggregation/quality scoring policy (Task 21).
- Strategy payload mapping (Task 14/15).

---

## 3) Provider interface contract (v1)

Python protocol (or abstract base class) must expose:

- `fetch_ohlcv(symbol: str, timeframe: str, since_ms: int | None, limit: int) -> list[CandleDTO]`
- `fetch_funding(symbol: str, since_ms: int | None, limit: int) -> list[FundingDTO]` (optional; may return empty)
- `fetch_open_interest(symbol: str, since_ms: int | None, limit: int) -> list[OpenInterestDTO]` (optional; may return empty)
- `provider_health() -> ProviderHealth`

Determinism requirements:
- Returned candles sorted ascending by `ts_open_ms`.
- Stable numeric coercion to decimal-safe representation before persistence.
- No provider-specific field leakage beyond adapter boundary.

---

## 4) Canonical candle schema contract

## 4.1 Table: `market_candles`

Required columns:

- `id` (PK)
- `provider_id` (text, not null)
- `venue` (text, not null)
- `symbol` (text, not null)
- `timeframe` (text, not null)
- `ts_open_ms` (bigint, not null)
- `ts_close_ms` (bigint, not null)
- `open` (numeric, not null)
- `high` (numeric, not null)
- `low` (numeric, not null)
- `close` (numeric, not null)
- `volume` (numeric, not null)
- `ingest_ts_ms` (bigint, not null)
- `dataset_version` (text, not null)
- `trace_id` (text, not null)

Uniqueness + indexes:
- Unique key: `(provider_id, venue, symbol, timeframe, ts_open_ms)`
- Index: `(symbol, timeframe, ts_open_ms)`
- Index: `(trace_id)`

## 4.2 Integrity checks (fail closed)

Reject candle with deterministic reason code when:
- `ts_close_ms <= ts_open_ms` -> `CANDLE_TS_INVALID`
- any OHLCV null/non-numeric -> `CANDLE_VALUE_INVALID`
- `high < max(open, close)` or `low > min(open, close)` -> `CANDLE_RANGE_INVALID`
- duplicate unique key in same run with mismatched values -> `CANDLE_DUPLICATE_CONFLICT`
- timeframe not in allowlist (`1m`,`5m`,`15m`,`1h`,`4h`,`1d`,`1w`) -> `TIMEFRAME_UNSUPPORTED`

---

## 5) Contract DTOs (canonical)

`CandleDTO` fields:
- `provider_id`, `venue`, `symbol`, `timeframe`
- `ts_open_ms`, `ts_close_ms`
- `open`, `high`, `low`, `close`, `volume`
- `dataset_version`, `trace_id`

`ProviderHealth` fields:
- `provider_id`
- `status` (`ok|degraded|down`)
- `reason_codes` (array)
- `rate_state` (`normal|throttled|tripped`)
- `as_of_ms`

---

## 6) Acceptance criteria (Task 19 done when)

1. Provider contract is implemented as a stable interface with typed DTOs.
2. `market_candles` migration exists with required fields, uniqueness key, and indexes.
3. Validator emits deterministic reason codes for all listed integrity failures.
4. Replay of identical provider payload into empty DB yields byte-stable row values/order.
5. Contract tests cover:
   - happy-path ingest,
   - duplicate idempotent ingest,
   - duplicate conflict reject,
   - malformed OHLCV reject,
   - unsupported timeframe reject.

---

## 7) Implementation notes for handoff

- Keep adapter boundary strict: normalize all provider payloads before DB writes.
- Persist `trace_id` on every row to support audit/replay and Task 22 integration.
- Timeframe identifiers should normalize to lowercase (`1h`, `4h`, etc.) at contract boundary.
- Do not introduce scheduler semantics in this task; Task 20 owns run cadence.

---

## 8) Linkage

- Enables Task 20 scheduler/backfill to consume a stable persistence contract.
- Provides canonical candle baseline required by Task 22 (strategy feed integration).
- Supplies deterministic inputs needed for Task 14/15 payload mapping work.
