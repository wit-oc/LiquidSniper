#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

BASE_BULK = "https://data.binance.vision/data/spot/monthly/klines"
BASE_API = "https://api.binance.com/api/v3/klines"


def month_iter(start_ym: str, end_ym: str) -> List[str]:
    ys, ms = map(int, start_ym.split("-"))
    ye, me = map(int, end_ym.split("-"))
    out: List[str] = []
    y, m = ys, ms
    while (y < ye) or (y == ye and m <= me):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            y += 1
            m = 1
    return out


def http_get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_bulk_month(symbol: str, interval: str, ym: str) -> List[Tuple[int, str, str, str, str, str]]:
    url = f"{BASE_BULK}/{symbol}/{interval}/{symbol}-{interval}-{ym}.zip"
    try:
        blob = http_get(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise

    rows: List[Tuple[int, str, str, str, str, str]] = []
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = [n for n in zf.namelist() if n.endswith(".csv")]
        if not names:
            return rows
        with zf.open(names[0], "r") as f:
            txt = io.TextIOWrapper(f, encoding="utf-8")
            reader = csv.reader(txt)
            for r in reader:
                if not r:
                    continue
                if r[0].lower() in {"open_time", "timestamp"}:
                    continue
                ts = int(r[0])
                if ts > 10_000_000_000_000:  # some dumps may use microseconds
                    ts //= 1000
                rows.append((ts, r[1], r[2], r[3], r[4], r[5]))
    return rows


def fetch_api(symbol: str, interval: str, start_ms: int, end_ms: int) -> List[Tuple[int, str, str, str, str, str]]:
    out: List[Tuple[int, str, str, str, str, str]] = []
    cur = start_ms
    while cur < end_ms:
        q = urllib.parse.urlencode(
            {
                "symbol": symbol,
                "interval": interval,
                "startTime": cur,
                "endTime": end_ms,
                "limit": 1000,
            }
        )
        blob = http_get(f"{BASE_API}?{q}")
        data = json.loads(blob.decode("utf-8"))
        if not data:
            break
        for r in data:
            out.append((int(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5])))
        nxt = int(data[-1][0])
        if nxt <= cur:
            break
        cur = nxt + 1
    return out


def now_ym() -> str:
    n = datetime.now(timezone.utc)
    return f"{n.year:04d}-{n.month:02d}"


def to_ms(ym: str) -> int:
    dt = datetime.strptime(ym + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def next_month_ms(ym: str) -> int:
    y, m = map(int, ym.split("-"))
    m += 1
    if m > 12:
        y += 1
        m = 1
    dt = datetime(y, m, 1, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch Binance OHLCV from bulk monthly klines with API fallback")
    ap.add_argument("--symbols", default="BTCUSDT,ETHUSDT,SOLUSDT")
    ap.add_argument("--intervals", default="15m,1h,4h")
    ap.add_argument("--start", default="2020-01")
    ap.add_argument("--end", default=now_ym())
    ap.add_argument("--out-dir", default="tools/strategy_sweep/data")
    args = ap.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    intervals = [i.strip() for i in args.intervals.split(",") if i.strip()]
    months = month_iter(args.start, args.end)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    coverage: Dict[str, dict] = {}

    for sym in symbols:
        for itv in intervals:
            key = f"{sym}_{itv}"
            rows: List[Tuple[int, str, str, str, str, str]] = []
            bulk_hits = 0
            for ym in months:
                mrows = fetch_bulk_month(sym, itv, ym)
                if mrows:
                    bulk_hits += 1
                    rows.extend(mrows)

            source = "bulk"
            if not rows:
                source = "api"
                rows = fetch_api(sym, itv, to_ms(args.start), next_month_ms(args.end))

            dedup = {}
            for ts, o, h, l, c, v in rows:
                dedup[ts] = (o, h, l, c, v)
            ts_sorted = sorted(dedup.keys())

            out_file = out_dir / f"{sym}_{itv}.csv"
            with out_file.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["timestamp", "open", "high", "low", "close", "volume"])
                for ts in ts_sorted:
                    o, h, l, c, v = dedup[ts]
                    w.writerow([ts, o, h, l, c, v])

            start_ts = ts_sorted[0] if ts_sorted else None
            end_ts = ts_sorted[-1] if ts_sorted else None
            coverage[key] = {
                "rows": len(ts_sorted),
                "start_ts": start_ts,
                "end_ts": end_ts,
                "start_utc": datetime.fromtimestamp(start_ts / 1000, tz=timezone.utc).isoformat() if start_ts else None,
                "end_utc": datetime.fromtimestamp(end_ts / 1000, tz=timezone.utc).isoformat() if end_ts else None,
                "source": source,
                "bulk_month_hits": bulk_hits,
                "file": str(out_file),
            }
            print(f"{key}: rows={len(ts_sorted)} source={source} bulk_month_hits={bulk_hits}")

    cov_file = out_dir / "coverage.json"
    cov_file.write_text(json.dumps(coverage, indent=2), encoding="utf-8")
    print(f"Wrote coverage: {cov_file}")


if __name__ == "__main__":
    main()
