from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from liquidsniper.core.db import init_db
from liquidsniper.core.sr_engine_v2 import (
    build_zones_for_tf,
    nearest_sr_levels_v1,
    persist_sr_state,
)


DEFAULT_SYMBOL_TF_FILES: dict[str, dict[str, str]] = {
    "BTCUSDT": {
        "1D": "IntradayTrading/data/btc_1d_blofin_derived_from_1h_2022_to_now.csv",
        "4H": "IntradayTrading/data/btc_4h_blofin_derived_from_1h_2022_to_now.csv",
    },
    "ETHUSDT": {
        "1D": "IntradayTrading/data/eth_1d_blofin_derived_from_1h_2022_to_now.csv",
        "4H": "IntradayTrading/data/eth_4h_blofin_derived_from_1h_2022_to_now.csv",
    },
}


def _iso_from_unix(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _load_csv_candles(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = float(row.get("timestamp") or 0.0)
            if ts <= 0:
                continue
            rows.append(
                {
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "close_time": _iso_from_unix(ts),
                }
            )
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_bootstrap(*, db_path: str, artifact_root: str, symbols: list[str], profile_id: str = "I") -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()

    all_zones: list[dict[str, Any]] = []
    all_touches: list[dict[str, Any]] = []
    snapshot: dict[str, Any] = {
        "contract": "zone_snapshot_v1",
        "generated_at": now_iso,
        "profile_id": profile_id,
        "symbols": {},
    }

    repo_root = Path.cwd()

    for symbol in symbols:
        tf_map = DEFAULT_SYMBOL_TF_FILES.get(symbol)
        if not tf_map:
            raise ValueError(f"No default CSV map configured for symbol={symbol}")

        symbol_zones: list[dict[str, Any]] = []
        symbol_touches: list[dict[str, Any]] = []
        tf_stats: dict[str, Any] = {}
        last_price: float | None = None

        for tf, rel_path in tf_map.items():
            csv_path = repo_root / rel_path
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing CSV source for {symbol} {tf}: {csv_path}")

            candles = _load_csv_candles(csv_path)
            if not candles:
                tf_stats[tf] = {"candles": 0, "zones": 0, "touches": 0}
                continue

            zones, touches = build_zones_for_tf(symbol, tf, candles)
            symbol_zones.extend(zones)
            symbol_touches.extend(touches)
            tf_stats[tf] = {
                "candles": len(candles),
                "zones": len(zones),
                "touches": len(touches),
                "source_csv": str(csv_path),
                "last_close_time": candles[-1]["close_time"],
            }
            last_price = float(candles[-1]["close"])

        all_zones.extend(symbol_zones)
        all_touches.extend(symbol_touches)

        nearest_payload = nearest_sr_levels_v1(
            profile_id=profile_id,
            entry=float(last_price or 0.0),
            zones=symbol_zones,
        )

        snapshot["symbols"][symbol] = {
            "last_price": last_price,
            "zone_count": len(symbol_zones),
            "touch_count": len(symbol_touches),
            "timeframes": tf_stats,
            "nearest": nearest_payload,
        }

    conn = init_db(db_path)
    try:
        with conn:
            for symbol in symbols:
                conn.execute("DELETE FROM sr_zone_touches WHERE symbol = ?;", (symbol,))
                conn.execute("DELETE FROM sr_zones WHERE symbol = ?;", (symbol,))
        persist_sr_state(conn, all_zones, all_touches)
    finally:
        conn.close()

    artifact_dir = Path(artifact_root) / "sr"
    _write_json(artifact_dir / "bootstrap_snapshot.json", snapshot)
    for symbol, payload in snapshot["symbols"].items():
        _write_json(artifact_dir / f"nearest_{symbol}.json", payload["nearest"])

    return snapshot


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap SR snapshots for BTC/ETH verification")
    parser.add_argument("--db", default="data/liquidsniper.sqlite", help="SQLite DB path")
    parser.add_argument("--artifact-root", default="data/artifacts", help="Artifact root directory")
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT", help="Comma-separated symbols")
    parser.add_argument("--profile", default="I", choices=["S", "I", "C"], help="Nearest SR profile")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    snapshot = run_bootstrap(
        db_path=args.db,
        artifact_root=args.artifact_root,
        symbols=symbols,
        profile_id=args.profile.upper(),
    )
    print(json.dumps({"ok": True, "symbols": list(snapshot["symbols"].keys())}, indent=2))


if __name__ == "__main__":
    main()
