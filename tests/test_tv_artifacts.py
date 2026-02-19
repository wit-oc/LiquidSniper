"""Tests for TradingView screenshot artifact helpers."""

from __future__ import annotations

from pathlib import Path

from liquidsniper.core.db import init_db
from liquidsniper.core.tv_artifacts import (
    ArtifactMountContract,
    insert_screenshot_artifact,
    query_ui_artifact_links,
)


def test_query_ui_artifact_links_maps_writer_paths_to_ui_mount(tmp_path: Path) -> None:
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
            66.0,
            70.0,
            68.0,
            75.0,
            70.0,
            "v0",
            "rulebook://default/v1",
            "simulation",
        ),
    )
    run_id = conn.execute("SELECT id FROM analysis_runs LIMIT 1;").fetchone()[0]

    insert_screenshot_artifact(
        conn,
        analysis_run_id=run_id,
        timeframe="15m",
        captured_ts="2026-02-15T13:00:01+00:00",
        source_chart_url="https://www.tradingview.com/chart/foo",
        artifact_path="/data/artifacts/tradingview/snapshots/BTCUSDT_15m.png",
        artifact_hash="sha256:aaa",
    )
    insert_screenshot_artifact(
        conn,
        analysis_run_id=run_id,
        timeframe="1h",
        captured_ts="2026-02-15T13:00:02+00:00",
        source_chart_url="https://www.tradingview.com/chart/foo",
        artifact_path="/data/artifacts/tradingview/snapshots/BTCUSDT_1h.png",
        artifact_hash="sha256:bbb",
    )

    links = query_ui_artifact_links(conn, analysis_run_id=run_id)

    conn.close()

    assert links["15m"] == "/artifacts/tradingview/snapshots/BTCUSDT_15m.png"
    assert links["1h"] == "/artifacts/tradingview/snapshots/BTCUSDT_1h.png"
    assert links["4h"] is None
    assert links["1D"] is None
    assert links["1W"] is None


def test_to_ui_href_falls_back_for_non_mounted_paths() -> None:
    contract = ArtifactMountContract()
    assert contract.to_ui_href("/tmp/random.png") == "/tmp/random.png"
