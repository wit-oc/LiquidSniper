"""Backtest evaluator harness for LiquidSniper MVP.

Consumes deterministic replay-like cases and produces summary metrics plus
pass/fail checks against configurable thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class EvalThresholds:
    max_negative_expectancy: float = -0.02
    max_drawdown_r: float = 3.0
    p95_latency_seconds: float = 15.0


def _pct(n: int, d: int) -> float:
    return 0.0 if d <= 0 else round((n / d) * 100.0, 2)


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    # deterministic nearest-rank style
    idx = max(0, min(len(xs) - 1, int(round(0.95 * (len(xs) - 1)))))
    return round(xs[idx], 3)


def evaluate_cases(cases: list[dict[str, Any]], thresholds: EvalThresholds | None = None) -> dict[str, Any]:
    t = thresholds or EvalThresholds()

    rs: list[float] = []
    wins = 0
    losses = 0
    latencies: list[float] = []

    for c in cases:
        r = float(c.get("outcome_r") or 0.0)
        rs.append(r)
        if r > 0:
            wins += 1
        elif r < 0:
            losses += 1

        if "latency_seconds" in c:
            latencies.append(float(c.get("latency_seconds") or 0.0))

    expectancy = round(mean(rs), 4) if rs else 0.0

    # max drawdown on cumulative R curve
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in rs:
        cum += r
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)

    p95_latency = _p95(latencies)

    checks = {
        "expectancy_ok": expectancy >= t.max_negative_expectancy,
        "drawdown_ok": max_dd <= t.max_drawdown_r,
        "latency_ok": p95_latency <= t.p95_latency_seconds,
    }

    return {
        "total": len(cases),
        "wins": wins,
        "losses": losses,
        "win_rate_pct": _pct(wins, len(cases)),
        "expectancy_r": expectancy,
        "max_drawdown_r": round(max_dd, 4),
        "p95_latency_seconds": p95_latency,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def render_markdown_report(summary: dict[str, Any], title: str = "LiquidSniper Backtest Evaluator Report") -> str:
    checks = summary.get("checks", {})
    lines = [
        f"# {title}",
        "",
        "## Metrics",
        f"- Total cases: {summary.get('total', 0)}",
        f"- Wins / Losses: {summary.get('wins', 0)} / {summary.get('losses', 0)}",
        f"- Win rate: {summary.get('win_rate_pct', 0.0)}%",
        f"- Expectancy (R): {summary.get('expectancy_r', 0.0)}",
        f"- Max drawdown (R): {summary.get('max_drawdown_r', 0.0)}",
        f"- p95 latency (s): {summary.get('p95_latency_seconds', 0.0)}",
        "",
        "## Checks",
        f"- Expectancy guardrail: {'PASS' if checks.get('expectancy_ok') else 'FAIL'}",
        f"- Drawdown guardrail: {'PASS' if checks.get('drawdown_ok') else 'FAIL'}",
        f"- Latency guardrail: {'PASS' if checks.get('latency_ok') else 'FAIL'}",
        "",
        f"## Overall: {'PASS' if summary.get('all_checks_pass') else 'FAIL'}",
    ]
    return "\n".join(lines) + "\n"
