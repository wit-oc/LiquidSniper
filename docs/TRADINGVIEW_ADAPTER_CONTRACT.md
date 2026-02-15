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
