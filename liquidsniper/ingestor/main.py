"""Telegram ingestion entrypoint for LiquidSniper MVP.

Usage:
  python -m liquidsniper.ingestor.main --source @MobChartBot --limit 20 --once
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from telethon import TelegramClient

from liquidsniper.core.card_engine import record_event_confluence
from liquidsniper.core.db import init_db
from liquidsniper.core.parser_mobchart import parse_mobchart_message


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _keychain_get(service: str, account: str = "openclaw") -> str | None:
    p = subprocess.run(
        ["security", "find-generic-password", "-a", account, "-s", service, "-w"],
        capture_output=True,
        text=True,
        check=False,
    )
    if p.returncode != 0:
        return None
    v = p.stdout.strip()
    return v or None


def _secret(name: str) -> str:
    val = os.getenv(name) or _keychain_get(name)
    if not val:
        raise RuntimeError(f"Missing required secret: {name}")
    return val


def _insert_raw_message(conn: sqlite3.Connection, chat_id: int, message_id: int, sender: str, text: str, raw_json: str) -> int:
    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO raw_telegram_messages(
              ts_ingested, telegram_chat_id, telegram_message_id, sender, text, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            (_utc_now_iso(), str(chat_id), str(message_id), sender, text, raw_json),
        )
        row = conn.execute(
            "SELECT id FROM raw_telegram_messages WHERE telegram_chat_id=? AND telegram_message_id=?;",
            (str(chat_id), str(message_id)),
        ).fetchone()
    return int(row[0])


def _insert_signal_event(conn: sqlite3.Connection, parsed: dict[str, Any], raw_id: int, line_index: int) -> int:
    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO signal_events(
              ts_alert, ts_ingested, venue, market_type, symbol, side, liquidity_side,
              level_price, liquidity_size_usd, distance_pct,
              strength_emoji_raw, side_emoji_raw, age_raw, age_seconds_min,
              raw_text, raw_message_id, line_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                None,
                _utc_now_iso(),
                parsed.get("venue"),
                parsed.get("market_type"),
                parsed.get("symbol"),
                parsed.get("side") or "unknown",
                parsed.get("liquidity_side") or "unknown",
                parsed.get("level_price"),
                parsed.get("liquidity_size_usd"),
                parsed.get("distance_pct"),
                parsed.get("strength_emoji_raw"),
                parsed.get("side_emoji_raw"),
                parsed.get("age_raw"),
                parsed.get("age_seconds_min"),
                parsed.get("raw_text"),
                raw_id,
                int(line_index),
            ),
        )
        row = conn.execute(
            "SELECT id FROM signal_events WHERE raw_message_id = ? AND line_index = ?;",
            (raw_id, int(line_index)),
        ).fetchone()
    return int(row[0])


async def ingest_once(source: str, limit: int, db_path: str, session_path: str) -> dict[str, int]:
    api_id = int(_secret("LIQUIDSNIPER_TELEGRAM_API_ID"))
    api_hash = _secret("LIQUIDSNIPER_TELEGRAM_API_HASH")

    Path(session_path).parent.mkdir(parents=True, exist_ok=True)
    conn = init_db(db_path)

    raw_count = 0
    parsed_count = 0
    parse_error_count = 0
    ignored_count = 0
    persist_error_count = 0
    confluence_count = 0

    async with TelegramClient(session_path, api_id, api_hash) as client:
        entity = await client.get_entity(source)
        async for msg in client.iter_messages(entity, limit=limit):
            text = msg.message or ""
            if not text.strip():
                continue

            raw_id = _insert_raw_message(
                conn,
                chat_id=msg.chat_id or 0,
                message_id=msg.id,
                sender=str(getattr(msg, "sender_id", "")),
                text=text,
                raw_json=msg.to_json(),
            )
            raw_count += 1

            parsed_rows = parse_mobchart_message(text)
            for i, row in enumerate(parsed_rows):
                et = row.get("event_type")
                if et == "ignored_line":
                    ignored_count += 1
                    continue
                if et == "parse_error":
                    parse_error_count += 1
                    continue

                line_index = int(row.get("line_index", i))
                try:
                    event_id = _insert_signal_event(conn, row, raw_id, line_index)
                    parsed_count += 1
                except sqlite3.Error:
                    persist_error_count += 1
                    continue

                try:
                    row_for_card = dict(row)
                    row_for_card["source_event_id"] = event_id
                    record_event_confluence(conn, row_for_card)
                    confluence_count += 1
                except (sqlite3.Error, ValueError):
                    persist_error_count += 1

    return {
        "raw_messages": raw_count,
        "parsed_events": parsed_count,
        "parse_errors": parse_error_count,
        "ignored_lines": ignored_count,
        "confluences_written": confluence_count,
        "persist_errors": persist_error_count,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="Telegram source handle, e.g. @MobChartBot")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--once", action="store_true", default=True)
    ap.add_argument("--db", default="data/liquidsniper.sqlite")
    ap.add_argument("--session", default="data/telegram_liquidsniper")
    args = ap.parse_args()

    result = asyncio.run(ingest_once(args.source, args.limit, args.db, args.session))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
