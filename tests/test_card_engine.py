from __future__ import annotations

from pathlib import Path

from liquidsniper.core.card_engine import (
    activate_card,
    archive_card,
    get_card,
    list_cards,
    record_event_confluence,
    upsert_card_for_event,
)
from liquidsniper.core.db import init_db


def _event(symbol: str, *, ts: str = "2026-02-12T12:00:00+00:00") -> dict:
    return {
        "symbol": symbol,
        "ts_ingested": ts,
        "venue": "binance",
        "market_type": "futures",
        "side": "ask",
        "level_price": 1.234,
        "liquidity_size_usd": 123000.0,
        "distance_pct": 1.2,
        "strength_emoji_raw": "🌒",
        "age_raw": "13h+",
    }


def test_upsert_card_new_symbol_creates_inbox(tmp_path: Path) -> None:
    conn = init_db(str(tmp_path / "ls.sqlite"))
    card_id = upsert_card_for_event(conn, _event("DOTUSDT"))

    card = get_card(conn, "DOTUSDT")
    assert card is not None
    assert card["id"] == card_id
    assert card["status"] == "inbox"


def test_upsert_card_existing_symbol_updates_last_signal(tmp_path: Path) -> None:
    conn = init_db(str(tmp_path / "ls.sqlite"))
    first = _event("DOTUSDT", ts="2026-02-12T12:00:00+00:00")
    second = _event("DOTUSDT", ts="2026-02-12T13:00:00+00:00")

    card_id_1 = upsert_card_for_event(conn, first)
    card_id_2 = upsert_card_for_event(conn, second)

    assert card_id_1 == card_id_2
    card = get_card(conn, "DOTUSDT")
    assert card is not None
    assert card["last_signal_ts"] == "2026-02-12T13:00:00+00:00"


def test_record_event_confluence_appends_rows(tmp_path: Path) -> None:
    conn = init_db(str(tmp_path / "ls.sqlite"))
    card_id, confl_id = record_event_confluence(conn, _event("CRVUSDT"))

    assert card_id > 0
    assert confl_id > 0

    count = conn.execute("SELECT COUNT(*) FROM confluences WHERE card_id = ?;", (card_id,)).fetchone()[0]
    assert count == 1


def test_activate_card_creates_trade_row(tmp_path: Path) -> None:
    conn = init_db(str(tmp_path / "ls.sqlite"))
    upsert_card_for_event(conn, _event("HANAUSDT"))

    card_id = activate_card(conn, "HANAUSDT")
    card = get_card(conn, "HANAUSDT")
    assert card is not None
    assert card["status"] == "active"

    trade_count = conn.execute("SELECT COUNT(*) FROM trades WHERE card_id = ?;", (card_id,)).fetchone()[0]
    assert trade_count == 1


def test_archive_and_list_cards_by_status(tmp_path: Path) -> None:
    conn = init_db(str(tmp_path / "ls.sqlite"))
    upsert_card_for_event(conn, _event("BTCUSDT"))
    upsert_card_for_event(conn, _event("ETHUSDT"))

    archived = archive_card(conn, "BTCUSDT")
    assert archived is True

    inbox = list_cards(conn, status="inbox")
    archived_rows = list_cards(conn, status="archived")

    assert any(r["symbol"] == "ETHUSDT" for r in inbox)
    assert any(r["symbol"] == "BTCUSDT" for r in archived_rows)
