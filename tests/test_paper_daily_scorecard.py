import json
from pathlib import Path

from liquidsniper.core.paper_artifacts import build_daily_scorecard, persist_daily_scorecard


DAY = "2026-02-19"


def _run(**overrides):
    base = {
        "run_id": "run-x",
        "timestamp": f"{DAY}T14:00:00Z",
        "proposal_decision": "accepted",
        "execution_decision": "executed",
        "pnl_r": 0.8,
        "decision_reason_codes": [],
        "feed_state": "ok",
        "feed_reason_codes": [],
    }
    base.update(overrides)
    return base


def test_build_daily_scorecard_aggregates_expectancy_rejects_and_feed_health():
    runs = [
        _run(run_id="run-1", pnl_r=1.2),
        _run(run_id="run-2", pnl_r=-0.6, feed_state="degraded", feed_reason_codes=["FRESHNESS_GAP"]),
        _run(
            run_id="run-3",
            proposal_decision="rejected",
            execution_decision="blocked",
            pnl_r=None,
            decision_reason_codes=["SCORE_BELOW_MIN", "POLICY_REJECTED"],
            feed_state="tripped",
            feed_reason_codes=["RATE_LIMIT_HIT"],
        ),
    ]

    out = build_daily_scorecard(trading_day=DAY, runs=runs)

    assert out["date"] == DAY
    assert out["runs_total"] == 3
    assert out["accepted"] == 2
    assert out["executed"] == 2
    assert out["rejected"] == 1
    assert out["expectancy_r"] == 0.3
    assert out["win_rate"] == 0.5
    assert out["profit_factor"] == 2.0
    assert out["reject_reason_distribution"] == {"POLICY_REJECTED": 1, "SCORE_BELOW_MIN": 1}
    assert out["top_reject_reasons"][0]["code"] == "POLICY_REJECTED"

    feed = out["feed_health"]
    assert feed["freshness_pct"] == 0.3333
    assert feed["gap_rate"] == 0.3333
    assert feed["rate_limit_rate"] == 0.3333
    assert feed["feed_state_distribution"] == {"degraded": 1, "ok": 1, "tripped": 1}


def test_persist_daily_scorecard_reads_runs_for_day_and_writes_json(tmp_path: Path):
    runs_dir = tmp_path / "paper_mvp" / "runs"
    runs_dir.mkdir(parents=True)

    (runs_dir / "run-in-day.json").write_text(
        json.dumps(_run(run_id="run-in-day", pnl_r=0.4), sort_keys=True),
        encoding="utf-8",
    )
    (runs_dir / "run-other-day.json").write_text(
        json.dumps(_run(run_id="run-other-day", timestamp="2026-02-18T14:00:00Z", pnl_r=5.0), sort_keys=True),
        encoding="utf-8",
    )

    payload, path = persist_daily_scorecard(trading_day=DAY, artifact_root=tmp_path)

    assert path == tmp_path / "paper_mvp" / "daily" / f"{DAY}.json"
    assert path.exists()
    assert payload["runs_total"] == 1
    assert payload["expectancy_r"] == 0.4

    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk == payload
