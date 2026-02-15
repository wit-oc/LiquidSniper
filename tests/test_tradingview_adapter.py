from __future__ import annotations

from liquidsniper.core.tradingview_adapter import (
    parse_tv_link,
    valid_status_transition,
    validate_webhook_payload,
)


def test_parse_tv_link_extracts_symbol_and_interval() -> None:
    link = parse_tv_link("https://www.tradingview.com/chart/abc123/?symbol=BINANCE:BTCUSDT&interval=60")
    assert link.symbol == "BINANCE:BTCUSDT"
    assert link.interval == "60"


def test_validate_webhook_payload_required_fields_and_price() -> None:
    ok, err = validate_webhook_payload(
        {
            "symbol": "BTCUSDT",
            "timeframe": "15",
            "event": "cross_up",
            "price": "67234.5",
            "timestamp": "2026-02-14T16:00:00Z",
        }
    )
    assert ok is True
    assert err is None

    ok2, err2 = validate_webhook_payload(
        {
            "symbol": "BTCUSDT",
            "timeframe": "15",
            "event": "cross_up",
            "price": "not-a-number",
            "timestamp": "2026-02-14T16:00:00Z",
        }
    )
    assert ok2 is False
    assert err2 == "invalid_price"


def test_status_transitions_cover_all_mvp_states() -> None:
    assert valid_status_transition("ok", "unavailable") is True
    assert valid_status_transition("ok", "auth_required") is True
    assert valid_status_transition("ok", "failed") is True
    assert valid_status_transition("auth_required", "ok") is True
    assert valid_status_transition("failed", "unavailable") is True
    assert valid_status_transition("unknown", "ok") is False
