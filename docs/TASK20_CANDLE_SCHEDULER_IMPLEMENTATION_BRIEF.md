# Task 20 Candle Scheduler + Backfill Implementation Brief

Status: Draft for implementation (2026-02-18)  
Owner: Redact + Wit  
Depends on: `docs/TASK19_PROVIDER_CONTRACT_IMPLEMENTATION_BRIEF.md`, `docs/DATA_FEED_STRATEGY_V1.md`, `docs/EXECUTION_CORE_COMMAND_CONTRACT_V1.md`

---

## 1) Purpose

Define a deterministic candle-close scheduler and bounded backfill flow that keeps canonical OHLCV windows fresh for scoring/execution gates while handling quota, outage, and data-integrity failures in a fail-closed manner.

---

## 2) In scope

1. Incremental candle-close scheduler contract per symbol/timeframe.
2. Startup/recovery backfill contract with bounded lookback and idempotent writes.
3. Failure-mode handling for provider/API/data failures with deterministic state transitions.
4. Scheduler health outputs consumed by `refresh-data` / `feed-health` surfaces.

Out of scope:
- Candle payload schema/validator internals (Task 19).
- Quality scoring and timeframe aggregation policy (Task 21).
- Strategy baseline swap to canonical store (Task 22).

---

## 3) Scheduler contract (v1)

## 3.1 Core loop

For each `(symbol, timeframe)` subscription:

1. Compute next expected closed-candle boundary in UTC.
2. Wait until boundary + settle lag (`close_lag_ms`, default 2500ms).
3. Fetch incremental window from provider using `since_ms = last_ts_open_ms`.
4. Validate + upsert candles into `market_candles` (Task 19 contract).
5. Advance checkpoint only when ingest batch commits successfully.

Determinism requirements:
- Single active worker per `(provider_id, venue, symbol, timeframe)` key.
- Stable ordering by `ts_open_ms` before persistence.
- Idempotent ingest path (replays do not mutate accepted rows).

## 3.2 Checkpoint state

Persist scheduler checkpoints in `feed_checkpoints`:

- `provider_id`, `venue`, `symbol`, `timeframe` (composite key)
- `last_ts_open_ms`
- `last_success_ms`
- `last_attempt_ms`
- `failure_count`
- `state` (`ok|degraded|tripped|resync_required`)
- `last_reason_code`
- `trace_id`

---

## 4) Backfill contract (v1)

## 4.1 Trigger conditions

Run backfill when any is true:
- first-time bootstrap (no checkpoint),
- detected gap (`expected_next_open_ms < newest_open_ms - timeframe_ms`),
- checkpoint marked `resync_required`.

## 4.2 Rules

- Backfill in bounded pages (default `limit=1000`) until gap closed or `max_backfill_bars` reached.
- Use deterministic page anchor progression (`since_ms = earliest_missing_open_ms`).
- Respect provider budget manager; backfill yields to incremental scheduler when budget constrained.
- On completion, verify contiguous coverage for target window; otherwise keep `resync_required`.

---

## 5) Failure-mode handling (required)

## 5.1 Failure classes -> reason codes -> action

1. Provider timeout/network errors  
   - code: `PROVIDER_TIMEOUT` / `PROVIDER_UNREACHABLE`  
   - action: exponential backoff with jitter; no checkpoint advance.

2. Quota/rate-limit responses (429/provider quota)  
   - code: `PROVIDER_RATE_LIMITED`  
   - action: throttle bucket, defer non-critical backfill, set state `degraded`.

3. 5xx or transient exchange faults  
   - code: `PROVIDER_UPSTREAM_ERROR`  
   - action: bounded retries; trip circuit on threshold.

4. Empty/missing expected candle window  
   - code: `CANDLE_GAP_DETECTED`  
   - action: mark `resync_required`, enqueue bounded backfill.

5. Validation/integrity reject from Task 19  
   - code: pass-through validator code (`CANDLE_*`, `TIMEFRAME_UNSUPPORTED`)  
   - action: reject batch, increment failure count, circuit contribution.

## 5.2 Circuit breaker rules

- Trip key: `(provider_id, venue)`.
- Trip when `N` consecutive failures in `window_ms` (defaults: `N=5`, `window_ms=120000`).
- While tripped:
  - scheduler marks impacted checkpoints `tripped`,
  - strategy-facing health reports `down|degraded`,
  - no proposal path may treat affected timeframe as fresh.
- Recovery requires cooldown expiry + one successful probe.

---

## 6) Health/event contract outputs

Each scheduler cycle emits a deterministic health snapshot:

- `provider_id`, `venue`, `symbol`, `timeframe`
- `freshness_ms`
- `gap_bars`
- `state` (`ok|degraded|tripped|resync_required`)
- `reason_codes` (ordered)
- `as_of_ms`
- `trace_id`

`feed-health` aggregates by worst state across required windows.

---

## 7) Acceptance criteria (Task 20 done when)

1. Incremental scheduler runs on candle-close cadence (no hot-loop polling).
2. Checkpoint table/state machine is implemented and persisted.
3. Backfill closes detected gaps within configured bounds and remains idempotent.
4. Failure modes above emit deterministic reason codes and state transitions.
5. Circuit breaker prevents repeated failing calls and exposes degraded/tripped health.
6. Contract/integration tests cover:
   - boundary close ingest success,
   - startup bootstrap backfill,
   - gap detection + recovery,
   - rate-limit throttling behavior,
   - breaker trip + cooldown probe recovery.

---

## 8) Handoff notes

- Keep schedule math UTC-only; do not depend on local timezone.
- Do not let backfill starve incremental close-path freshness.
- Trace IDs must link scheduler attempt -> ingest batch -> health event for replay.
- Task 21 may tighten quality gating, but Task 20 must already fail closed on missing/stale windows.

---

## 9) Linkage

- Consumes Task 19 canonical ingest contract and validator reason codes.
- Provides deterministic freshness/gap semantics consumed by Task 22 strategy integration.
- Establishes scheduling baseline required before Task 23 budget/breaker hardening depth.
