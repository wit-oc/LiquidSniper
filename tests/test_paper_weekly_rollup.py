import json
from pathlib import Path

from liquidsniper.core.paper_artifacts import build_weekly_rollup, persist_weekly_rollup


WEEK = "2026-W08"


def _run(**overrides):
    base = {
        "run_id": "run-x",
        "timestamp": "2026-02-19T14:00:00Z",
        "proposal_decision": "accepted",
        "execution_decision": "executed",
        "pnl_r": 0.8,
        "decision_reason_codes": [],
        "feed_state": "ok",
        "feed_reason_codes": [],
    }
    base.update(overrides)
    return base


def test_build_weekly_rollup_aggregates_and_computes_hold_posture_for_small_sample():
    runs = [
        _run(run_id="run-1", pnl_r=1.2),
        _run(run_id="run-2", pnl_r=-0.6, feed_state="degraded", feed_reason_codes=["FRESHNESS_GAP"]),
        _run(
            run_id="run-3",
            proposal_decision="rejected",
            execution_decision="blocked",
            pnl_r=None,
            decision_reason_codes=["SCORE_BELOW_MIN"],
            feed_state="tripped",
            feed_reason_codes=["RATE_LIMIT_HIT"],
        ),
    ]

    out = build_weekly_rollup(trading_week=WEEK, runs=runs)

    assert out["week"] == WEEK
    assert out["runs_total"] == 3
    assert out["accepted"] == 2
    assert out["executed"] == 2
    assert out["rejected"] == 1
    assert out["expectancy_r"] == 0.3
    assert out["win_rate"] == 0.5
    assert out["profit_factor"] == 2.0
    assert out["reject_reason_distribution"] == {"SCORE_BELOW_MIN": 1}

    feed = out["feed_health"]
    assert feed["freshness_pct"] == 0.3333
    assert feed["gap_rate"] == 0.3333
    assert feed["rate_limit_rate"] == 0.3333

    posture = out["posture"]
    assert posture["recommendation"] == "HOLD"
    blocker_codes = [row["code"] for row in posture["top_blockers"]]
    assert "SAMPLE_TOO_SMALL" in blocker_codes


def test_build_weekly_rollup_includes_bankroll_summary_when_present():
    out = build_weekly_rollup(
        trading_week=WEEK,
        runs=[
            _run(
                run_id="run-1",
                timestamp="2026-02-17T10:00:00Z",
                bankroll={"starting_equity_usd": 1000, "available_usd": 1005, "reserved_risk_usd": 0, "realized_pnl_usd": 5},
            ),
            _run(
                run_id="run-2",
                timestamp="2026-02-18T10:00:00Z",
                bankroll={"starting_equity_usd": 1000, "available_usd": 990, "reserved_risk_usd": 5, "realized_pnl_usd": -10},
            ),
        ],
    )

    assert out["bankroll"]["starting_equity_usd"] == 1000.0
    assert out["bankroll"]["available_start_usd"] == 1005.0
    assert out["bankroll"]["available_end_usd"] == 990.0
    assert out["bankroll"]["available_delta_usd"] == -15.0


def test_persist_weekly_rollup_reads_runs_for_week_and_writes_json(tmp_path: Path):
    runs_dir = tmp_path / "paper_mvp" / "runs"
    runs_dir.mkdir(parents=True)

    (runs_dir / "run-in-week.json").write_text(
        json.dumps(_run(run_id="run-in-week", timestamp="2026-02-19T14:00:00Z", pnl_r=0.4), sort_keys=True),
        encoding="utf-8",
    )
    (runs_dir / "run-other-week.json").write_text(
        json.dumps(_run(run_id="run-other-week", timestamp="2026-02-10T14:00:00Z", pnl_r=5.0), sort_keys=True),
        encoding="utf-8",
    )

    payload, path = persist_weekly_rollup(trading_week=WEEK, artifact_root=tmp_path)

    assert path == tmp_path / "paper_mvp" / "weekly" / f"{WEEK}.json"
    assert path.exists()
    assert payload["runs_total"] == 1
    assert payload["expectancy_r"] == 0.4

    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk == payload


def test_build_weekly_rollup_sets_no_go_when_hard_failure_code_present():
    out = build_weekly_rollup(
        trading_week=WEEK,
        runs=[
            _run(
                run_id="run-hard-failure",
                proposal_decision="rejected",
                execution_decision="blocked",
                pnl_r=None,
                decision_reason_codes=["NON_BYPASS_FAILED"],
                feed_state="ok",
            )
        ],
    )

    assert out["posture"]["recommendation"] == "NO_GO"
    assert out["posture"]["top_blockers"][0]["code"] == "NON_BYPASS_FAILED"
