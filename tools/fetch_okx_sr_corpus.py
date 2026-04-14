#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import ccxt

from liquidsniper.core.sr_universe import CANONICAL_SR_SOURCE, load_validation_basket, symbol_to_asset

DATA_ROOT = Path("IntradayTrading/data")
DEFAULT_SINCE_ISO = "2022-01-01T00:00:00Z"
TIMEFRAME_ORDER = ("4h", "1d")


def iso_to_ms(value: str) -> int:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)


def write_csv(path: Path, rows: list[list[float]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for row in rows:
            ts_ms, o, h, l, c, v = row[:6]
            writer.writerow([int(ts_ms // 1000), o, h, l, c, v])
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_ohlcv_full(exchange: ccxt.Exchange, market_symbol: str, timeframe: str, since_ms: int) -> list[list[float]]:
    out: list[list[float]] = []
    cursor = since_ms
    while True:
        batch = exchange.fetch_ohlcv(market_symbol, timeframe=timeframe, since=cursor, limit=300)
        if not batch:
            break
        if out and batch[0][0] <= out[-1][0]:
            batch = [row for row in batch if row[0] > out[-1][0]]
        if not batch:
            break
        out.extend(batch)
        cursor = batch[-1][0] + 1
        if len(batch) < 300:
            break
        time.sleep(exchange.rateLimit / 1000.0)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch canonical OKX 4H/1D SR corpus for the validation basket.")
    parser.add_argument("--symbols", default="", help="Comma-separated symbols like BTCUSDT,ETHUSDT. Default: validation basket.")
    parser.add_argument("--since", default=DEFAULT_SINCE_ISO)
    parser.add_argument("--timeframes", default="4h,1d")
    parser.add_argument("--sleep-ms", type=int, default=350)
    args = parser.parse_args()

    if args.symbols.strip():
        symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    else:
        symbols = [row.symbol for row in load_validation_basket()]
    timeframes = [item.strip().lower() for item in args.timeframes.split(",") if item.strip()]

    exchange = ccxt.okx({"enableRateLimit": True})
    markets = exchange.load_markets()
    since_ms = iso_to_ms(args.since)
    manifest = {
        "provider": "ccxt",
        "exchange_id": exchange.id,
        "source": CANONICAL_SR_SOURCE,
        "pulled_at_utc": datetime.now(timezone.utc).isoformat(),
        "since_utc": args.since,
        "files": [],
        "missing_symbols": [],
    }

    for symbol in symbols:
        market_symbol = f"{symbol[:-4]}/USDT"
        if market_symbol not in markets:
            manifest["missing_symbols"].append({"symbol": symbol, "reason": f"market_not_found:{market_symbol}"})
            continue
        asset = symbol_to_asset(symbol)
        for timeframe in timeframes:
            rows = fetch_ohlcv_full(exchange, market_symbol, timeframe, since_ms)
            if not rows:
                manifest["missing_symbols"].append({"symbol": symbol, "timeframe": timeframe, "reason": "no_rows"})
                continue
            out_path = DATA_ROOT / f"{asset}_{timeframe}_{CANONICAL_SR_SOURCE}_2022_to_now.csv"
            sha = write_csv(out_path, rows)
            manifest["files"].append(
                {
                    "path": str(out_path),
                    "symbol_requested": market_symbol,
                    "symbol_resolved": market_symbol,
                    "timeframe": timeframe,
                    "rows": len(rows),
                    "first_ts": int(rows[0][0] // 1000),
                    "last_ts": int(rows[-1][0] // 1000),
                    "sha256": sha,
                }
            )
            time.sleep(max(args.sleep_ms, exchange.rateLimit) / 1000.0)

    manifest_path = DATA_ROOT / "provenance_manifest_okx_ccxt_validation_basket.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "manifest": str(manifest_path), "files": len(manifest['files']), "missing": len(manifest['missing_symbols'])}, indent=2))


if __name__ == "__main__":
    main()
