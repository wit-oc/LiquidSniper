import json

import pytest

from liquidsniper.ops import paper_daemon


def test_paper_daemon_rejects_non_paper_mode(monkeypatch):
    monkeypatch.setenv("LIQUIDSNIPER_MODE", "live")
    with pytest.raises(RuntimeError, match="only supports"):
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
    monkeypatch.setenv("LIQUIDSNIPER_SYMBOLS", "BTCUSDT,ETHUSDT")
    monkeypatch.setenv("LIQUIDSNIPER_PAPER_BANKROLL_USD", "2000")

    paper_daemon.main()

    payload = json.loads(health.read_text(encoding="utf-8"))
    assert payload["service"] == "paper-runner"
    assert payload["status"] == "ok"
    assert payload["cycle_count"] == 1
    assert payload["cycle_stats"]["attempted"] == 2
    assert payload["cycle_stats"]["executed"] >= 1

    runs_dir = artifact_root / "paper_mvp" / "runs"
    assert runs_dir.exists()
    run_files = list(runs_dir.glob("*.json"))
    assert len(run_files) >= 1
