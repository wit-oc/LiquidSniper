from pathlib import Path

from liquidsniper.ops.paper_parallel import PaperParallelOrchestrator


def test_parallel_orchestrator_rejects_non_paper_mode(tmp_path: Path):
    orchestrator = PaperParallelOrchestrator(str(tmp_path / "artifacts"))
    out = orchestrator.run(mode="live", enabled_strategies=["intraday", "scalp"], lane_runner=lambda *_: (1, 1, 0))
    assert out["decision"] == "blocked"
    assert out["reason_codes"] == ("MODE_GUARD_PARALLEL_REQUIRES_PAPER",)


def test_parallel_orchestrator_runs_lanes_with_isolated_state(tmp_path: Path):
    orchestrator = PaperParallelOrchestrator(str(tmp_path / "artifacts"))

    def lane_runner(strategy: str, lane_state_path: Path):
        assert strategy in {"intraday", "scalp"}
        assert strategy in lane_state_path.name
        return (2, 1 if strategy == "intraday" else 0, 1)

    out = orchestrator.run(mode="paper", enabled_strategies=["intraday", "scalp"], lane_runner=lane_runner)
    assert out["decision"] == "executed"
    assert len(out["lanes"]) == 2
    for lane in out["lanes"]:
        assert Path(lane["throttle_state_path"]).exists()
