from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def gate_funnel(logs: list[dict]) -> dict:
    n = len(logs)
    def c(pred):
        return sum(1 for r in logs if pred(r))

    return {
        "bars": n,
        "zone_touched": c(lambda r: r.get("zone_touched", False)),
        "strict_retest": c(lambda r: r.get("strict_retest", False)),
        "near_retest": c(lambda r: r.get("near_retest", False)),
        "retest_gate": c(lambda r: r.get("retest_gate", False)),
        "regime_gate": c(lambda r: r.get("regime_gate", False)),
        "chop_ok": c(lambda r: r.get("chop_ok", False)),
        "long_score_ok": c(lambda r: r.get("long_score_ok", False)),
        "short_score_ok": c(lambda r: r.get("short_score_ok", False)),
        "entries": c(lambda r: str(r.get("action", "none")).startswith("enter_")),
    }


def rejection_reasons(logs: list[dict]) -> dict:
    ctr = Counter()
    for r in logs:
        if str(r.get("action", "none")).startswith("enter_"):
            continue
        if not r.get("zone_touched", False):
            ctr["no_zone_touch"] += 1
            continue
        if not r.get("retest_gate", False):
            ctr["retest_gate_fail"] += 1
        if not r.get("regime_gate", True):
            ctr["regime_fail"] += 1
        if r.get("cooldown_active", False):
            ctr["cooldown_active"] += 1
        if not r.get("chop_ok", True):
            ctr["chop_fail"] += 1
        if not (r.get("long_score_ok", True) or r.get("short_score_ok", True)):
            ctr["score_gate_fail"] += 1
        if not (r.get("long_quality_ok", True) or r.get("short_quality_ok", True)):
            ctr["quality_fail"] += 1
    return dict(ctr)


def trade_attribution(events: list[dict], price_df: pd.DataFrame) -> dict:
    opens = {"long": [], "short": []}
    trades = []

    for e in events:
        ev = e.get("event")
        idx = int(e.get("index", 0))
        if ev == "enter_long":
            opens["long"].append({"side":"long","entry_idx": idx, "entry": float(e.get("entry", price_df.loc[idx, "close"])), "mode": e.get("retest_mode", "none"), "score": float(e.get("confluence_score", 0.0))})
        elif ev == "enter_short":
            opens["short"].append({"side":"short","entry_idx": idx, "entry": float(e.get("entry", price_df.loc[idx, "close"])), "mode": e.get("retest_mode", "none"), "score": float(e.get("confluence_score", 0.0))})
        elif ev in ("exit_stop", "exit_tp2"):
            side = e.get("side")
            if side in opens and opens[side]:
                t = opens[side].pop(0)
                t["exit_idx"] = idx
                t["exit_reason"] = ev
                t["exit"] = float(price_df.loc[idx, "close"])
                trades.append(t)

    by_mode = defaultdict(lambda: {"count": 0, "wins": 0, "sum_pnl": 0.0, "mae_r_sum": 0.0, "mfe_r_sum": 0.0})
    for t in trades:
        i0, i1 = t["entry_idx"], t["exit_idx"]
        if i1 <= i0:
            continue
        w = price_df.iloc[i0:i1 + 1]
        entry = t["entry"]
        side = t.get("side", "long")
        if side == "long":
            pnl = t["exit"] - entry
            adverse = (entry - w["low"].min())
            favorable = (w["high"].max() - entry)
            risk_unit = max(entry * 0.001, 1e-9)
        else:
            pnl = entry - t["exit"]
            adverse = (w["high"].max() - entry)
            favorable = (entry - w["low"].min())
            risk_unit = max(entry * 0.001, 1e-9)

        mode = t["mode"]
        by_mode[mode]["count"] += 1
        by_mode[mode]["wins"] += 1 if pnl > 0 else 0
        by_mode[mode]["sum_pnl"] += pnl
        by_mode[mode]["mae_r_sum"] += max(adverse, 0.0) / risk_unit
        by_mode[mode]["mfe_r_sum"] += max(favorable, 0.0) / risk_unit

    out = {}
    for m, v in by_mode.items():
        c = max(v["count"], 1)
        out[m] = {
            "count": v["count"],
            "win_rate": v["wins"] / c,
            "avg_pnl": v["sum_pnl"] / c,
            "avg_mae_r": v["mae_r_sum"] / c,
            "avg_mfe_r": v["mfe_r_sum"] / c,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", type=Path, required=True)
    ap.add_argument("--events", type=Path, required=True)
    ap.add_argument("--barlogs", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    price_df = pd.read_csv(args.price)
    events = load_jsonl(args.events)
    logs = load_jsonl(args.barlogs)

    report = {
        "funnel": gate_funnel(logs),
        "rejections": rejection_reasons(logs),
        "trade_attribution": trade_attribution(events, price_df),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
