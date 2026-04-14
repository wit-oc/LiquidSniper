from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

import pandas as pd

from intraday_revisit.engine.runner import Bar, RunnerConfig, SignalRunner
from intraday_revisit.engine.structure import StructureBias, classify_structure_from_pivots, detect_pivots
from intraday_revisit.engine.zones_builder import build_zones_from_candles
from intraday_revisit.research.first_pass_metrics import build_trades, summarize


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
    current = StructureBias.NEUTRAL
    mapped = {}
    keys = sorted(bias_by_ts.keys())
    ki = 0
    for i, row in df_1h.iterrows():
        ts = int(row["timestamp"])
        while ki < len(keys) and keys[ki] <= ts:
            current = bias_by_ts[keys[ki]]
            ki += 1
        mapped[i] = current
    return mapped


def eval_symbol(df_1h: pd.DataFrame, zone_width: float, reclaim_buf: float, max_zone_frac: float) -> dict:
    df_4h = resample_4h(df_1h)
    zones = build_zones_from_candles(df_4h["high"].tolist(), df_4h["low"].tolist(), left=2, right=2, width_frac=zone_width)
    bmap = bias_map_from_4h(df_4h, df_1h)
    bars = [Bar(index=i, open=r.open, high=r.high, low=r.low, close=r.close) for i, r in df_1h.iterrows()]

    runner = SignalRunner(RunnerConfig(max_zone_width_frac=max_zone_frac, reclaim_buffer_frac=reclaim_buf))
    events, _ = runner.run_with_logs(bars, bmap, zones)
    trades = build_trades(events, df_1h["close"])
    return summarize(trades)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--btc", type=Path, required=True)
    ap.add_argument("--eth", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("intraday_revisit/artifacts/sweeps/sweep_v1.json"))
    args = ap.parse_args()

    btc = load_ohlcv(args.btc)
    eth = load_ohlcv(args.eth)

    zone_widths = [0.0005, 0.001, 0.0015]
    reclaim_bufs = [0.0005, 0.001, 0.0015]
    max_zone_fracs = [0.0075, 0.01, 0.015]

    rows = []
    for zw, rb, mz in product(zone_widths, reclaim_bufs, max_zone_fracs):
        r_btc = eval_symbol(btc, zw, rb, mz)
        r_eth = eval_symbol(eth, zw, rb, mz)
        rows.append({
            "zone_width": zw,
            "reclaim_buf": rb,
            "max_zone_frac": mz,
            "btc": r_btc,
            "eth": r_eth,
            "score": ((r_btc["pf"] + r_eth["pf"]) / 2.0),
        })

    rows.sort(key=lambda x: x["score"], reverse=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"top": rows[:10], "all": rows}, indent=2))
    print(f"wrote {args.out}")
    print(json.dumps(rows[:3], indent=2))


if __name__ == "__main__":
    main()
