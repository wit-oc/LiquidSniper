import json
from datetime import datetime, timezone

from liquidsniper.core.execution_boundary import ExecutionBoundary
from liquidsniper.ops import paper_daemon


def test_lane_close_boundary_divisibility_routes_expected_lanes():
    assert paper_daemon._lane_should_run(strategy="scalp", tick_index=100)
    assert not paper_daemon._lane_should_run(strategy="intraday", tick_index=100)
    assert not paper_daemon._lane_should_run(strategy="swing", tick_index=100)

    assert paper_daemon._lane_should_run(strategy="scalp", tick_index=102)
    assert paper_daemon._lane_should_run(strategy="intraday", tick_index=102)
    assert not paper_daemon._lane_should_run(strategy="swing", tick_index=102)

    assert paper_daemon._lane_should_run(strategy="scalp", tick_index=108)
    assert paper_daemon._lane_should_run(strategy="intraday", tick_index=108)
    assert paper_daemon._lane_should_run(strategy="swing", tick_index=108)


def test_base_tick_index_and_sleep_honor_exchange_offset():
    now = datetime(2026, 2, 23, 15, 4, 58, tzinfo=timezone.utc)

    # +2s exchange offset means exchange time is exactly at 5m boundary.
    assert paper_daemon._base_tick_index(now, offset_ms=2000) != paper_daemon._base_tick_index(now, offset_ms=0)
    assert paper_daemon._seconds_until_next_base_tick(now, offset_ms=2000) == paper_daemon.BASE_TICK_SECONDS
    assert paper_daemon._seconds_until_next_base_tick(now, offset_ms=0) == 2


def test_parallel_cycle_skips_preclose_without_block_noise(monkeypatch, tmp_path):
    health = tmp_path / "health.json"

    monkeypatch.setenv("LIQUIDSNIPER_PAPER_PARALLEL_STRATEGIES", "scalp,intraday,swing")
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS_SCALP", "BTCUSDT")
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS_INTRADAY", "ETHUSDT")
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS_SWING", "SOLUSDT")

    calls: list[str] = []

    def fake_lane_cycle(*, strategy: str, symbols, **kwargs):
        calls.append(strategy)
        return {"attempted": len(symbols), "executed": 0, "blocked": 0}

    monkeypatch.setattr(paper_daemon, "_run_lane_cycle", fake_lane_cycle)

    boundaries = {"scalp": ExecutionBoundary(), "intraday": ExecutionBoundary(), "swing": ExecutionBoundary()}
    paper_daemon.run_cycle_parallel(
        loop_seconds=paper_daemon.BASE_TICK_SECONDS,
        health_path=health,
        cycle_count=1,
        lane_boundaries=boundaries,
        lane_run_flags={"scalp": True, "intraday": False, "swing": False},
    )

    assert calls == ["scalp"]

    payload = json.loads(health.read_text(encoding="utf-8"))
    assert payload["cycle_stats"]["attempted"] == 1
    assert payload["cycle_stats"]["blocked"] == 0
    assert payload["cycle_stats"]["skipped_preclose"] == 2

    lanes = {lane["strategy"]: lane for lane in payload["lanes"]}
    assert lanes["intraday"]["attempted"] == 0
    assert lanes["intraday"]["blocked"] == 0
    assert lanes["intraday"]["skipped_preclose"] == 1
