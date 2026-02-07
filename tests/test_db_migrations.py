"""Tests for SQLite schema migrations."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from liquidsniper.core.db import MIGRATIONS_DIR, apply_migrations, init_db


EXPECTED_TABLES = {
    "schema_migrations",
    "raw_telegram_messages",
    "signal_events",
    "cards",
    "confluences",
    "trades",
}


def test_init_db_creates_expected_tables(tmp_path: Path) -> None:
    """Initializing a fresh DB applies schema migrations."""
    db_file = tmp_path / "liquidsniper.sqlite"
    conn = init_db(str(db_file))

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()
    }

    conn.close()
    assert EXPECTED_TABLES.issubset(tables)


def test_raw_message_unique_constraint_is_enforced(tmp_path: Path) -> None:
    """Duplicate (chat_id, message_id) pairs should fail."""
    conn = init_db(str(tmp_path / "liquidsniper.sqlite"))
    row = ("2026-02-07T00:00:00+00:00", "chat-1", "msg-1", "sender", "text", "{}")

    conn.execute(
        """
        INSERT INTO raw_telegram_messages(
            ts_ingested, telegram_chat_id, telegram_message_id, sender, text, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?);
        """,
        row,
    )

    with conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO raw_telegram_messages(
                    ts_ingested, telegram_chat_id, telegram_message_id, sender, text, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                row,
            )
    conn.close()


def test_apply_migrations_is_idempotent(tmp_path: Path) -> None:
    """Applying migrations repeatedly should not duplicate versions."""
    conn = init_db(str(tmp_path / "liquidsniper.sqlite"))
    apply_migrations(conn)

    versions = [
        row[0]
        for row in conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version;"
        ).fetchall()
    ]

    conn.close()
    expected_versions = sorted(path.stem for path in MIGRATIONS_DIR.glob("*.sql"))
    assert versions == expected_versions


def test_signal_event_unique_raw_line_guard(tmp_path: Path) -> None:
    """Duplicate signal rows for same raw message line should fail."""
    conn = init_db(str(tmp_path / "liquidsniper.sqlite"))
    conn.execute(
        """
        INSERT INTO raw_telegram_messages(
            ts_ingested, telegram_chat_id, telegram_message_id, sender, text, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?);
        """,
        ("2026-02-07T00:00:00+00:00", "chat-2", "msg-2", "sender", "text", "{}"),
    )
    raw_message_id = conn.execute(
        "SELECT id FROM raw_telegram_messages WHERE telegram_chat_id = ? AND telegram_message_id = ?;",
        ("chat-2", "msg-2"),
    ).fetchone()[0]

    row = (
        "2026-02-07T00:00:00+00:00",
        "binance",
        "perp",
        "BTCUSDT",
        "unknown",
        "unknown",
        raw_message_id,
        0,
    )
    conn.execute(
        """
        INSERT INTO signal_events(
            ts_ingested, venue, market_type, symbol, side, liquidity_side, raw_message_id, line_index
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        row,
    )

    with conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO signal_events(
                    ts_ingested, venue, market_type, symbol, side, liquidity_side, raw_message_id, line_index
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                row,
            )
    conn.close()
