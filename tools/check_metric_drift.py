#!/usr/bin/env python3
"""Fail CI when evaluator metrics drift below baseline thresholds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True, help="Path to current metrics summary JSON")
    ap.add_argument("--baseline", required=True, help="Path to baseline threshold JSON")
    args = ap.parse_args()

    summary = _load(args.summary)
    baseline = _load(args.baseline)

    failures: list[str] = []

    if float(summary.get("expectancy_r", 0.0)) < float(baseline.get("min_expectancy_r", 0.0)):
        failures.append("expectancy_r")

    if float(summary.get("win_rate_pct", 0.0)) < float(baseline.get("min_win_rate_pct", 0.0)):
        failures.append("win_rate_pct")

    if float(summary.get("max_drawdown_r", 999.0)) > float(baseline.get("max_drawdown_r", 999.0)):
        failures.append("max_drawdown_r")

    if float(summary.get("p95_latency_seconds", 999.0)) > float(baseline.get("max_p95_latency_seconds", 999.0)):
        failures.append("p95_latency_seconds")

    if failures:
        print("METRIC_DRIFT_FAIL:" + ",".join(failures))
        return 1

    print("METRIC_DRIFT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
