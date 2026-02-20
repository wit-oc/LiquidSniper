import json

import pytest

from liquidsniper.ops import paper_daemon


def test_paper_daemon_rejects_non_paper_mode(monkeypatch):
    monkeypatch.setenv("LIQUIDSNIPER_MODE", "live")
    with pytest.raises(RuntimeError, match="only supports"):
        paper_daemon.main()


def test_paper_daemon_writes_health_in_run_once(monkeypatch, tmp_path):
    health = tmp_path / "paper.health.json"
    monkeypatch.setenv("LIQUIDSNIPER_MODE", "paper")
    monkeypatch.setenv("LIQUIDSNIPER_RUN_ONCE", "true")
    monkeypatch.setenv("LIQUIDSNIPER_LOOP_SECONDS", "3")
    monkeypatch.setenv("LIQUIDSNIPER_HEALTH_PATH", str(health))

    paper_daemon.main()

    payload = json.loads(health.read_text(encoding="utf-8"))
    assert payload["service"] == "paper-runner"
    assert payload["status"] == "ok"
    assert payload["cycle_count"] == 1
