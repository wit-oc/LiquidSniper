"""Tests for simulation-first alerting helpers."""

from __future__ import annotations

from pathlib import Path

from liquidsniper.core.analysis_engine import Decision
from liquidsniper.core.db import init_db
from liquidsniper.core.simulation_mode import (
    AlertingConfig,
    persist_decision,
    query_candidates_per_day,
    query_high_priority_per_day,
    query_symbol_concentration,
    should_send_alert,
)


def test_alerting_config_defaults_to_simulation(monkeypatch) -> None:
    monkeypatch.delenv("ALERTS_ENABLED", raising=False)
    monkeypatch.delenv("ALERTS_SIMULATION", raising=False)

    config = AlertingConfig.from_env()

    assert config.alerts_enabled is False
    assert config.alerts_simulation is True
    assert config.run_mode == "simulation"


def test_should_send_alert_requires_live_mode() -> None:
    assert (
        should_send_alert(
            Decision.PUBLISH_CANDIDATE,
            AlertingConfig(alerts_enabled=False, alerts_simulation=True),
        )
        is False
    )
    assert (
        should_send_alert(
            Decision.PUBLISH_CANDIDATE,
            AlertingConfig(alerts_enabled=True, alerts_simulation=False),
        )
        is True
    )


def test_persist_decision_and_metric_queries(tmp_path: Path) -> None:
    conn = init_db(str(tmp_path / "liquidsniper.sqlite"))

    sim_cfg = AlertingConfig(alerts_enabled=False, alerts_simulation=True)
    live_cfg = AlertingConfig(alerts_enabled=True, alerts_simulation=False)

    persist_decision(
        conn,
        symbol="BTCUSDT",
        side="bid",
        zone_priority_score=70.0,
        context_score=72.0,
        pre_score=70.9,
        agent_confidence_score=75.0,
        final_score=72.13,
        decision=Decision.PUBLISH_CANDIDATE,
        rationale="qualified candidate",
        config=sim_cfg,
    )
    persist_decision(
        conn,
        symbol="ETHUSDT",
        side="ask",
        zone_priority_score=78.0,
        context_score=82.0,
        pre_score=79.8,
        agent_confidence_score=92.0,
        final_score=83.46,
        decision=Decision.PUBLISH_CANDIDATE,
        rationale="high-priority candidate",
        config=live_cfg,
    )
    persist_decision(
        conn,
        symbol="BTCUSDT",
        side="unknown",
        zone_priority_score=40.0,
        context_score=52.0,
        pre_score=45.4,
        agent_confidence_score=0.0,
        final_score=31.78,
        decision=Decision.WATCH_ONLY,
        rationale="below pre-score floor",
        config=sim_cfg,
    )

    run_modes = [
        row[0]
        for row in conn.execute("SELECT run_mode FROM analysis_runs ORDER BY id;").fetchall()
    ]
    would_alert = [
        row[0]
        for row in conn.execute(
            "SELECT would_alert FROM candidate_decisions ORDER BY id;"
        ).fetchall()
    ]

    candidates_per_day = query_candidates_per_day(conn)
    high_priority_per_day = query_high_priority_per_day(conn)
    symbol_concentration = query_symbol_concentration(conn)

    conn.close()

    assert run_modes == ["simulation", "live", "simulation"]
    assert would_alert == [1, 1, 0]
    assert candidates_per_day[0][1] == 2
    assert high_priority_per_day[0][1] == 1
    assert symbol_concentration == [("BTCUSDT", 1), ("ETHUSDT", 1)]
