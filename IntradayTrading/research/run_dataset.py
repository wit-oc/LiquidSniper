from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from intraday_revisit.engine.logger import write_jsonl
from intraday_revisit.engine.runner import Bar, SignalRunner
from intraday_revisit.engine.structure import StructureBias, classify_structure_from_pivots, detect_pivots
from intraday_revisit.engine.zones_builder import build_zones_from_candles


def load_ohlcv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
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

    # map 4h bias to timestamp, then forward-fill onto 1h bars
    bias_by_ts = {int(df_4h.iloc[p.index]["timestamp"]): p.bias for p in points}
    current = StructureBias.NEUTRAL
    mapped = {}
    for i, row in df_1h.iterrows():
        ts = int(row["timestamp"])
        for k in sorted(bias_by_ts.keys()):
            if k <= ts:
                current = bias_by_ts[k]
            else:
                break
        mapped[i] = current
    return mapped


def run_symbol(symbol: str, input_csv: Path, out_dir: Path) -> None:
    df_1h = load_ohlcv(input_csv)
    df_4h = resample_4h(df_1h)

    zones = build_zones_from_candles(df_4h["high"].tolist(), df_4h["low"].tolist(), left=2, right=2)
    bmap = bias_map_from_4h(df_4h, df_1h)

    has_volume = "volume" in df_1h.columns
    bars = [
        Bar(
            index=i,
            open=r.open,
            high=r.high,
            low=r.low,
            close=r.close,
            timestamp=int(r.timestamp),
            volume=(None if not has_volume or pd.isna(r.volume) else float(r.volume)),
        )
        for i, r in df_1h.iterrows()
    ]
    runner = SignalRunner()
    events, logs = runner.run_with_logs(bars, bmap, zones, symbol=symbol, tf="1h")

    out_dir.mkdir(parents=True, exist_ok=True)
    # events are written raw (event-centric schema); bar logs use canonical log schema.
    with (out_dir / f"{symbol.lower()}_events.jsonl").open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, separators=(",", ":")) + "\n")
    write_jsonl(out_dir / f"{symbol.lower()}_barlogs.jsonl", logs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--btc", type=Path, required=True)
    ap.add_argument("--eth", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("intraday_revisit/artifacts/initial_run"))
    args = ap.parse_args()

    run_symbol("BTC", args.btc, args.out)
    run_symbol("ETH", args.eth, args.out)
    print(f"Wrote artifacts to {args.out}")
