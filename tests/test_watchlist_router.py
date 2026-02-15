from __future__ import annotations

from liquidsniper.core.watchlist_router import classify_symbol, normalize_symbol


def test_normalize_symbol_handles_exchange_and_perp_suffix() -> None:
    assert normalize_symbol("BINANCE:BTCUSDT") == "BTCUSDT"
    assert normalize_symbol("BTCUSDT.P") == "BTCUSDT"


def test_classify_symbol_states() -> None:
    cfg = "config/watchlists.json"
    assert classify_symbol("BTCUSDT", cfg).state == "charted_primary"
    assert classify_symbol("DOGEUSDT", cfg).state == "supported_blofin_uncharted"
    assert classify_symbol("UNKNOWNUSDT", cfg).state == "unsupported_or_unknown"
