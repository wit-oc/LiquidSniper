from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_health(path: Path, *, status: str, loop_seconds: int, cycle_count: int) -> None:
    payload = {
        "service": "paper-runner",
        "mode": "paper",
        "status": status,
        "loop_seconds": loop_seconds,
        "cycle_count": cycle_count,
        "updated_at": _utc_now(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run_cycle(*, loop_seconds: int, health_path: Path, cycle_count: int) -> None:
    _write_health(health_path, status="ok", loop_seconds=loop_seconds, cycle_count=cycle_count)


def main() -> None:
    mode = os.getenv("LIQUIDSNIPER_MODE", "paper").strip().lower()
    if mode != "paper":
        raise RuntimeError("paper_daemon only supports LIQUIDSNIPER_MODE=paper")

    loop_seconds = int(os.getenv("LIQUIDSNIPER_LOOP_SECONDS", "60"))
    run_once = os.getenv("LIQUIDSNIPER_RUN_ONCE", "false").strip().lower() in {"1", "true", "yes"}
    health_path = Path(os.getenv("LIQUIDSNIPER_HEALTH_PATH", "/var/lib/liquidsniper/logs/paper_runner.health.json"))

    cycle_count = 0
    while True:
        cycle_count += 1
        run_cycle(loop_seconds=loop_seconds, health_path=health_path, cycle_count=cycle_count)
        if run_once:
            break
        time.sleep(max(1, loop_seconds))


if __name__ == "__main__":
    main()
