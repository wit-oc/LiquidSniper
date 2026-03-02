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

OUT_DIR = Path("intraday_revisit/artifacts/sweeps/miniwave_v2_1")


# Keep miniwave_v2 baseline fixed; only tune requested knobs.
BASE_PARAMS = {
    "zone_width": 0.0015,
    "retest_max_bars": 8,
    "reclaim_buffer_frac": 0.00035,
    "momentum_min_frac": 0.0012,
    "trend_slope_min": 0.0002,
    "chop_slope_abs_max": 0.00012,
    "strict_retest_bps_max": 18.0,
    "near_retest_bps_max": 24.0,
    "score_gate_min": 5.8,
    "risk_pct_high_conf": 1.6,
}


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


def _log_telemetry(logs: list[dict], events: list[dict]) -> dict:
    bars = len(logs)
    zone_touched = sum(1 for r in logs if r.get("zone_touched", False))
    strict_retest = sum(1 for r in logs if r.get("strict_retest", False))
    near_retest = sum(1 for r in logs if r.get("near_retest", False))
    entries = [e for e in events if e.get("event") in ("enter_long", "enter_short")]
    near_entries = sum(1 for e in entries if e.get("retest_mode") == "near")
    strict_entries = sum(1 for e in entries if e.get("retest_mode") == "strict")
    score_mean = (sum((r.get("selected_score", 0.0) or 0.0) for r in logs if (r.get("selected_score", 0.0) or 0.0) > 0) / max(sum(1 for r in logs if (r.get("selected_score", 0.0) or 0.0) > 0), 1))
    return {
        "bars": bars,
        "zone_touch_rate": zone_touched / max(bars, 1),
        "strict_retest_rate": strict_retest / max(bars, 1),
        "near_retest_rate": near_retest / max(bars, 1),
        "entry_count": len(entries),
        "strict_entry_count": strict_entries,
        "near_entry_count": near_entries,
        "near_entry_share": near_entries / max(len(entries), 1),
        "selected_score_mean": score_mean,
    }


def eval_symbol(df_1h: pd.DataFrame, df_4h: pd.DataFrame, cfg: RunnerConfig, zone_width: float) -> dict:
    zones = build_zones_from_candles(df_4h["high"].tolist(), df_4h["low"].tolist(), width_frac=zone_width)
    bmap = bias_map_from_4h(df_4h, df_1h)
    bars = [Bar(index=i, open=r.open, high=r.high, low=r.low, close=r.close) for i, r in df_1h.iterrows()]
    runner = SignalRunner(cfg)
    events, logs = runner.run_with_logs(bars, bmap, zones)
    trades = build_trades(events, df_1h["close"])
    metrics = summarize(
        trades,
        fee_bps_per_side=FEE_BPS,
        slippage_bps_per_side=SLIPPAGE_BPS,
        funding_bps_per_8h=FUNDING_BPS_8H,
    )
    metrics["telemetry"] = _log_telemetry(logs, events)
    return metrics


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

    for old in OUT_DIR.glob("attempt_*.json"):
        old.unlink()

    trigger_vals = [6.4, 6.8]
    stop_buffer_vals = [0.0009, 0.0011]
    rr_tp2_vals = [2.2, 2.5]
    near_penalty_vals = [0.8, 1.1]

    rows: list[dict] = []
    attempt = 0

    for trigger, stop_buffer, rr_tp2, near_penalty in product(
        trigger_vals, stop_buffer_vals, rr_tp2_vals, near_penalty_vals
    ):
        attempt += 1
        cfg = RunnerConfig(
            allow_neutral_bias=False,  # hard daily trend alignment
            max_zone_width_frac=0.03,
            reclaim_buffer_frac=BASE_PARAMS["reclaim_buffer_frac"],
            retest_max_bars=BASE_PARAMS["retest_max_bars"],
            require_retest_sequence=True,
            enable_swing_location_gate=True,
            long_location_max=0.82,
            short_location_min=0.18,
            enable_momentum_gate=True,
            momentum_min_frac=BASE_PARAMS["momentum_min_frac"],
            enable_chop_gate=True,
            chop_slope_abs_max=BASE_PARAMS["chop_slope_abs_max"],
            trend_slope_min=BASE_PARAMS["trend_slope_min"],
            min_rejection_wick_frac=0.0006,
            min_body_frac=0.0005,
            atr_floor_frac=0.0009,
            strict_retest_bps_max=BASE_PARAMS["strict_retest_bps_max"],
            near_retest_bps_max=BASE_PARAMS["near_retest_bps_max"],
            near_retest_penalty_max=near_penalty,
            enable_confluence_gate=True,
            score_gate_min=BASE_PARAMS["score_gate_min"],
            trigger_score_min=trigger,
            stop_buffer_frac=stop_buffer,
            rr_tp2=rr_tp2,
            risk_pct_low_conf=1.0,
            risk_pct_high_conf=BASE_PARAMS["risk_pct_high_conf"],
            high_conf_score_threshold=8.0,
        )

        btc = eval_symbol(btc_df, btc_4h, cfg, zone_width=BASE_PARAMS["zone_width"])
        eth = eval_symbol(eth_df, eth_4h, cfg, zone_width=BASE_PARAMS["zone_width"])

        row = {
            "attempt": attempt,
            "params": {
                **BASE_PARAMS,
                "trigger_score_min": trigger,
                "stop_buffer_frac": stop_buffer,
                "rr_tp2": rr_tp2,
                "near_retest_penalty_max": near_penalty,
            },
            "btc": btc,
            "eth": eth,
        }
        row["avg_pf"] = (btc["pf"] + eth["pf"]) / 2.0
        row["worst_dd_pct"] = max(btc["max_dd_pct"], eth["max_dd_pct"])
        row["total_trades"] = btc["trades"] + eth["trades"]
        row["pass_constraints"] = verdict(row)

        rows.append(row)
        (OUT_DIR / f"attempt_{attempt:03d}.json").write_text(json.dumps(row, indent=2), encoding="utf-8")

    ranked = sorted(rows, key=sort_key, reverse=True)
    (OUT_DIR / "ranked.json").write_text(json.dumps(ranked, indent=2), encoding="utf-8")

    best = ranked[0]
    passed = [r for r in ranked if r["pass_constraints"]]

    lines = [
        "# miniwave_v2.1 narrow sweep",
        "",
        f"Cost assumptions: fee={FEE_BPS} bps/side, slippage={SLIPPAGE_BPS} bps/side, funding={FUNDING_BPS_8H} bps/8h.",
        "Trend alignment: hard (allow_neutral_bias=False).",
        "",
        "## Search space",
        f"- trigger_score_min: {trigger_vals}",
        f"- stop_buffer_frac: {stop_buffer_vals}",
        f"- rr_tp2: {rr_tp2_vals}",
        f"- near_retest_penalty_max: {near_penalty_vals}",
        f"- total attempts: {len(rows)}",
        "",
        "## Best by ranking (avg PF desc, DD asc, trades desc)",
        f"- attempt {best['attempt']:03d}",
        f"- avg_pf={best['avg_pf']:.3f}",
        f"- worst_dd_pct={best['worst_dd_pct']:.2f}",
        f"- total_trades={best['total_trades']}",
        f"- pass_constraints={best['pass_constraints']}",
        f"- params={json.dumps(best['params'])}",
        "",
        "## Constraints check",
    ]

    trade_ok = best["total_trades"] > 100
    pf_ok = best["avg_pf"] > 1.0
    dd_ok = best["worst_dd_pct"] <= 15.0
    lines.append(f"- trades > 100: {'PASS' if trade_ok else 'FAIL'} ({best['total_trades']})")
    lines.append(f"- PF > 1: {'PASS' if pf_ok else 'FAIL'} ({best['avg_pf']:.3f})")
    lines.append(f"- DD <= 15%: {'PASS' if dd_ok else 'FAIL'} ({best['worst_dd_pct']:.2f}%)")

    if passed:
        lines.append("")
        lines.append(f"Constraint verdict: PASS (found {len(passed)} passing profiles).")
    else:
        lines.append("")
        lines.append("Constraint verdict: FAIL (no profile met trades>100, PF>1, DD<=15%).")

    (OUT_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
