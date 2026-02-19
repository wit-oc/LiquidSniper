# TradingView Adapter Contract (MVP v1)

## Status model

Supported statuses:
- `ok`
- `unavailable`
- `auth_required`
- `failed`

These states are contract-tested in `tests/test_tradingview_adapter.py`.

## Link parsing

`parse_tv_link(url)` extracts:
- `symbol` (e.g. `BINANCE:BTCUSDT`)
- `interval` (if present)

## Webhook payload validation

`validate_webhook_payload(payload)` requires:
- `symbol`
- `timeframe`
- `event`
- `price` (numeric)
- `timestamp`

Returns `(is_valid, error_code)` for deterministic handling.

## Screenshot artifact mount contract (Task 11)

Shared-mount defaults for backend + UI:
- Backend writer root: `/data/artifacts`
- UI reader root: `/artifacts`

Environment overrides:
- `TV_ARTIFACTS_WRITER_ROOT`
- `TV_ARTIFACTS_UI_ROOT`

`liquidsniper.core.tv_artifacts.query_ui_artifact_links(...)` returns a UI-ready per-run map for:
- `15m`, `1h`, `4h`, `1D`, `1W`

Backend paths under writer root are translated to UI hrefs by preserving relative suffixes.
