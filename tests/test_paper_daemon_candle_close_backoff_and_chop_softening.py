from __future__ import annotations

import json
from datetime import datetime, timezone

from liquidsniper.core.execution_boundary import ExecutionBoundary
from liquidsniper.ops import paper_daemon


def test_htf_chop_components_bounded_and_trend_sensitive() -> None:
    closes_trend = [100 + i for i in range(40)]
    highs_trend = [c + 0.5 for c in closes_trend]
    lows_trend = [c - 0.5 for c in closes_trend]

    trend = paper_daemon._compute_htf_chop_components(closes_trend, highs_trend, lows_trend, lookback=14)
    assert 0.0 <= trend["ci"] <= 100.0
    assert 0.0 <= trend["er"] <= 100.0
    assert 0.0 <= trend["norm"] <= 100.0

    closes_chop = [100 + (1 if i % 2 == 0 else -1) for i in range(40)]
    highs_chop = [max(c, closes_chop[max(0, i - 1)]) + 0.4 for i, c in enumerate(closes_chop)]
    lows_chop = [min(c, closes_chop[max(0, i - 1)]) - 0.4 for i, c in enumerate(closes_chop)]
    chop = paper_daemon._compute_htf_chop_components(closes_chop, highs_chop, lows_chop, lookback=14)

    assert chop["norm"] > trend["norm"]


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


def test_close_confirm_succeeds_on_second_retry_for_same_target_candle() -> None:
    calls: list[int] = []
    seen_targets: list[str] = []

    def sleep_fn(sec: float) -> None:
        calls.append(int(sec))

    def flips_closed(_symbol: str, *, now: datetime, cycle_count: int, policy, target_close_ts: str = ""):
        seen_targets.append(target_close_ts)
        return {
            "side": "buy",
            "entry": 50000.0,
            "candle_ts": target_close_ts or now.isoformat(),
            "candle_closed": len(calls) >= 2,
            "target_open_ts": "2026-02-23T14:45:00+00:00",
            "target_close_ts": "2026-02-23T15:00:00+00:00",
            "matched_candle_open_ts": "2026-02-23T14:45:00+00:00" if len(calls) >= 2 else None,
            "htf_chop": 40.0,
            "sr_first_retest": True,
            "sr_distance_bps": 10.0,
            "bos_choch": False,
            "secondary_hits": 2,
            "breakout_regime": False,
            "data_fetch_attempts": 0,
        }

    initial = flips_closed(
        "BTCUSDT",
        now=datetime.now(timezone.utc),
        cycle_count=1,
        policy=paper_daemon.load_profile_policy(),
        target_close_ts="2026-02-23T15:00:00+00:00",
    )
    snapshot, meta = paper_daemon._confirm_candle_close_with_backoff(
        snapshot=initial,
        snapshot_builder=flips_closed,
        symbol="BTCUSDT",
        cycle_count=1,
        policy=paper_daemon.load_profile_policy(),
        now=datetime(2026, 2, 23, 15, 0, 0, tzinfo=timezone.utc),
        sleep_fn=sleep_fn,
    )

    assert calls == [5, 10]
    assert meta["close_confirm_attempts"] == 2
    assert meta["close_confirm_elapsed_sec"] == 15
    assert meta["close_confirm_timeout"] is False
    assert snapshot["candle_closed"] is True
    assert all(ts == "2026-02-23T15:00:00+00:00" for ts in seen_targets)


def test_target_candle_selection_and_alignment_helpers() -> None:
    now = datetime(2026, 2, 23, 15, 0, 2, tzinfo=timezone.utc)
    open_ts, close_ts = paper_daemon._target_candle_window(now=now, tf_minutes=15, offset_ms=0)
    assert open_ts == datetime(2026, 2, 23, 14, 45, 0, tzinfo=timezone.utc)
    assert close_ts == datetime(2026, 2, 23, 15, 0, 0, tzinfo=timezone.utc)

    candles = [
        {"open_time": datetime(2026, 2, 23, 14, 30, 0, tzinfo=timezone.utc), "close": 1.0},
        {"open_time": datetime(2026, 2, 23, 14, 45, 0, tzinfo=timezone.utc), "close": 2.0},
    ]
    matched = paper_daemon._select_candle_by_open_time(candles, target_open=open_ts)
    assert matched is not None
    assert matched["close"] == 2.0


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
            "target_open_ts": "2026-02-23T14:45:00+00:00",
            "target_close_ts": "2026-02-23T15:00:00+00:00",
            "matched_candle_open_ts": None,
            "exchange_offset_ms": 0,
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
    assert payload["target_open_ts"] == "2026-02-23T14:45:00+00:00"
    assert payload["target_close_ts"] == "2026-02-23T15:00:00+00:00"
    assert payload["matched_candle_open_ts"] is None


def test_soft_hard_chop_mode_with_breakout_only_relaxing_sr(monkeypatch, tmp_path) -> None:
    health = tmp_path / "health.json"
    artifact_root = tmp_path / "artifacts"

    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS", "BTCUSDT,ETHUSDT")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", "false")
    monkeypatch.setenv("LIQUIDSNIPER_HTF_CHOP_SOFT_MAX", "50")
    monkeypatch.setenv("LIQUIDSNIPER_HTF_CHOP_HARD_MAX", "58")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_SR_FIRST_RETEST", "true")
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
            "sr_first_retest": breakout,
            "sr_retest_mode": "near_breakout" if breakout else "none",
            "sr_near_retest_used": breakout,
            "sr_penalty": 0.4 if breakout else 0.0,
            "sr_distance_bps": 25.0,
            "bos_choch": True,
            "secondary_hits": 3,
            "breakout_regime": breakout,
            "breakout_window_ok": breakout,
            "htf_chop_ci": 55.0,
            "htf_chop_er": 55.0,
            "htf_chop_norm": 55.0,
            "htf_chop_penalty": 0.0,
            "data_fetch_attempts": 2,
        }

    monkeypatch.setattr(paper_daemon, "_build_market_snapshot", scripted)

    boundary = ExecutionBoundary(starting_bankroll_usd=10000)
    paper_daemon.run_cycle(loop_seconds=60, health_path=health, cycle_count=1, boundary=boundary)

    payloads = [json.loads(p.read_text(encoding="utf-8")) for p in (artifact_root / "paper_mvp" / "runs").glob("*.json")]
    by_symbol = {p["symbol"]: p for p in payloads}

    assert by_symbol["BTCUSDT"]["execution_decision"] == "executed"
    assert by_symbol["BTCUSDT"]["breakout_regime"] is True
    assert by_symbol["BTCUSDT"]["htf_chop_mode"] == "soft_hard"
    assert by_symbol["BTCUSDT"]["htf_chop_threshold_effective"] == 58.0
    assert by_symbol["BTCUSDT"]["sr_retest_mode"] == "near_breakout"
    assert by_symbol["BTCUSDT"]["sr_near_retest_used"] is True

    assert by_symbol["ETHUSDT"]["proposal_decision"] == "rejected"
    assert "RETEST_REQUIRED" in by_symbol["ETHUSDT"]["decision_reason_codes"]
    assert by_symbol["ETHUSDT"]["breakout_regime"] is False
    assert by_symbol["ETHUSDT"]["htf_chop_mode"] == "soft_hard"
