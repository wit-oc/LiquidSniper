from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import json
import os
import threading

from liquidsniper.core.mode_guard import guard_parallel_mode


@dataclass(frozen=True)
class LaneResult:
    strategy: str
    attempted: int
    executed: int
    blocked: int
    throttle_state_path: str


class PaperParallelOrchestrator:
    def __init__(self, artifact_root: str | None = None) -> None:
        self._artifact_root = Path(artifact_root or os.getenv("LS_ARTIFACT_ROOT", "artifacts"))
        self._lock = threading.Lock()

    def _lane_state_path(self, strategy: str) -> Path:
        return self._artifact_root / "paper_mvp" / "state" / "lanes" / f"{strategy}_throttle_state.json"

    def run(
        self,
        *,
        mode: str,
        enabled_strategies: list[str],
        lane_runner: Callable[[str, Path], tuple[int, int, int]],
    ) -> dict[str, object]:
        guard = guard_parallel_mode(mode=mode, payload={"parallel": True, "strategy_lanes": enabled_strategies})
        if not guard.allowed:
            return {"decision": "blocked", "reason_codes": (guard.reason_code,), "lanes": []}

        lanes = sorted({s for s in enabled_strategies if s in {"scalp", "intraday", "swing"}})
        results: list[LaneResult] = []

        def _run(strategy: str) -> LaneResult:
            path = self._lane_state_path(strategy)
            path.parent.mkdir(parents=True, exist_ok=True)
            attempted, executed, blocked = lane_runner(strategy, path)
            with self._lock:
                payload = {
                    "strategy": strategy,
                    "attempted": attempted,
                    "executed": executed,
                    "blocked": blocked,
                }
                path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            return LaneResult(strategy, attempted, executed, blocked, str(path))

        with ThreadPoolExecutor(max_workers=max(1, len(lanes))) as pool:
            for lane in pool.map(_run, lanes):
                results.append(lane)

        return {
            "decision": "executed",
            "reason_codes": (),
            "lanes": [r.__dict__ for r in sorted(results, key=lambda x: x.strategy)],
        }
