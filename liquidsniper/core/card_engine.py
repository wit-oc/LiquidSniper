"""Card generation and workflow engine for LiquidSniper.

This module is DB-facing but intentionally simple: given parsed signal events,
maintain symbol-centric cards, confluences, and optional trade rows.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_or_create_card(conn: sqlite3.Connection, symbol: str, ts: str) -> int:
    row = conn.execute("SELECT id FROM cards WHERE symbol = ?;", (symbol,)).fetchone()
    if row:
        card_id = int(row[0])
        conn.execute(
            """
            UPDATE cards
            SET updated_ts = ?, last_signal_ts = COALESCE(?, last_signal_ts)
            WHERE id = ?;
            """,
            (ts, ts, card_id),
        )
        return card_id

    conn.execute(
        """
        INSERT INTO cards(symbol, status, created_ts, updated_ts, last_signal_ts)
        VALUES (?, 'inbox', ?, ?, ?);
        """,
        (symbol, ts, ts, ts),
    )
    return int(conn.execute("SELECT last_insert_rowid();").fetchone()[0])


def upsert_card_for_event(conn: sqlite3.Connection, event: dict[str, Any]) -> int:
    """Create/update card for a parsed signal event and return card_id."""
    symbol = str(event.get("symbol") or "").strip()
    if not symbol:
        raise ValueError("event.symbol is required")

    ts = str(event.get("ts_ingested") or _utc_now_iso())
    with conn:
        return _get_or_create_card(conn, symbol, ts)


def append_confluence(conn: sqlite3.Connection, event: dict[str, Any], card_id: int) -> int:
    """Append one confluence row for a signal event."""
    ts = str(event.get("ts_ingested") or _utc_now_iso())

    with conn:
        conn.execute(
            """
            INSERT INTO confluences(
                card_id,
                ts_first_seen,
                ts_last_seen,
                venue,
                market_type,
                side,
                level_price,
                liquidity_size_usd,
                distance_pct,
                strength_emoji_raw,
                age_raw,
                source_event_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                card_id,
                ts,
                ts,
                event.get("venue"),
                event.get("market_type"),
                event.get("side"),
                event.get("level_price"),
                event.get("liquidity_size_usd"),
                event.get("distance_pct"),
                event.get("strength_emoji_raw"),
                event.get("age_raw"),
                event.get("source_event_id"),
            ),
        )
        return int(conn.execute("SELECT last_insert_rowid();").fetchone()[0])


def record_event_confluence(conn: sqlite3.Connection, event: dict[str, Any]) -> tuple[int, int]:
    """Convenience helper: upsert card and append confluence for one event."""
    card_id = upsert_card_for_event(conn, event)
    confl_id = append_confluence(conn, event, card_id)
    return card_id, confl_id


def activate_card(conn: sqlite3.Connection, symbol: str) -> int:
    """Set card status active and ensure a trade row exists; returns card_id."""
    ts = _utc_now_iso()
    with conn:
        row = conn.execute("SELECT id FROM cards WHERE symbol = ?;", (symbol,)).fetchone()
        if not row:
            conn.execute(
                """
                INSERT INTO cards(symbol, status, created_ts, updated_ts, last_signal_ts)
                VALUES (?, 'active', ?, ?, ?);
                """,
                (symbol, ts, ts, ts),
            )
            card_id = int(conn.execute("SELECT last_insert_rowid();").fetchone()[0])
        else:
            card_id = int(row[0])
            conn.execute(
                "UPDATE cards SET status='active', updated_ts=? WHERE id=?;",
                (ts, card_id),
            )

        trade = conn.execute("SELECT id FROM trades WHERE card_id = ?;", (card_id,)).fetchone()
        if not trade:
            conn.execute(
                """
                INSERT INTO trades(card_id, created_ts, updated_ts, status)
                VALUES (?, ?, ?, 'planned');
                """,
                (card_id, ts, ts),
            )

        return card_id


def archive_card(conn: sqlite3.Connection, symbol: str) -> bool:
    """Archive card by symbol. Returns True if a row was updated."""
    ts = _utc_now_iso()
    with conn:
        cur = conn.execute(
            "UPDATE cards SET status='archived', updated_ts=? WHERE symbol=?;",
            (ts, symbol),
        )
    return cur.rowcount > 0


def get_card(conn: sqlite3.Connection, symbol: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT id, symbol, status, created_ts, updated_ts, last_signal_ts, score
        FROM cards
        WHERE symbol = ?;
        """,
        (symbol,),
    ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "symbol": row[1],
        "status": row[2],
        "created_ts": row[3],
        "updated_ts": row[4],
        "last_signal_ts": row[5],
        "score": row[6],
    }


def list_cards(conn: sqlite3.Connection, status: str | None = None) -> list[dict[str, Any]]:
    if status is None:
        rows = conn.execute(
            """
            SELECT id, symbol, status, created_ts, updated_ts, last_signal_ts, score
            FROM cards
            ORDER BY updated_ts DESC;
            """
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, symbol, status, created_ts, updated_ts, last_signal_ts, score
            FROM cards
            WHERE status = ?
            ORDER BY updated_ts DESC;
            """,
            (status,),
        ).fetchall()

    return [
        {
            "id": r[0],
            "symbol": r[1],
            "status": r[2],
            "created_ts": r[3],
            "updated_ts": r[4],
            "last_signal_ts": r[5],
            "score": r[6],
        }
        for r in rows
    ]
