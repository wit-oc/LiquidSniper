from __future__ import annotations

from liquidsniper.core.parser_mobchart import (
    parse_age_min_seconds,
    parse_mobchart_message,
    parse_size_usd,
)


def test_parse_single_line_sample() -> None:
    text = "Binance SPOT: 🌓 GPSUSDT $0.0097 $339.11K 0.1% 🔴 1h 22m"
    rows = parse_mobchart_message(text)

    assert len(rows) == 1
    row = rows[0]
    assert row["event_type"] == "liquidity_screener_alert"
    assert row["venue"] == "binance"
    assert row["market_type"] == "spot"
    assert row["symbol"] == "GPSUSDT"
    assert row["level_price"] == 0.0097
    assert row["liquidity_size_usd"] == 339_110
    assert row["distance_pct"] == 0.1
    assert row["side"] == "ask"
    assert row["liquidity_side"] == "sell"
    assert row["strength_emoji_raw"] == "🌓"
    assert row["age_raw"] == "1h 22m"
    assert row["age_seconds_min"] == 1 * 3600 + 22 * 60


def test_parse_scientific_notation_price() -> None:
    text = "Binance SPOT: 🌒 BTTCUSDT $3.3e-7 $156.44K 0% 🔴 4h 6m"
    row = parse_mobchart_message(text)[0]

    assert row["event_type"] == "liquidity_screener_alert"
    assert row["level_price"] == 3.3e-7
    assert row["liquidity_size_usd"] == 156_440
    assert row["distance_pct"] == 0.0


def test_parse_multiline_batch_with_context_inheritance() -> None:
    text = "\n".join(
        [
            "Binance FUTURES: 🌒 DYDXUSDT $0.115 $216.54K 1.8% 🔴 2h 21m",
            "🌒 DOTUSDT $1.354 $263.68K 1.2% 🔴 13h+",
            "🌔 HANAUSDT $0.0355 $81.01K 1.3% 🟢 3h 40m",
        ]
    )

    rows = parse_mobchart_message(text)
    assert len(rows) == 3

    for row in rows:
        assert row["event_type"] == "liquidity_screener_alert"
        assert row["venue"] == "binance"
        assert row["market_type"] == "futures"

    assert rows[1]["symbol"] == "DOTUSDT"
    assert rows[1]["age_seconds_min"] == 13 * 3600

    assert rows[2]["symbol"] == "HANAUSDT"
    assert rows[2]["side"] == "bid"
    assert rows[2]["liquidity_side"] == "buy"


def test_parsing_helpers_size_suffixes() -> None:
    assert parse_size_usd("339.11K") == 339_110
    assert parse_size_usd("2.66M") == 2_660_000
    assert parse_size_usd("1.2B") == 1_200_000_000


def test_parsing_helpers_age_formats() -> None:
    assert parse_age_min_seconds("13h+") == 13 * 3600
    assert parse_age_min_seconds("61h+") == 61 * 3600
    assert parse_age_min_seconds("3h 2m") == 3 * 3600 + 2 * 60
    assert parse_age_min_seconds("4h 6m") == 4 * 3600 + 6 * 60


def test_non_signal_line_is_ignored() -> None:
    text = "Binance SPOT: Welcome to MobChart — premium links in bio"
    rows = parse_mobchart_message(text)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "ignored_line"


def test_malformed_line_returns_parse_error_and_no_crash() -> None:
    # malformed-but-probable line (contains symbol/$/side marker) should count as parse_error
    text = "Binance SPOT: BADUSDT $oops $100K 1.0% 🔴 ???"
    rows = parse_mobchart_message(text)

    assert len(rows) == 1
    row = rows[0]
    assert row["event_type"] == "parse_error"
    assert row["venue"] == "binance"
    assert row["market_type"] == "spot"
    assert row["line_index"] == 0
    assert "error" in row
