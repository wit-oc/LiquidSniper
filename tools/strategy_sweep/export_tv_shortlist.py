#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List


def read_csv(path: Path) -> List[dict]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(row: dict, key: str) -> float:
    try:
        return float(row.get(key, 0.0))
    except Exception:
        return 0.0


def pick_safe(rows: List[dict], n: int = 3) -> List[dict]:
    ranked = sorted(rows, key=lambda r: (to_float(r, "max_dd"), -to_float(r, "pf"), -to_float(r, "net_pnl")))
    return ranked[:n]


def main() -> None:
    ap = argparse.ArgumentParser(description="Export TradingView shortlist from profile leaderboards")
    ap.add_argument("--in-dir", default="tools/strategy_sweep/outputs")
    ap.add_argument("--out", default="tools/strategy_sweep/outputs/tv_shortlist.csv")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    shortlist: List[dict] = []

    for profile in ["C", "I", "S"]:
        rows = read_csv(in_dir / f"leaderboard_{profile}.csv")
        rows.sort(key=lambda r: to_float(r, "score"), reverse=True)
        top = rows[:10]
        safe = pick_safe(rows, n=3)

        for i, row in enumerate(top, 1):
            shortlist.append({"profile": profile, "bucket": "top10", "rank": i, **row})
        for i, row in enumerate(safe, 1):
            shortlist.append({"profile": profile, "bucket": "safe", "rank": i, **row})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if shortlist:
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(shortlist[0].keys()))
            w.writeheader()
            w.writerows(shortlist)
    print(f"Wrote {len(shortlist)} rows to {out}")


if __name__ == "__main__":
    main()
