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
    "analysis_runs",
    "candidate_decisions",
    "screenshot_artifacts",
    "market_candles",
    "feed_checkpoints",
    "feed_health_events",
    "strategy_accounts",
    "strategy_account_configs",
    "sr_zones",
    "sr_zone_touches",
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


def test_sr_zone_diagnostic_columns_exist_after_migrations(tmp_path: Path) -> None:
    """SR diagnostic columns should be present for selection introspection."""
    conn = init_db(str(tmp_path / "liquidsniper.sqlite"))
    cols = [row[1] for row in conn.execute("PRAGMA table_info(sr_zones);").fetchall()]
    conn.close()

    for expected in [
        "reaction_efficiency_score",
        "spent_zone_penalty",
        "retest_weight",
        "selection_score",
        "zone_width_bps",
    ]:
        assert expected in cols


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


def test_analysis_run_and_decision_write_read_flow(tmp_path: Path) -> None:
    """A run can persist one decision and an optional screenshot artifact."""
    conn = init_db(str(tmp_path / "liquidsniper.sqlite"))

    conn.execute(
        """
        INSERT INTO analysis_runs(
            created_ts, symbol, side, zone_priority_score, context_score, pre_score,
            agent_confidence_score, final_score, score_version, rulebook_ref, run_mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            "2026-02-15T13:00:00+00:00",
            "BTCUSDT",
            "bid",
            55.0,
            65.0,
            59.5,
            72.0,
            63.25,
            "v0",
            "rulebook://default/v1",
            "simulation",
        ),
    )
    run_id = conn.execute("SELECT id FROM analysis_runs LIMIT 1;").fetchone()[0]

    conn.execute(
        """
        INSERT INTO candidate_decisions(
            analysis_run_id, created_ts, decision, rationale, would_alert
        ) VALUES (?, ?, ?, ?, ?);
        """,
        (
            run_id,
            "2026-02-15T13:00:02+00:00",
            "watch_only",
            "pre_score below publish threshold",
            0,
        ),
    )

    conn.execute(
        """
        INSERT INTO screenshot_artifacts(
            analysis_run_id, timeframe, captured_ts, source_chart_url, artifact_path, artifact_hash
        ) VALUES (?, ?, ?, ?, ?, ?);
        """,
        (
            run_id,
            "1h",
            "2026-02-15T13:00:01+00:00",
            "https://www.tradingview.com/chart/example",
            "/data/artifacts/btcusdt-1h.png",
            "sha256:abc123",
        ),
    )

    joined = conn.execute(
        """
        SELECT r.symbol, d.decision, a.timeframe
        FROM analysis_runs r
        JOIN candidate_decisions d ON d.analysis_run_id = r.id
        LEFT JOIN screenshot_artifacts a ON a.analysis_run_id = r.id
        WHERE r.id = ?;
        """,
        (run_id,),
    ).fetchone()

    conn.close()
    assert joined == ("BTCUSDT", "watch_only", "1h")
