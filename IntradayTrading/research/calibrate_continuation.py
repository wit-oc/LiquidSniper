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

FEE_BPS = 5.0
SLIPPAGE_BPS = 2.0
FUNDING_BPS_8H = 1.0


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


def attempt_space(attempt: int) -> dict[str, list[float | int | bool]]:
    # Continuation-focused path: progressively relax confluence while preserving bias + retest + wick confirmation.
    spaces = {
        1: {
            "zone_width": [0.001, 0.0015],
            "retest": [8],
            "reclaim": [0.0004],
            "momentum": [0.0015, 0.0012],
            "trend": [0.00025],
            "chop": [0.00015],
            "long_loc": [0.72],
            "short_loc": [0.28],
            "wick": [0.0008],
            "body": [0.0007],
            "allow_neutral": [False],
        },
        2: {
            "zone_width": [0.0015, 0.002],
            "retest": [10],
            "reclaim": [0.00035],
            "momentum": [0.0012, 0.001],
            "trend": [0.0002],
            "chop": [0.00012],
            "long_loc": [0.76],
            "short_loc": [0.24],
            "wick": [0.0007],
            "body": [0.0006],
            "allow_neutral": [False],
        },
        3: {
            "zone_width": [0.0015, 0.002, 0.0025],
            "retest": [10, 12],
            "reclaim": [0.0003],
            "momentum": [0.001, 0.0008],
            "trend": [0.00015],
            "chop": [0.0001, 0.00008],
            "long_loc": [0.8],
            "short_loc": [0.2],
            "wick": [0.0006],
            "body": [0.0005],
            "allow_neutral": [False],
        },
        4: {
            "zone_width": [0.002, 0.0025],
            "retest": [12],
            "reclaim": [0.00025],
            "momentum": [0.0008, 0.0006],
            "trend": [0.0001],
            "chop": [0.00006],
            "long_loc": [0.84],
            "short_loc": [0.16],
            "wick": [0.0005],
            "body": [0.00045],
            "allow_neutral": [True],
        },
        5: {
            "zone_width": [0.0025, 0.003],
            "retest": [12, 14],
            "reclaim": [0.0002],
            "momentum": [0.0006, 0.0004],
            "trend": [0.00008],
            "chop": [0.00004],
            "long_loc": [0.88],
            "short_loc": [0.12],
            "wick": [0.0004],
            "body": [0.00035],
            "allow_neutral": [True],
        },
    }
    return spaces[attempt]


def score_row(btc: dict, eth: dict) -> float:
    # Favor tradability + PF while punishing drawdown.
    trades = btc["trades"] + eth["trades"]
    avg_pf = (btc["pf"] + eth["pf"]) / 2.0
    dd_penalty = 0.0005 * (btc["max_dd"] + eth["max_dd"])
    return avg_pf + (0.002 * trades) - dd_penalty


def pass_fail_reason(best: dict) -> tuple[bool, str]:
    btc = best["btc"]
    eth = best["eth"]
    total_trades = btc["trades"] + eth["trades"]
    avg_pf = (btc["pf"] + eth["pf"]) / 2.0
    total_net = btc["net"] + eth["net"]
    worst_dd = max(btc["max_dd"], eth["max_dd"])

    if total_trades < 30:
        return False, f"Insufficient tradability ({total_trades} total trades < 30)."
    if avg_pf < 1.05:
        return False, f"Cost-adjusted PF too low (avg {avg_pf:.2f} < 1.05)."
    if total_net <= 0:
        return False, f"Negative combined net after costs ({total_net:.2f})."
    if worst_dd > 350:
        return False, f"Drawdown too high (worst symbol DD {worst_dd:.2f} > 350)."
    return True, "Pass: tradable, PF > 1.05, positive net, DD within limit."


def run_attempt(attempt: int, btc_df: pd.DataFrame, eth_df: pd.DataFrame, btc_4h: pd.DataFrame, eth_4h: pd.DataFrame) -> dict:
    space = attempt_space(attempt)
    best = None

    for zw, rt, rb, mm, tr, ch, ll, sl, wk, bd, an in product(
        space["zone_width"],
        space["retest"],
        space["reclaim"],
        space["momentum"],
        space["trend"],
        space["chop"],
        space["long_loc"],
        space["short_loc"],
        space["wick"],
        space["body"],
        space["allow_neutral"],
    ):
        cfg = RunnerConfig(
            max_zone_width_frac=0.03,
            reclaim_buffer_frac=rb,
            retest_max_bars=rt,
            require_retest_sequence=True,
            enable_swing_location_gate=True,
            long_location_max=ll,
            short_location_min=sl,
            enable_momentum_gate=True,
            momentum_min_frac=mm,
            enable_chop_gate=True,
            chop_slope_abs_max=ch,
            trend_slope_min=tr,
            min_rejection_wick_frac=wk,
            min_body_frac=bd,
            allow_neutral_bias=an,
            atr_floor_frac=0.0009,
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
                "long_location_max": ll,
                "short_location_min": sl,
                "min_rejection_wick_frac": wk,
                "min_body_frac": bd,
                "allow_neutral_bias": an,
            },
            "btc": btc,
            "eth": eth,
        }
        row["score"] = score_row(btc, eth)
        if best is None or row["score"] > best["score"]:
            best = row

    passed, reason = pass_fail_reason(best)
    best["pass"] = passed
    best["pass_fail_reason"] = reason
    best["cost_assumptions"] = {
        "fee_bps_per_side": FEE_BPS,
        "slippage_bps_per_side": SLIPPAGE_BPS,
        "funding_bps_per_8h": FUNDING_BPS_8H,
    }
    return best


def append_summary(summary_path: Path, result: dict) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    line = (
        f"- attempt {result['attempt']}: "
        f"BTC trades={result['btc']['trades']} pf={result['btc']['pf']:.3f} dd={result['btc']['max_dd']:.2f}; "
        f"ETH trades={result['eth']['trades']} pf={result['eth']['pf']:.3f} dd={result['eth']['max_dd']:.2f}; "
        f"pass={result['pass']} | {result['pass_fail_reason']}\n"
    )
    with summary_path.open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempt", type=int, required=True, choices=[1, 2, 3, 4, 5])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--summary", type=Path, default=Path("intraday_revisit/artifacts/sweeps/continuation_summary.md"))
    args = ap.parse_args()

    btc_df = load_ohlcv(Path("intraday_revisit/data/btc_1h_blofin_2022_to_now.csv"))
    eth_df = load_ohlcv(Path("intraday_revisit/data/eth_1h_blofin_2022_to_now.csv"))
    btc_4h = resample_4h(btc_df)
    eth_4h = resample_4h(eth_df)

    best = run_attempt(args.attempt, btc_df, eth_df, btc_4h, eth_4h)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(best, indent=2))
    append_summary(args.summary, best)
    print(json.dumps(best, indent=2))


if __name__ == "__main__":
    main()
