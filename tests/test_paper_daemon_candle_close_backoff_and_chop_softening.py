from __future__ import annotations

import json
from datetime import datetime, timezone

from liquidsniper.core.execution_boundary import ExecutionBoundary
from liquidsniper.ops import paper_daemon


def test_close_confirm_backoff_schedule_and_timeout_without_prior_candle_fallback() -> None:
    calls: list[int] = []

    def sleep_fn(sec: float) -> None:
        calls.append(int(sec))

    def always_open(_symbol: str, *, now: datetime, cycle_count: int, policy):
        return {
            "side": "buy",
            "entry": 50000.0,
            "candle_ts": now.isoformat(),
            "candle_closed": False,
            "htf_chop": 40.0,
            "sr_first_retest": True,
            "sr_distance_bps": 10.0,
            "bos_choch": False,
            "secondary_hits": 2,
            "breakout_regime": False,
            "data_fetch_attempts": 0,
        }

    snapshot, meta = paper_daemon._confirm_candle_close_with_backoff(
        snapshot=always_open("BTCUSDT", now=datetime.now(timezone.utc), cycle_count=1, policy=paper_daemon.load_profile_policy()),
        snapshot_builder=always_open,
        symbol="BTCUSDT",
        cycle_count=1,
        policy=paper_daemon.load_profile_policy(),
        now=datetime(2026, 2, 23, 15, 0, 0, tzinfo=timezone.utc),
        sleep_fn=sleep_fn,
    )

    assert calls == [5, 10, 15]
    assert meta["close_confirm_attempts"] == 3
    assert meta["close_confirm_elapsed_sec"] == 30
    assert meta["close_confirm_timeout"] is True
    assert snapshot["candle_closed"] is False


def test_fetch_klines_retry_uses_same_endpoint_and_reports_attempts(monkeypatch) -> None:
    monkeypatch.setenv("LIQUIDSNIPER_MARKETDATA_BASE", "https://data-api.binance.vision")
    monkeypatch.setenv("LIQUIDSNIPER_DATA_FETCH_RETRY_ATTEMPTS", "3")
    monkeypatch.setenv("LIQUIDSNIPER_DATA_FETCH_RETRY_BASE_MS", "100")
    monkeypatch.setenv("LIQUIDSNIPER_DATA_FETCH_RETRY_MAX_MS", "400")

    sleeps: list[float] = []
    attempts = {"n": 0}

    def sleep_fn(sec: float) -> None:
        sleeps.append(sec)

    def flaky(symbol: str, interval: str, *, limit: int = 120):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise paper_daemon.MarketDataUnavailable("BINANCE_FETCH_FAILED:BTCUSDT:15m")
        return [{"close": 1.0, "high": 1.0, "low": 1.0, "close_time": datetime.now(timezone.utc)}] * 60

    monkeypatch.setattr(paper_daemon, "_fetch_klines", flaky)

    candles, used = paper_daemon._fetch_klines_with_retry("BTCUSDT", "15m", limit=60, sleep_fn=sleep_fn)
    assert len(candles) == 60
    assert used == 3
    assert sleeps == [0.1, 0.2]


def test_run_cycle_emits_candle_close_timeout_and_diagnostics(monkeypatch, tmp_path) -> None:
    health = tmp_path / "health.json"
    artifact_root = tmp_path / "artifacts"

    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS", "BTCUSDT")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", "true")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_SR_FIRST_RETEST", "false")
    monkeypatch.setenv("LIQUIDSNIPER_MIN_SECONDARY_HITS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_COOLDOWN_SECONDS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_DAILY_MAX_TRADES", "100")

    def never_closed(*args, **kwargs):
        return {
            "side": "buy",
            "entry": 50000.0,
            "candle_ts": "2026-02-23T15:00:00+00:00",
            "candle_closed": False,
            "htf_chop": 20.0,
            "sr_first_retest": True,
            "sr_distance_bps": 10.0,
            "bos_choch": True,
            "secondary_hits": 3,
            "breakout_regime": False,
            "data_fetch_attempts": 1,
            "data_source": "binance",
        }

    monkeypatch.setattr(paper_daemon, "_build_market_snapshot", never_closed)
    monkeypatch.setattr(paper_daemon.time, "sleep", lambda _s: None)

    boundary = ExecutionBoundary(starting_bankroll_usd=2000)
    paper_daemon.run_cycle(loop_seconds=60, health_path=health, cycle_count=1, boundary=boundary)

    run_files = list((artifact_root / "paper_mvp" / "runs").glob("*.json"))
    assert len(run_files) == 1
    payload = json.loads(run_files[0].read_text(encoding="utf-8"))
    assert payload["decision_reason_codes"] == ["CANDLE_CLOSE_TIMEOUT"]
    assert payload["close_confirm_attempts"] == 3
    assert payload["close_confirm_elapsed_sec"] == 30


def test_breakout_softening_only_when_breakout_regime_true(monkeypatch, tmp_path) -> None:
    health = tmp_path / "health.json"
    artifact_root = tmp_path / "artifacts"

    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS", "BTCUSDT,ETHUSDT")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", "false")
    monkeypatch.setenv("LIQUIDSNIPER_HTF_CHOP_MAX", "50")
    monkeypatch.setenv("LIQUIDSNIPER_HTF_CHOP_SOFTEN_POINTS", "8")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_SR_FIRST_RETEST", "false")
    monkeypatch.setenv("LIQUIDSNIPER_MIN_SECONDARY_HITS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_COOLDOWN_SECONDS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_DAILY_MAX_TRADES", "100")

    def scripted(symbol: str, **kwargs):
        breakout = symbol == "BTCUSDT"
        return {
            "side": "buy",
            "entry": 50000.0,
            "candle_ts": f"2026-02-23T15:0{'0' if breakout else '5'}:00+00:00",
            "candle_closed": True,
            "htf_chop": 55.0,
            "sr_first_retest": True,
            "sr_distance_bps": 10.0,
            "bos_choch": True,
            "secondary_hits": 3,
            "breakout_regime": breakout,
            "data_fetch_attempts": 2,
        }

    monkeypatch.setattr(paper_daemon, "_build_market_snapshot", scripted)

    boundary = ExecutionBoundary(starting_bankroll_usd=10000)
    paper_daemon.run_cycle(loop_seconds=60, health_path=health, cycle_count=1, boundary=boundary)

    payloads = [json.loads(p.read_text(encoding="utf-8")) for p in (artifact_root / "paper_mvp" / "runs").glob("*.json")]
    by_symbol = {p["symbol"]: p for p in payloads}

    assert by_symbol["BTCUSDT"]["execution_decision"] == "executed"
    assert by_symbol["BTCUSDT"]["breakout_regime"] is True
    assert by_symbol["BTCUSDT"]["htf_chop_mode"] == "breakout_softened"
    assert by_symbol["BTCUSDT"]["htf_chop_threshold_effective"] == 58.0

    assert by_symbol["ETHUSDT"]["proposal_decision"] == "rejected"
    assert "HTF_CHOP_BLOCKED" in by_symbol["ETHUSDT"]["decision_reason_codes"]
    assert by_symbol["ETHUSDT"]["breakout_regime"] is False
    assert by_symbol["ETHUSDT"]["htf_chop_mode"] == "strict"
