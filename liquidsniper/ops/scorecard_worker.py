from __future__ import annotations

from datetime import datetime, timezone

from liquidsniper.core.paper_artifacts import persist_daily_scorecard, persist_weekly_rollup


def main() -> None:
    now = datetime.now(timezone.utc)
    trading_day = now.strftime("%Y-%m-%d")
    trading_week = now.strftime("%G-W%V")
    persist_daily_scorecard(trading_day=trading_day)
    persist_weekly_rollup(trading_week=trading_week)


if __name__ == "__main__":
    main()
