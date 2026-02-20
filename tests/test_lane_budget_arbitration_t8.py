from liquidsniper.ops.paper_parallel import PaperParallelOrchestrator


def test_lane_budget_limit_reject_source(tmp_path):
    o = PaperParallelOrchestrator(str(tmp_path / "artifacts"))
    out = o.run(
        mode="paper",
        enabled_strategies=["intraday"],
        lane_runner=lambda *_: (1, 1, 0),
        lane_budget_usd={"intraday": 50},
        lane_used_usd={"intraday": 50},
    )
    lane = out["lanes"][0]
    assert lane["blocked"] == 1
    assert lane["reject_source"] == "lane_limit"


def test_global_breaker_wins_over_lane_execution(tmp_path):
    o = PaperParallelOrchestrator(str(tmp_path / "artifacts"))
    out = o.run(
        mode="paper",
        enabled_strategies=["intraday", "scalp"],
        lane_runner=lambda *_: (1, 1, 0),
        global_breaker_tripped=True,
    )
    assert all(l["reject_source"] == "global_drawdown_trip" for l in out["lanes"])
    assert all(l["executed"] == 0 for l in out["lanes"])
