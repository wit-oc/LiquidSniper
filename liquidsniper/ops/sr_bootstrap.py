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

DEFAULT_TF_LOOKBACK = {
    "1D": 0,   # 0 => all available history (no decay)
    "4H": 800,
}

DEFAULT_TF_TUNING: dict[str, dict[str, Any]] = {
    # Daily major-mode: sparse, high-significance structural anchors.
    "1D": {
        "cluster_eps": 1.25,
        "reaction_atr_min": 0.60,
        "min_meaningful_touches": 5,
        "min_zone_separation_bps": 250.0,
        "max_zones": 12,
        "require_first_retest_quality": True,
    },
    # 4H operational context: denser than 1D but still controlled.
    "4H": {
        "cluster_eps": 1.10,
        "reaction_atr_min": 0.45,
        "min_meaningful_touches": 4,
        "min_zone_separation_bps": 120.0,
        "max_zones": 20,
        "require_first_retest_quality": False,
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


def _collapse_zones_by_distance(
    zones: list[dict[str, Any]],
    *,
    min_zone_separation_bps: float,
    max_zones_per_symbol: int,
) -> list[dict[str, Any]]:
    if not zones:
        return []

    ranked = sorted(
        zones,
        key=lambda z: (
            -(float(z.get("strength_score") or 0.0)),
            -(int(z.get("meaningful_touch_count") or 0)),
            -(float(z.get("reaction_score") or 0.0)),
        ),
    )

    kept: list[dict[str, Any]] = []
    for z in ranked:
        mid = float(z.get("zone_mid") or 0.0)
        if mid <= 0:
            continue

        too_close = False
        for k in kept:
            kmid = float(k.get("zone_mid") or 0.0)
            if kmid <= 0:
                continue
            dist_bps = abs(mid - kmid) / max(abs(kmid), 1e-9) * 10000.0
            if dist_bps < min_zone_separation_bps:
                too_close = True
                break

        if too_close:
            continue

        kept.append(z)
        if len(kept) >= max_zones_per_symbol:
            break

    return sorted(kept, key=lambda z: float(z.get("zone_mid") or 0.0))


def run_bootstrap(
    *,
    db_path: str,
    artifact_root: str,
    symbols: list[str],
    profile_id: str = "I",
    # Operational (4H / default) tuning
    cluster_eps: float = 1.10,
    reaction_atr_min: float = 0.45,
    min_meaningful_touches: int = 4,
    min_zone_separation_bps: float = 120.0,
    # Daily major-mode tuning (no decay)
    daily_major_mode: bool = True,
    daily_cluster_eps: float = 1.25,
    daily_reaction_atr_min: float = 0.60,
    daily_min_meaningful_touches: int = 5,
    daily_min_zone_separation_bps: float = 250.0,
    daily_max_zones: int = 12,
    daily_require_first_retest_quality: bool = True,
    # Global caps/lookbacks
    max_zones_per_symbol: int = 32,
    max_zones_4h: int = 20,
    lookback_1d: int = 0,
    lookback_4h: int = 800,
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()

    all_zones: list[dict[str, Any]] = []
    all_touches: list[dict[str, Any]] = []
    snapshot: dict[str, Any] = {
        "contract": "zone_snapshot_v1",
        "generated_at": now_iso,
        "profile_id": profile_id,
        "tuning": {
            "cluster_eps": cluster_eps,
            "reaction_atr_min": reaction_atr_min,
            "min_meaningful_touches": min_meaningful_touches,
            "min_zone_separation_bps": min_zone_separation_bps,
            "daily_major_mode": daily_major_mode,
            "daily_cluster_eps": daily_cluster_eps,
            "daily_reaction_atr_min": daily_reaction_atr_min,
            "daily_min_meaningful_touches": daily_min_meaningful_touches,
            "daily_min_zone_separation_bps": daily_min_zone_separation_bps,
            "daily_max_zones": daily_max_zones,
            "daily_require_first_retest_quality": daily_require_first_retest_quality,
            "max_zones_per_symbol": max_zones_per_symbol,
            "max_zones_4h": max_zones_4h,
            "lookback_1d": lookback_1d,
            "lookback_4h": lookback_4h,
        },
        "symbols": {},
    }

    lookback_map = {
        "1D": max(0, int(lookback_1d)),
        "4H": max(0, int(lookback_4h)),
    }

    repo_root = Path.cwd()

    for symbol in symbols:
        tf_map = DEFAULT_SYMBOL_TF_FILES.get(symbol)
        if not tf_map:
            raise ValueError(f"No default CSV map configured for symbol={symbol}")

        symbol_zones_raw: list[dict[str, Any]] = []
        symbol_touches_raw: list[dict[str, Any]] = []
        symbol_zones: list[dict[str, Any]] = []
        symbol_touches: list[dict[str, Any]] = []
        tf_stats: dict[str, Any] = {}
        last_price: float | None = None

        for tf, rel_path in tf_map.items():
            csv_path = repo_root / rel_path
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing CSV source for {symbol} {tf}: {csv_path}")

            candles_all = _load_csv_candles(csv_path)
            lookback_cap = lookback_map.get(tf, DEFAULT_TF_LOOKBACK.get(tf, 0))
            candles = candles_all[-lookback_cap:] if lookback_cap > 0 else candles_all
            if not candles:
                tf_stats[tf] = {
                    "candles_total": len(candles_all),
                    "candles_used": 0,
                    "zones_raw": 0,
                    "zones_kept": 0,
                    "touches_raw": 0,
                    "touches_kept": 0,
                }
                continue

            if tf == "1D" and daily_major_mode:
                tf_cluster_eps = daily_cluster_eps
                tf_reaction_atr_min = daily_reaction_atr_min
                tf_min_meaningful_touches = daily_min_meaningful_touches
                tf_min_sep_bps = daily_min_zone_separation_bps
                tf_max_zones = daily_max_zones
                tf_require_first_retest_quality = daily_require_first_retest_quality
            else:
                tf_cluster_eps = cluster_eps
                tf_reaction_atr_min = reaction_atr_min
                tf_min_meaningful_touches = min_meaningful_touches
                tf_min_sep_bps = min_zone_separation_bps
                tf_max_zones = max_zones_4h if tf == "4H" else max_zones_per_symbol
                tf_require_first_retest_quality = False

            zones_tf_raw, touches_tf_raw = build_zones_for_tf(
                symbol,
                tf,
                candles,
                cluster_eps=tf_cluster_eps,
                reaction_atr_min=tf_reaction_atr_min,
                min_meaningful_touches=tf_min_meaningful_touches,
            )

            if tf_require_first_retest_quality:
                allowed_retest = {"reject", "deviation"}
                zones_tf_prefilter = [
                    z for z in zones_tf_raw
                    if z.get("status") == "confirmed" and str(z.get("first_retest_result") or "") in allowed_retest
                ]
            else:
                zones_tf_prefilter = [z for z in zones_tf_raw if z.get("status") == "confirmed"]

            zones_tf_kept = _collapse_zones_by_distance(
                zones_tf_prefilter,
                min_zone_separation_bps=tf_min_sep_bps,
                max_zones_per_symbol=tf_max_zones,
            )
            kept_ids_tf = {str(z.get("zone_id")) for z in zones_tf_kept}
            touches_tf_kept = [t for t in touches_tf_raw if str(t.get("zone_id")) in kept_ids_tf]

            symbol_zones_raw.extend(zones_tf_raw)
            symbol_touches_raw.extend(touches_tf_raw)
            symbol_zones.extend(zones_tf_kept)
            symbol_touches.extend(touches_tf_kept)

            tf_stats[tf] = {
                "candles_total": len(candles_all),
                "candles_used": len(candles),
                "zones_raw": len(zones_tf_raw),
                "zones_prefilter": len(zones_tf_prefilter),
                "zones_kept": len(zones_tf_kept),
                "touches_raw": len(touches_tf_raw),
                "touches_kept": len(touches_tf_kept),
                "source_csv": str(csv_path),
                "last_close_time": candles[-1]["close_time"],
                "tf_tuning": {
                    "cluster_eps": tf_cluster_eps,
                    "reaction_atr_min": tf_reaction_atr_min,
                    "min_meaningful_touches": tf_min_meaningful_touches,
                    "min_zone_separation_bps": tf_min_sep_bps,
                    "max_zones": tf_max_zones,
                    "require_first_retest_quality": tf_require_first_retest_quality,
                },
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
            "zone_count_raw": len(symbol_zones_raw),
            "zone_count": len(symbol_zones),
            "touch_count_raw": len(symbol_touches_raw),
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

    # Operational (4H/default) knobs
    parser.add_argument("--cluster-eps", type=float, default=1.10, help="ATR-normalized cluster epsilon")
    parser.add_argument("--reaction-atr-min", type=float, default=0.45, help="Min ATR reaction for meaningful touch")
    parser.add_argument("--min-meaningful-touches", type=int, default=4, help="Min meaningful touches for confirmed zone")
    parser.add_argument("--min-zone-separation-bps", type=float, default=120.0, help="Min separation between kept zones")
    parser.add_argument("--max-zones-per-symbol", type=int, default=32, help="Max zones retained per symbol after collapse")
    parser.add_argument("--max-zones-4h", type=int, default=20, help="Max zones retained for 4H after collapse")

    # Daily major-mode knobs
    parser.add_argument("--daily-major-mode", action="store_true", default=True, help="Enable strict daily major-mode filtering")
    parser.add_argument("--no-daily-major-mode", action="store_false", dest="daily_major_mode", help="Disable strict daily major-mode filtering")
    parser.add_argument("--daily-cluster-eps", type=float, default=1.25, help="1D ATR-normalized cluster epsilon")
    parser.add_argument("--daily-reaction-atr-min", type=float, default=0.60, help="1D min ATR reaction for meaningful touch")
    parser.add_argument("--daily-min-meaningful-touches", type=int, default=5, help="1D min meaningful touches")
    parser.add_argument("--daily-min-zone-separation-bps", type=float, default=250.0, help="1D minimum separation between kept zones")
    parser.add_argument("--daily-max-zones", type=int, default=12, help="1D max retained major zones")
    parser.add_argument("--daily-require-first-retest-quality", action="store_true", default=True, help="Require 1D first retest to be reject/deviation")
    parser.add_argument("--no-daily-require-first-retest-quality", action="store_false", dest="daily_require_first_retest_quality", help="Do not require quality first retest for 1D")

    parser.add_argument("--lookback-1d", type=int, default=0, help="1D candles used in bootstrap (0=all available)")
    parser.add_argument("--lookback-4h", type=int, default=800, help="4H candles used in bootstrap")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    snapshot = run_bootstrap(
        db_path=args.db,
        artifact_root=args.artifact_root,
        symbols=symbols,
        profile_id=args.profile.upper(),
        cluster_eps=float(args.cluster_eps),
        reaction_atr_min=float(args.reaction_atr_min),
        min_meaningful_touches=int(args.min_meaningful_touches),
        min_zone_separation_bps=float(args.min_zone_separation_bps),
        daily_major_mode=bool(args.daily_major_mode),
        daily_cluster_eps=float(args.daily_cluster_eps),
        daily_reaction_atr_min=float(args.daily_reaction_atr_min),
        daily_min_meaningful_touches=int(args.daily_min_meaningful_touches),
        daily_min_zone_separation_bps=float(args.daily_min_zone_separation_bps),
        daily_max_zones=int(args.daily_max_zones),
        daily_require_first_retest_quality=bool(args.daily_require_first_retest_quality),
        max_zones_per_symbol=int(args.max_zones_per_symbol),
        max_zones_4h=int(args.max_zones_4h),
        lookback_1d=int(args.lookback_1d),
        lookback_4h=int(args.lookback_4h),
    )
    print(json.dumps({"ok": True, "symbols": list(snapshot["symbols"].keys())}, indent=2))


if __name__ == "__main__":
    main()
