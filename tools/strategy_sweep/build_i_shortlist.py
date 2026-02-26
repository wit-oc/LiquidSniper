#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List


def f(row: dict, k: str) -> float:
    try:
        return float(row.get(k, 0.0))
    except Exception:
        return 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description="Build profile-I global shortlist with return-first objective")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--dd-guardrail", type=float, default=0.35, help="max acceptable max_dd")
    ap.add_argument("--out-shortlist", default="shortlist_I.csv")
    ap.add_argument("--out-leaderboard", default="leaderboard_I_global.csv")
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    rows: List[dict] = []

    for d in sorted(run_dir.iterdir()):
        if not d.is_dir():
            continue
        lb = d / "leaderboard_I.csv"
        if not lb.exists():
            continue
        with lb.open("r", newline="", encoding="utf-8") as f_in:
            for r in csv.DictReader(f_in):
                r["dataset"] = d.name
                r["dd_guardrail_pass"] = "1" if f(r, "max_dd") <= args.dd_guardrail else "0"
                rows.append(r)

    rows.sort(
        key=lambda r: (
            0 if r["dd_guardrail_pass"] == "1" else 1,
            -f(r, "net_pnl"),
            -f(r, "pf"),
            f(r, "max_dd"),
            -f(r, "win_rate"),
        )
    )

    top = rows[: args.top]
    out_lb = run_dir / args.out_leaderboard
    out_sl = run_dir / args.out_shortlist

    if rows:
        with out_lb.open("w", newline="", encoding="utf-8") as f_lb:
            w = csv.DictWriter(f_lb, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        with out_sl.open("w", newline="", encoding="utf-8") as f_sl:
            w = csv.DictWriter(f_sl, fieldnames=list(top[0].keys()))
            w.writeheader()
            w.writerows(top)

    summary = {
        "run_dir": str(run_dir),
        "rows": len(rows),
        "dd_guardrail": args.dd_guardrail,
        "shortlist_rows": len(top),
    }
    (run_dir / "i_profile_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
