#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

NUM_FIELDS = [
    "net_pnl_pct",
    "profit_factor",
    "max_dd_pct",
    "total_trades",
    "win_rate_pct",
    "avg_trade_pct",
]


def fnum(v: str):
    if v is None:
        return None
    v = str(v).strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def load_rows(path: Path):
    with path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows


def complete(row: dict) -> bool:
    return all(fnum(row.get(k, "")) is not None for k in NUM_FIELDS)


def score_row(row: dict, baseline: dict | None) -> float:
    pf = fnum(row.get("profit_factor")) or 0.0
    pnl = fnum(row.get("net_pnl_pct")) or -999.0
    dd = fnum(row.get("max_dd_pct")) or 999.0
    trades = fnum(row.get("total_trades")) or 0.0

    score = 0.0
    score += pf * 100
    score += pnl * 5
    score -= dd * 4
    if trades < 30:
        score -= 15

    if baseline and row.get("run_id") != baseline.get("run_id"):
        bpf = fnum(baseline.get("profit_factor")) or 0.0
        bdd = fnum(baseline.get("max_dd_pct")) or 999.0
        score += (pf - bpf) * 40
        score -= max(0.0, dd - bdd) * 2

    return round(score, 2)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tradingview/scripts/score_runs.py tradingview/results/run_log.csv")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2

    rows = load_rows(path)
    baseline = next((r for r in rows if str(r.get("is_control", "")).lower() == "true"), None)

    completed = [r for r in rows if complete(r)]
    pending = [r for r in rows if not complete(r)]

    print("=== TradingView Run Leaderboard ===")
    if not completed:
        print("No completed runs yet. Fill metrics in CSV first.")
    else:
        ranked = sorted(completed, key=lambda r: score_row(r, baseline), reverse=True)
        for i, r in enumerate(ranked, 1):
            print(
                f"{i:>2}. {r['run_id']:<10} score={score_row(r, baseline):>6} | "
                f"PF={fnum(r['profit_factor']):>5} | Net%={fnum(r['net_pnl_pct']):>6} | "
                f"DD%={fnum(r['max_dd_pct']):>5} | Trades={int(fnum(r['total_trades']) or 0):>3} | "
                f"Δ={r.get('value_changes','')}"
            )

    if pending:
        print("\n=== Pending Runs ===")
        for r in pending:
            print(f"- {r['run_id']}: {r.get('delta_summary','')} ({r.get('value_changes','')})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
