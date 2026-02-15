from __future__ import annotations

import subprocess
from pathlib import Path


def _f(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / name


def test_metric_drift_gate_passes_on_good_summary() -> None:
    proc = subprocess.run(
        [
            "python3",
            "tools/check_metric_drift.py",
            "--summary",
            str(_f("metric_summary_pass_v1.json")),
            "--baseline",
            str(_f("metric_baseline_v1.json")),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "METRIC_DRIFT_OK" in proc.stdout


def test_metric_drift_gate_fails_on_regression() -> None:
    proc = subprocess.run(
        [
            "python3",
            "tools/check_metric_drift.py",
            "--summary",
            str(_f("metric_summary_fail_v1.json")),
            "--baseline",
            str(_f("metric_baseline_v1.json")),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "METRIC_DRIFT_FAIL" in proc.stdout
