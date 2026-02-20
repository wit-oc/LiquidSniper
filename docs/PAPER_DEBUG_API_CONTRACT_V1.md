# Paper Debug API Contract v1

Read-only contract for paper-mode strategy account diagnostics.

## Read-only + auth guard
- Methods allowed: `GET`, `HEAD` only.
- Any non-read method returns `405` with `READ_ONLY_MODE` error payload.
- Guard supports either:
  - `Authorization: Bearer <LIQUIDSNIPER_DEBUG_TOKEN>`
  - Basic auth via `LIQUIDSNIPER_DEBUG_USER` + `LIQUIDSNIPER_DEBUG_PASS`

## Filters (all list/snapshot endpoints)
- `strategy`: `scalp | intraday | swing`
- `run_id`: exact run id
- `test_id`: exact test-id from run payload (`test_id` or `trade_intent.test_id`)
- `limit`: integer, default `200`, max `1000`

## Endpoints
- `GET /api/v1/debug/strategies`
  - Returns per-strategy summary cards (`runs_total`, `executed_total`, `rejected_total`, `open_positions`, `latest_run_ts`).

- `GET /api/v1/debug/orders`
  - Returns recent run/order flow rows.

- `GET /api/v1/debug/positions`
  - Returns inferred open paper positions (executed runs with no explicit exit reason).

- `GET /api/v1/debug/events`
  - Returns gate/reject/feed reason code events.

- `GET /api/v1/debug/snapshot`
  - Returns combined payload: `strategies`, `orders`, `positions`, `events`, plus `meta.filters` and `meta.read_only=true`.

## Response envelope
All endpoints return:
```json
{
  "data": [],
  "meta": {
    "read_only": true,
    "count": 0,
    "filters": {
      "strategy": null,
      "run_id": null,
      "test_id": null,
      "limit": 200
    }
  }
}
```
