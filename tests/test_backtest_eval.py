from __future__ import annotations

import json
from pathlib import Path

from liquidsniper.core.backtest_eval import evaluate_cases, render_markdown_report


def _load_cases() -> list[dict]:
    p = Path(__file__).parent / "fixtures" / "backtest_eval_cases_v1.json"
    return list(json.loads(p.read_text(encoding="utf-8"))["cases"])


def test_backtest_eval_summary_and_checks_pass() -> None:
    summary = evaluate_cases(_load_cases())

    assert summary["total"] == 8
    assert summary["wins"] == 5
    assert summary["losses"] == 3
    assert summary["expectancy_r"] == 0.3625
    assert summary["max_drawdown_r"] == 0.8
    assert summary["p95_latency_seconds"] == 14.0
    assert summary["all_checks_pass"] is True


def test_backtest_markdown_render_contains_overall() -> None:
    summary = evaluate_cases(_load_cases())
    md = render_markdown_report(summary)

    assert "# LiquidSniper Backtest Evaluator Report" in md
    assert "## Overall: PASS" in md
