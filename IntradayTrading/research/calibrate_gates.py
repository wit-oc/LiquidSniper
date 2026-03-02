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
    keys = sorted(bias_by_ts.keys())
    current = StructureBias.NEUTRAL
    mapped = {}
    ki = 0
    for i, row in df_1h.iterrows():
        ts = int(row["timestamp"])
        while ki < len(keys) and keys[ki] <= ts:
            current = bias_by_ts[keys[ki]]
            ki += 1
        mapped[i] = current
    return mapped


def eval_symbol(df_1h: pd.DataFrame, df_4h: pd.DataFrame, cfg: RunnerConfig, zone_width: float):
    zones = build_zones_from_candles(df_4h["high"].tolist(), df_4h["low"].tolist(), width_frac=zone_width)
    bmap = bias_map_from_4h(df_4h, df_1h)
    bars = [Bar(index=i, open=r.open, high=r.high, low=r.low, close=r.close) for i, r in df_1h.iterrows()]
    runner = SignalRunner(cfg)
    events, _ = runner.run_with_logs(bars, bmap, zones)
    trades = build_trades(events, df_1h["close"])
    return summarize(trades, fee_bps_per_side=5.0, slippage_bps_per_side=2.0, funding_bps_per_8h=1.0)


def combo_score(btc: dict, eth: dict) -> float:
    # Favor PF with minimum tradability
    trades = btc["trades"] + eth["trades"]
    if trades < 40:
        return -1.0
    return ((btc["pf"] + eth["pf"]) / 2.0) + (0.0005 * trades)


def attempt_space(attempt: int):
    # progressively relax from strict to tradable while keeping Foxian anchor (context gates on)
    if attempt == 1:
        return dict(
            zone_width=[0.001],
            momentum=[0.0025, 0.002],
            chop=[0.0008, 0.0006],
            long_loc=[0.5, 0.55],
            short_loc=[0.5, 0.45],
            retest=[6],
        )
    if attempt == 2:
        return dict(zone_width=[0.001, 0.0015], momentum=[0.002, 0.0015], chop=[0.0006, 0.0004], long_loc=[0.6], short_loc=[0.4], retest=[8])
    if attempt == 3:
        return dict(zone_width=[0.001, 0.0015], momentum=[0.0015, 0.001], chop=[0.0004, 0.0002], long_loc=[0.65], short_loc=[0.35], retest=[8, 10])
    if attempt == 4:
        return dict(zone_width=[0.001, 0.0015, 0.002], momentum=[0.001, 0.0007], chop=[0.0002, 0.0001], long_loc=[0.7], short_loc=[0.3], retest=[10])
    return dict(zone_width=[0.001, 0.0015, 0.002], momentum=[0.0007, 0.0005], chop=[0.0001, 0.0], long_loc=[0.75], short_loc=[0.25], retest=[10, 12])


def run_attempt(attempt: int, btc_df: pd.DataFrame, eth_df: pd.DataFrame, btc_4h: pd.DataFrame, eth_4h: pd.DataFrame) -> dict:
    space = attempt_space(attempt)
    best = None
    for zw, mm, ch, ll, sl, rt in product(
        space["zone_width"],
        space["momentum"],
        space["chop"],
        space["long_loc"],
        space["short_loc"],
        space["retest"],
    ):
        cfg = RunnerConfig(
            max_zone_width_frac=0.02,
            reclaim_buffer_frac=0.0005,
            retest_max_bars=rt,
            enable_swing_location_gate=True,
            long_location_max=ll,
            short_location_min=sl,
            enable_momentum_gate=True,
            momentum_min_frac=mm,
            enable_chop_gate=True,
            chop_slope_abs_max=ch,
        )
        btc = eval_symbol(btc_df, btc_4h, cfg, zone_width=zw)
        eth = eval_symbol(eth_df, eth_4h, cfg, zone_width=zw)
        score = combo_score(btc, eth)
        row = {
            "attempt": attempt,
            "params": {
                "zone_width": zw,
                "momentum_min_frac": mm,
                "chop_slope_abs_max": ch,
                "long_location_max": ll,
                "short_location_min": sl,
                "retest_max_bars": rt,
            },
            "btc": btc,
            "eth": eth,
            "score": score,
        }
        if best is None or row["score"] > best["score"]:
            best = row
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempt", type=int, default=0, help="1-5 to run a single attempt; 0 runs all")
    ap.add_argument("--out", type=Path, default=Path("intraday_revisit/artifacts/sweeps/gate_calibration_v1.json"))
    args = ap.parse_args()

    btc_df = load_ohlcv(Path("intraday_revisit/data/btc_1h_blofin_2022_to_now.csv"))
    eth_df = load_ohlcv(Path("intraday_revisit/data/eth_1h_blofin_2022_to_now.csv"))
    btc_4h = resample_4h(btc_df)
    eth_4h = resample_4h(eth_df)

    attempts = [args.attempt] if args.attempt in {1, 2, 3, 4, 5} else [1, 2, 3, 4, 5]
    all_attempts = [run_attempt(a, btc_df, eth_df, btc_4h, eth_4h) for a in attempts]

    global_best = max(all_attempts, key=lambda x: x["score"]) if all_attempts else None
    out = {"best_by_attempt": all_attempts, "global_best": global_best}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
