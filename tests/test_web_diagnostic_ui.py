"""Tests for minimal diagnostic UI query helpers."""

from __future__ import annotations

from pathlib import Path

from liquidsniper.core.analysis_engine import Decision
from liquidsniper.core.db import init_db
from liquidsniper.core.simulation_mode import AlertingConfig, persist_decision
from liquidsniper.web.app import query_diagnostic_cards


def _seed_run(
    conn,
    *,
    symbol: str,
    decision: Decision,
    final_score: float,
) -> int:
    return persist_decision(
        conn,
        symbol=symbol,
        side="bid",
        zone_priority_score=70.0,
        context_score=68.0,
        pre_score=69.0,
        agent_confidence_score=80.0,
        final_score=final_score,
        decision=decision,
        rationale=f"{symbol} rationale",
        config=AlertingConfig(alerts_enabled=False, alerts_simulation=True),
    )


def test_query_diagnostic_cards_supports_would_alert_and_score_filters(tmp_path: Path) -> None:
    conn = init_db(str(tmp_path / "liquidsniper.sqlite"))

    _seed_run(
        conn,
        symbol="BTCUSDT",
        decision=Decision.PUBLISH_CANDIDATE,
        final_score=82.0,
    )
    _seed_run(
        conn,
        symbol="ETHUSDT",
        decision=Decision.WATCH_ONLY,
        final_score=64.0,
    )

    cards = query_diagnostic_cards(
        conn,
        would_alert_only=True,
        min_final_score=80.0,
        status="all",
    )

    conn.close()

    assert len(cards) == 1
    assert cards[0].symbol == "BTCUSDT"
    assert cards[0].would_alert is True


def test_query_diagnostic_cards_filters_by_status(tmp_path: Path) -> None:
    conn = init_db(str(tmp_path / "liquidsniper.sqlite"))

    _seed_run(
        conn,
        symbol="SOLUSDT",
        decision=Decision.REJECT,
        final_score=61.0,
    )
    _seed_run(
        conn,
        symbol="XRPUSDT",
        decision=Decision.PUBLISH_CANDIDATE,
        final_score=79.0,
    )

    cards = query_diagnostic_cards(
        conn,
        status="reject",
    )

    conn.close()

    assert len(cards) == 1
    assert cards[0].decision == "reject"
    assert cards[0].symbol == "SOLUSDT"
