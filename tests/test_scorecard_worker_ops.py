import json

from liquidsniper.ops import scorecard_worker


def test_scorecard_worker_writes_daily_weekly_and_health(monkeypatch, tmp_path):
    artifact_root = tmp_path / "artifacts"
    health = tmp_path / "scorecard.health.json"

    monkeypatch.setenv("LIQUIDSNIPER_ARTIFACT_ROOT", str(artifact_root))
    monkeypatch.setenv("LIQUIDSNIPER_SCORECARD_HEALTH_PATH", str(health))

    scorecard_worker.main()

    payload = json.loads(health.read_text(encoding="utf-8"))
    day = payload["trading_day"]
    week = payload["trading_week"]

    assert (artifact_root / "paper_mvp" / "daily" / f"{day}.json").exists()
    assert (artifact_root / "paper_mvp" / "weekly" / f"{week}.json").exists()
    assert payload["service"] == "scorecard-worker"
    assert payload["status"] == "ok"
