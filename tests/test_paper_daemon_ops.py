import json

import pytest

from liquidsniper.core.execution_boundary import ExecutionBoundary
from liquidsniper.ops import paper_daemon


def test_paper_daemon_rejects_non_paper_mode(monkeypatch):
    monkeypatch.setenv("LIQUIDSNIPER_MODE", "live")
    with pytest.raises(RuntimeError, match="MODE_GUARD_PAPER_DAEMON_REQUIRES_PAPER"):
        paper_daemon.main()


def test_paper_daemon_writes_health_and_run_artifacts_in_run_once(monkeypatch, tmp_path):
    health = tmp_path / "paper.health.json"
    artifact_root = tmp_path / "artifacts"

    monkeypatch.setenv("LIQUIDSNIPER_MODE", "paper")
    monkeypatch.setenv("LIQUIDSNIPER_RUN_ONCE", "true")
    monkeypatch.setenv("LIQUIDSNIPER_LOOP_SECONDS", "3")
    monkeypatch.setenv("LIQUIDSNIPER_HEALTH_PATH", str(health))
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setenv("LIQUIDSNIPER_PROFILE_MODE", "intraday_only")
    monkeypatch.setenv("LIQUIDSNIPER_PROFILE_ID", "I")
    monkeypatch.setenv("LIQUIDSNIPER_POLICY_VERSION", "v1")
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS", "BTCUSDT")
    monkeypatch.setenv("LIQUIDSNIPER_PAPER_BANKROLL_USD", "2000")
    monkeypatch.setenv("LIQUIDSNIPER_DATA_SOURCE", "mock")

    # Permissive gates for deterministic acceptance.
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", "false")
    monkeypatch.setenv("LIQUIDSNIPER_HTF_CHOP_MAX", "100")
    monkeypatch.setenv("LIQUIDSNIPER_MIN_SECONDARY_HITS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_SR_FIRST_RETEST", "false")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_BOS_CHOCH", "false")
    monkeypatch.setenv("LIQUIDSNIPER_COOLDOWN_SECONDS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_DAILY_MAX_TRADES", "100")
    monkeypatch.setenv("LIQUIDSNIPER_ENFORCE_ONE_OPEN_POSITION", "false")

    paper_daemon.main()

    payload = json.loads(health.read_text(encoding="utf-8"))
    assert payload["service"] == "paper-runner"
    assert payload["status"] == "ok"
    assert payload["cycle_count"] == 1
    assert payload["cycle_stats"]["attempted"] == 1
    assert payload["cycle_stats"]["executed"] == 1

    runs_dir = artifact_root / "paper_mvp" / "runs"
    assert runs_dir.exists()
    run_files = list(runs_dir.glob("*.json"))
    assert len(run_files) == 1

    run_payload = json.loads(run_files[0].read_text(encoding="utf-8"))
    assert isinstance(run_payload["gate_checks"], dict)
    assert isinstance(run_payload["policy_snapshot"], dict)
    assert isinstance(run_payload["candle_timestamp"], str)


def test_run_cycle_persists_idempotency_and_blocks_duplicate(monkeypatch, tmp_path):
    health = tmp_path / "paper.health.json"
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setenv("LIQUIDSNIPER_PROFILE_ID", "I")
    monkeypatch.setenv("LIQUIDSNIPER_POLICY_VERSION", "v1")
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS", "BTCUSDT")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", "false")
    monkeypatch.setenv("LIQUIDSNIPER_HTF_CHOP_MAX", "100")
    monkeypatch.setenv("LIQUIDSNIPER_MIN_SECONDARY_HITS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_SR_FIRST_RETEST", "false")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_BOS_CHOCH", "false")
    monkeypatch.setenv("LIQUIDSNIPER_COOLDOWN_SECONDS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_DAILY_MAX_TRADES", "100")
    monkeypatch.setenv("LIQUIDSNIPER_ENFORCE_ONE_OPEN_POSITION", "false")

    def fixed_snapshot(*args, **kwargs):
        return {
            "side": "buy",
            "entry": 50000.0,
            "candle_ts": "2026-02-20T14:30:00+00:00",
            "candle_closed": True,
            "htf_chop": 25.0,
            "sr_first_retest": True,
            "bos_choch": True,
            "secondary_hits": 3,
        }

    monkeypatch.setattr(paper_daemon, "_build_market_snapshot", fixed_snapshot)

    boundary = ExecutionBoundary(starting_bankroll_usd=2000)
    paper_daemon.run_cycle(loop_seconds=3, health_path=health, cycle_count=1, boundary=boundary)
    paper_daemon.run_cycle(loop_seconds=3, health_path=health, cycle_count=2, boundary=boundary)

    payload = json.loads(health.read_text(encoding="utf-8"))
    assert payload["cycle_stats"]["attempted"] == 1
    assert payload["cycle_stats"]["blocked"] == 1

    state_path = artifact_root / "paper_mvp" / "state" / "execution_throttle_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["executed_today"] == 1
    assert "realized_pnl_today_usd" in state
    assert len(state["seen_idempotency_keys"]) == 1


def test_fetch_klines_rejects_non_https_or_unapproved_host(monkeypatch):
    monkeypatch.setenv("LIQUIDSNIPER_MARKETDATA_BASE", "http://example.com")
    with pytest.raises(paper_daemon.MarketDataUnavailable, match="BINANCE_BASE_URL_INVALID"):
        paper_daemon._fetch_klines("BTCUSDT", "15m", limit=5)

    monkeypatch.setenv("LIQUIDSNIPER_MARKETDATA_BASE", "https://evil.example")
    with pytest.raises(paper_daemon.MarketDataUnavailable, match="BINANCE_BASE_URL_INVALID"):
        paper_daemon._fetch_klines("BTCUSDT", "15m", limit=5)


def test_daily_loss_circuit_breaker_halts_remaining_trades(monkeypatch, tmp_path):
    health = tmp_path / "paper.health.json"
    artifact_root = tmp_path / "artifacts"

    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setenv("LIQUIDSNIPER_PROFILE_ID", "I")
    monkeypatch.setenv("LIQUIDSNIPER_POLICY_VERSION", "v1")
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS", "BTCUSDT,ETHUSDT")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", "false")
    monkeypatch.setenv("LIQUIDSNIPER_HTF_CHOP_MAX", "100")
    monkeypatch.setenv("LIQUIDSNIPER_MIN_SECONDARY_HITS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_SR_FIRST_RETEST", "false")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_BOS_CHOCH", "false")
    monkeypatch.setenv("LIQUIDSNIPER_COOLDOWN_SECONDS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_DAILY_MAX_TRADES", "100")
    monkeypatch.setenv("LIQUIDSNIPER_ENFORCE_ONE_OPEN_POSITION", "false")
    monkeypatch.setenv("LIQUIDSNIPER_MAX_DAILY_LOSS_USD", "5")

    def fixed_snapshot(*args, **kwargs):
        return {
            "side": "buy",
            "entry": 50000.0,
            "candle_ts": "2026-02-20T14:30:00+00:00",
            "candle_closed": True,
            "htf_chop": 25.0,
            "sr_first_retest": True,
            "bos_choch": True,
            "secondary_hits": 3,
        }

    monkeypatch.setattr(paper_daemon, "_build_market_snapshot", fixed_snapshot)

    original_build_proposal = paper_daemon._build_proposal

    def negative_pnl_proposal(*args, **kwargs):
        proposal, policy = original_build_proposal(*args, **kwargs)
        proposal["pnl_usd"] = -10.0
        return proposal, policy

    monkeypatch.setattr(paper_daemon, "_build_proposal", negative_pnl_proposal)

    boundary = ExecutionBoundary(starting_bankroll_usd=2000)
    paper_daemon.run_cycle(loop_seconds=3, health_path=health, cycle_count=1, boundary=boundary)

    payload = json.loads(health.read_text(encoding="utf-8"))
    assert payload["cycle_stats"]["attempted"] == 2
    # Entry fills no longer realize PnL immediately; closes realize PnL when SL/BE/TP exits occur.
    assert payload["cycle_stats"]["executed"] == 2
    assert payload["cycle_stats"]["blocked"] == 0

    state_path = artifact_root / "paper_mvp" / "state" / "execution_throttle_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["realized_pnl_today_usd"] == 0.0
