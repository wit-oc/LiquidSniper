import json

from liquidsniper.core.execution_boundary import ExecutionBoundary
from liquidsniper.ops import paper_daemon


def test_smoke_trade_frequency_and_expected_rejects(monkeypatch, tmp_path):
    artifact_root = tmp_path / "artifacts"
    health = tmp_path / "health.json"

    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setenv("LIQUIDSNIPER_PROFILE_ID", "I")
    monkeypatch.setenv("LIQUIDSNIPER_POLICY_VERSION", "v1")
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS", "BTCUSDT,ETHUSDT")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", "true")
    monkeypatch.setenv("LIQUIDSNIPER_HTF_CHOP_MAX", "50")
    monkeypatch.setenv("LIQUIDSNIPER_MIN_SECONDARY_HITS", "2")
    monkeypatch.setenv("LIQUIDSNIPER_COOLDOWN_SECONDS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_DAILY_MAX_TRADES", "100")
    monkeypatch.setenv("LIQUIDSNIPER_ENFORCE_ONE_OPEN_POSITION", "true")

    def scripted_snapshot(symbol: str, *, cycle_count: int, **kwargs):
        pass_gate = (cycle_count % 2 == 0) and (symbol == "BTCUSDT")
        return {
            "candle_ts": f"2026-02-20T14:{(cycle_count % 12) * 5:02d}:00+00:00",
            "candle_closed": pass_gate,
            "htf_chop": 30.0 if pass_gate else 65.0,
            "sr_first_retest": pass_gate,
            "bos_choch": pass_gate,
            "secondary_hits": 3 if pass_gate else 0,
        }

    monkeypatch.setattr(paper_daemon, "_build_market_snapshot", scripted_snapshot)

    boundary = ExecutionBoundary(starting_bankroll_usd=5000)
    for cycle in range(1, 9):
        paper_daemon.run_cycle(loop_seconds=60, health_path=health, cycle_count=cycle, boundary=boundary)

    run_files = list((artifact_root / "paper_mvp" / "runs").glob("*.json"))
    attempted = 8 * 2
    execution_rate = len(run_files) / attempted

    assert 0.1 <= execution_rate <= 0.6
    # At least one rejection should have occurred from strict gate profile.
    state_path = artifact_root / "paper_mvp" / "state" / "execution_throttle_state.json"
    assert state_path.exists()
    health_payload = json.loads(health.read_text(encoding="utf-8"))
    assert health_payload["cycle_stats"]["blocked"] >= 1
