"""Tests for minimal diagnostic UI query helpers."""

from __future__ import annotations

from pathlib import Path

from liquidsniper.core.analysis_engine import Decision
from liquidsniper.core.db import init_db
from liquidsniper.core.simulation_mode import AlertingConfig, persist_decision
from liquidsniper.web.app import _build_ui_pair_analytics, query_diagnostic_cards


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


def test_build_ui_pair_analytics_loads_available_structure_timeframes(monkeypatch) -> None:
    calls: list[tuple[str, int]] = []

    def fake_find(symbol: str, tf: str):
        return Path(f"/tmp/{symbol.lower()}_{tf.lower()}.csv") if tf == "1D" else None

    def fake_load(path: Path, *, limit: int = 600):
        calls.append((path.name, limit))
        return [{"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5} for _ in range(8)]

    def fake_build(*, symbol: str, profile_id: str, entry: float, zones: list[dict], candles_by_tf: dict[str, list[dict]]):
        return {
            "symbol": symbol,
            "profile_id": profile_id,
            "entry": entry,
            "zone_count": len(zones),
            "market_structure": {"available_timeframes": sorted(candles_by_tf.keys())},
        }

    monkeypatch.setattr("liquidsniper.web.app._find_market_structure_csv", fake_find)
    monkeypatch.setattr("liquidsniper.web.app.load_candles_from_csv", fake_load)
    monkeypatch.setattr("liquidsniper.web.app.build_pair_analytics_snapshot", fake_build)

    payload = _build_ui_pair_analytics(
        symbol="BTCUSDT",
        profile="I",
        entry=100.0,
        zones=[{"zone_id": "z1"}, {"zone_id": "z2"}],
    )

    assert payload["symbol"] == "BTCUSDT"
    assert payload["profile_id"] == "I"
    assert payload["entry"] == 100.0
    assert payload["zone_count"] == 2
    assert payload["market_structure"]["available_timeframes"] == ["1D"]
    assert calls == [("btcusdt_1d.csv", 600)]
