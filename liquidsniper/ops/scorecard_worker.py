from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from liquidsniper.core.paper_artifacts import persist_daily_scorecard, persist_weekly_rollup


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _write_health(path: Path, *, trading_day: str, trading_week: str) -> None:
    payload = {
        "service": "scorecard-worker",
        "mode": "paper",
        "status": "ok",
        "trading_day": trading_day,
        "trading_week": trading_week,
        "updated_at": _utc_now().isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    now = _utc_now()
    trading_day = now.strftime("%Y-%m-%d")
    trading_week = now.strftime("%G-W%V")

    artifact_root_env = os.getenv("LIQUIDSNIPER_ARTIFACT_ROOT") or os.getenv("LS_ARTIFACT_ROOT")
    artifact_root = Path(artifact_root_env) if artifact_root_env else None

    persist_daily_scorecard(trading_day=trading_day, artifact_root=artifact_root)
    persist_weekly_rollup(trading_week=trading_week, artifact_root=artifact_root)

    health_path = Path(os.getenv("LIQUIDSNIPER_SCORECARD_HEALTH_PATH", "/var/lib/liquidsniper/logs/scorecard_worker.health.json"))
    _write_health(health_path, trading_day=trading_day, trading_week=trading_week)


if __name__ == "__main__":
    main()
