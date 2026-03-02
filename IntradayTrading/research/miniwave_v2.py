from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from intraday_revisit.engine.runner import Bar, RunnerConfig, SignalRunner
from intraday_revisit.engine.structure import StructureBias, classify_structure_from_pivots, detect_pivots
from intraday_revisit.engine.zones_builder import build_zones_from_candles
from intraday_revisit.research.first_pass_metrics import build_trades, summarize

FEE_BPS = 5.0
SLIPPAGE_BPS = 2.0
FUNDING_BPS_8H = 1.0

OUT_DIR = Path("intraday_revisit/artifacts/sweeps/miniwave_v2")


def load_ohlcv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df.sort_values("timestamp").reset_index(drop=True)


def resample_4h(df_1h: pd.DataFrame) -> pd.DataFrame:
    d = df_1h.copy()
    d["ts"] = pd.to_datetime(d["timestamp"], unit="s", utc=True)
    d = d.set_index("ts")
    out = pd.DataFrame()
    out["open"] = d["open"].resample("4h").first()
    out["high"] = d["high"].resample("4h").max()
    out["low"] = d["low"].resample("4h").min()
    out["close"] = d["close"].resample("4h").last()
    out = out.dropna().reset_index()
    out["timestamp"] = out["ts"].astype("int64") // 10**9
    return out[["timestamp", "open", "high", "low", "close"]]


def bias_map_from_4h(df_4h: pd.DataFrame, df_1h: pd.DataFrame) -> dict[int, StructureBias]:
    pivots = detect_pivots(df_4h["high"].tolist(), df_4h["low"].tolist(), left=2, right=2)
    points = classify_structure_from_pivots(pivots)
    bias_by_ts = {int(df_4h.iloc[p.index]["timestamp"]): p.bias for p in points}
    keys = sorted(bias_by_ts.keys())
    current = StructureBias.NEUTRAL
    mapped: dict[int, StructureBias] = {}
    ki = 0
    for i, row in df_1h.iterrows():
        ts = int(row["timestamp"])
        while ki < len(keys) and keys[ki] <= ts:
            current = bias_by_ts[keys[ki]]
            ki += 1
        mapped[i] = current
    return mapped


def eval_symbol(df_1h: pd.DataFrame, df_4h: pd.DataFrame, cfg: RunnerConfig, zone_width: float) -> dict:
    zones = build_zones_from_candles(df_4h["high"].tolist(), df_4h["low"].tolist(), width_frac=zone_width)
    bmap = bias_map_from_4h(df_4h, df_1h)
    bars = [Bar(index=i, open=r.open, high=r.high, low=r.low, close=r.close) for i, r in df_1h.iterrows()]
    runner = SignalRunner(cfg)
    events, _ = runner.run_with_logs(bars, bmap, zones)
    trades = build_trades(events, df_1h["close"])
    return summarize(
        trades,
        fee_bps_per_side=FEE_BPS,
        slippage_bps_per_side=SLIPPAGE_BPS,
        funding_bps_per_8h=FUNDING_BPS_8H,
    )


def attempt_space() -> dict[int, dict[str, list[float | int]]]:
    return {
        1: {
            "zone_width": [0.0015],
            "retest": [8],
            "reclaim": [0.00035],
            "momentum": [0.0012],
            "trend": [0.0002],
            "chop": [0.00012],
            "strict_bps": [18.0],
            "near_bps": [24.0],
            "near_penalty": [0.5],
            "score_gate": [5.8],
            "trigger": [6.8],
            "risk_hi": [1.6],
        },
        2: {
            "zone_width": [0.002],
            "retest": [10],
            "reclaim": [0.00030],
            "momentum": [0.0010],
            "trend": [0.00015],
            "chop": [0.0001],
            "strict_bps": [20.0],
            "near_bps": [28.0],
            "near_penalty": [0.7],
            "score_gate": [5.6],
            "trigger": [6.6],
            "risk_hi": [1.8],
        },
        3: {
            "zone_width": [0.0025],
            "retest": [12],
            "reclaim": [0.00025],
            "momentum": [0.0008],
            "trend": [0.0001],
            "chop": [0.00008],
            "strict_bps": [22.0],
            "near_bps": [32.0],
            "near_penalty": [0.9],
            "score_gate": [5.4],
            "trigger": [6.4],
            "risk_hi": [2.0],
        },
    }


def sort_key(row: dict) -> tuple[float, float, int]:
    return (row["avg_pf"], -row["worst_dd_pct"], row["total_trades"])


def verdict(row: dict) -> bool:
    return row["total_trades"] > 100 and row["avg_pf"] > 1.0 and row["worst_dd_pct"] <= 15.0


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    btc_df = load_ohlcv(Path("intraday_revisit/data/btc_1h_blofin_2022_to_now.csv"))
    eth_df = load_ohlcv(Path("intraday_revisit/data/eth_1h_blofin_2022_to_now.csv"))
    btc_4h = resample_4h(btc_df)
    eth_4h = resample_4h(eth_df)

    all_rows: list[dict] = []

    for attempt, space in attempt_space().items():
        best: dict | None = None
        for zw, rt, rb, mm, tr, ch, sb, nb, npn, sg, tg, rhi in product(
            space["zone_width"],
            space["retest"],
            space["reclaim"],
            space["momentum"],
            space["trend"],
            space["chop"],
            space["strict_bps"],
            space["near_bps"],
            space["near_penalty"],
            space["score_gate"],
            space["trigger"],
            space["risk_hi"],
        ):
            cfg = RunnerConfig(
                allow_neutral_bias=False,
                max_zone_width_frac=0.03,
                reclaim_buffer_frac=rb,
                retest_max_bars=rt,
                require_retest_sequence=True,
                enable_swing_location_gate=True,
                long_location_max=0.82,
                short_location_min=0.18,
                enable_momentum_gate=True,
                momentum_min_frac=mm,
                enable_chop_gate=True,
                chop_slope_abs_max=ch,
                trend_slope_min=tr,
                min_rejection_wick_frac=0.0006,
                min_body_frac=0.0005,
                atr_floor_frac=0.0009,
                strict_retest_bps_max=sb,
                near_retest_bps_max=nb,
                near_retest_penalty_max=npn,
                enable_confluence_gate=True,
                score_gate_min=sg,
                trigger_score_min=tg,
                risk_pct_low_conf=1.0,
                risk_pct_high_conf=rhi,
                high_conf_score_threshold=8.0,
            )

            btc = eval_symbol(btc_df, btc_4h, cfg, zone_width=zw)
            eth = eval_symbol(eth_df, eth_4h, cfg, zone_width=zw)
            row = {
                "attempt": attempt,
                "params": {
                    "zone_width": zw,
                    "retest_max_bars": rt,
                    "reclaim_buffer_frac": rb,
                    "momentum_min_frac": mm,
                    "trend_slope_min": tr,
                    "chop_slope_abs_max": ch,
                    "strict_retest_bps_max": sb,
                    "near_retest_bps_max": nb,
                    "near_retest_penalty_max": npn,
                    "score_gate_min": sg,
                    "trigger_score_min": tg,
                    "risk_pct_high_conf": rhi,
                },
                "btc": btc,
                "eth": eth,
            }
            row["avg_pf"] = (btc["pf"] + eth["pf"]) / 2.0
            row["worst_dd_pct"] = max(btc["max_dd_pct"], eth["max_dd_pct"])
            row["total_trades"] = btc["trades"] + eth["trades"]
            row["pass_constraints"] = verdict(row)

            if best is None or sort_key(row) > sort_key(best):
                best = row

        assert best is not None
        all_rows.append(best)
        (OUT_DIR / f"attempt_{attempt}.json").write_text(json.dumps(best, indent=2), encoding="utf-8")

    ranked = sorted(all_rows, key=sort_key, reverse=True)
    (OUT_DIR / "ranked.json").write_text(json.dumps(ranked, indent=2), encoding="utf-8")

    passed = [r for r in ranked if r["pass_constraints"]]
    lines = [
        "# miniwave_v2 summary",
        "",
        f"Cost assumptions: fee={FEE_BPS} bps/side, slippage={SLIPPAGE_BPS} bps/side, funding={FUNDING_BPS_8H} bps/8h.",
        "",
        "## Ranked shortlist",
    ]
    for i, r in enumerate(ranked, start=1):
        lines.append(
            f"{i}. attempt {r['attempt']} | avg_pf={r['avg_pf']:.3f} | worst_dd_pct={r['worst_dd_pct']:.2f} | trades={r['total_trades']} | pass={r['pass_constraints']}"
        )
    lines.append("")
    if passed:
        best = passed[0]
        lines.append(
            f"Constraint verdict: PASS (attempt {best['attempt']} with avg_pf={best['avg_pf']:.3f}, DD%={best['worst_dd_pct']:.2f}, trades={best['total_trades']})."
        )
    else:
        lines.append("Constraint verdict: FAIL (no config met trades>100, PF>1, DD<=15%).")
        lines.append("")
        lines.append("## BLOCKED")
        lines.append("No blocker in execution; blocker is strategy quality under current logic/cost assumptions.")
        lines.append("Smallest next step: widen sweep to lower trigger_score_min and tune stop_buffer_frac / rr_tp2 for PF lift.")

    (OUT_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
