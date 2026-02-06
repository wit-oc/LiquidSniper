#!/usr/bin/env python3
"""Fetch top-N coins by market cap from CoinMarketCap and write universe artifacts.

Outputs (by default):
- data/universe/top100.json
- data/universe/top100_usdt_pairs.txt

Requires:
- CMC_API_KEY environment variable (CoinMarketCap Pro API key)

Design notes:
- We intentionally avoid third-party deps (requests) for easy bootstrap.
- Treats the CMC list as the source of truth for rank/market cap at fetch time.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Tuple

CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

# Stablecoins to exclude by default.
# (We can refine over time; keep this list conservative.)
DEFAULT_EXCLUDE_SYMBOLS = {
    "USDT",
    "USDC",
    "DAI",
    "TUSD",
    "USDE",
    "FDUSD",
    "USDP",
    "FRAX",
    "LUSD",
    "GUSD",
    "PYUSD",
    "USDJ",
    "USD1",
    "USDS",
}


def http_get_json(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
    return json.loads(body.decode("utf-8"))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=100, help="Top N (non-stables) to keep")
    p.add_argument(
        "--convert",
        default="USD",
        help="CMC convert currency for quotes (default: USD)",
    )
    p.add_argument(
        "--quote",
        default="USDT",
        help="Quote asset for pairs list (default: USDT)",
    )
    p.add_argument(
        "--out-json",
        default="data/universe/top100.json",
        help="Output JSON path",
    )
    p.add_argument(
        "--out-pairs",
        default="data/universe/top100_usdt_pairs.txt",
        help="Output pairs list path (one per line)",
    )
    p.add_argument(
        "--exclude",
        default=",".join(sorted(DEFAULT_EXCLUDE_SYMBOLS)),
        help="Comma-separated base symbols to exclude (default: common stables)",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Print a short debug summary to stderr",
    )
    return p.parse_args()


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def main() -> int:
    args = parse_args()

    api_key = os.environ.get("CMC_API_KEY")
    if not api_key:
        print(
            "Missing CMC_API_KEY env var. Put it in .env and export it (or run: CMC_API_KEY=... python ...)",
            file=sys.stderr,
        )
        return 2

    exclude = {s.strip().upper() for s in args.exclude.split(",") if s.strip()}

    params = {
        "start": "1",
        # Ask for more than we need so we can exclude stables and still get N.
        "limit": str(max(args.limit * 2, 200)),
        "convert": args.convert,
        "sort": "market_cap",
        "sort_dir": "desc",
        "cryptocurrency_type": "all",
    }
    url = CMC_URL + "?" + urllib.parse.urlencode(params)

    data = http_get_json(url, headers={"X-CMC_PRO_API_KEY": api_key, "Accept": "application/json"})

    if "data" not in data or not isinstance(data["data"], list):
        print(f"Unexpected CMC response shape: {list(data.keys())}", file=sys.stderr)
        return 3

    rows: List[Dict[str, Any]] = data["data"]

    picked: List[Dict[str, Any]] = []
    for r in rows:
        sym = (r.get("symbol") or "").upper()
        if not sym:
            continue
        if sym in exclude:
            continue

        quote = (((r.get("quote") or {}).get(args.convert) or {}) if isinstance(r.get("quote"), dict) else {})
        market_cap = quote.get("market_cap")
        price = quote.get("price")

        picked.append(
            {
                "rank": r.get("cmc_rank"),
                "id": r.get("id"),
                "symbol": sym,
                "name": r.get("name"),
                "slug": r.get("slug"),
                "market_cap": market_cap,
                "price": price,
            }
        )

        if len(picked) >= args.limit:
            break

    if len(picked) < args.limit:
        print(f"Only collected {len(picked)} assets after excludes; consider lowering excludes or increasing fetch limit.", file=sys.stderr)

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    out = {
        "source": "coinmarketcap",
        "fetched_at": now,
        "limit": args.limit,
        "exclude": sorted(exclude),
        "assets": picked,
    }

    ensure_parent(args.out_json)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")

    quote_asset = args.quote.upper()
    pairs = [f"{a['symbol']}{quote_asset}" for a in picked if a.get("symbol")]

    ensure_parent(args.out_pairs)
    with open(args.out_pairs, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(p + "\n")

    if args.debug:
        mcaps = [a.get("market_cap") for a in picked if isinstance(a.get("market_cap"), (int, float))]
        min_mcap = min(mcaps) if mcaps else None
        print(f"Wrote {len(picked)} assets → {args.out_json}", file=sys.stderr)
        print(f"Wrote {len(pairs)} pairs → {args.out_pairs}", file=sys.stderr)
        if min_mcap is not None:
            print(f"Min market cap in picked set: {min_mcap:,.0f} {args.convert}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
