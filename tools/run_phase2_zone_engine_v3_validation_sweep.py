from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from liquidsniper.core.pair_analytics import build_pair_analytics_snapshot, load_candles_from_csv
from liquidsniper.core.sr_universe import discover_symbol_tf_files, resolve_market_structure_csv
from liquidsniper.ops.sr_bootstrap import run_bootstrap

MVP_13_PAIR_UNIVERSE = [
    "BTCUSDT",
    "ETHUSDT",
    "XRPUSDT",
    "SOLUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "BCHUSDT",
    "LINKUSDT",
    "XLMUSDT",
    "LTCUSDT",
    "AVAXUSDT",
    "HBARUSDT",
    "DOTUSDT",
]
REQUESTED_STRUCTURE_TFS = ("1H", "4H", "1D")
CHART_TFS = ("4H", "1D")


def repo_root() -> Path:
    return ROOT


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def fetch_symbol_zones(conn: sqlite3.Connection, symbol: str) -> list[dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT *
        FROM sr_zones
        WHERE symbol = ?
        ORDER BY
            CASE WHEN tf = '1D' THEN 0 WHEN tf = '4H' THEN 1 ELSE 2 END,
            selection_score DESC,
            strength_score DESC,
            updated_ts DESC
        """,
        (symbol,),
    ).fetchall()
    return [dict(row) for row in rows]


def build_structure_inputs(symbol: str) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    candles_by_tf: dict[str, list[dict[str, Any]]] = {}
    availability: dict[str, dict[str, Any]] = {}
    for tf in REQUESTED_STRUCTURE_TFS:
        path = resolve_market_structure_csv(symbol, tf)
        if path is None:
            availability[tf] = {
                "timeframe": tf,
                "status": "missing_source",
                "reason": "no matching candle csv found",
            }
            continue
        try:
            candles = load_candles_from_csv(path, limit=600)
        except Exception as exc:  # pragma: no cover - exercised in real runs
            availability[tf] = {
                "timeframe": tf,
                "status": "load_failed",
                "reason": str(exc),
                "path": str(path),
            }
            continue
        candles_by_tf[tf] = candles
        availability[tf] = {
            "timeframe": tf,
            "status": "ready",
            "path": str(path.relative_to(repo_root()) if path.is_absolute() else path),
            "candle_count": len(candles),
        }
    return candles_by_tf, availability


def build_chart_ready_payload(symbol: str, entry: float, analytics: dict[str, Any], zones: list[dict[str, Any]]) -> dict[str, Any]:
    sr_levels = analytics.get("sr", {}).get("nearest_levels", {})
    highlighted_ids = [
        str(zone.get("zone_id"))
        for zone in [
            sr_levels.get("nearest_support"),
            sr_levels.get("next_support"),
            sr_levels.get("nearest_resistance"),
            sr_levels.get("next_resistance"),
        ]
        if isinstance(zone, dict) and zone.get("zone_id")
    ]
    charts: dict[str, Any] = {}
    for tf in CHART_TFS:
        path = resolve_market_structure_csv(symbol, tf)
        tf_zones = [z for z in zones if str(z.get("tf") or "").upper() == tf]
        charts[tf] = {
            "timeframe": tf,
            "entry": entry,
            "csv_path": str(path.relative_to(repo_root()) if path and path.is_absolute() else path) if path else None,
            "eligible_zone_ids": [str(z.get("zone_id")) for z in tf_zones if z.get("zone_id")],
            "highlighted_zone_ids": [zid for zid in highlighted_ids if zid in {str(z.get('zone_id')) for z in tf_zones}],
            "candle_limit": 220,
        }
    return {
        "contract": "audit_chart_inputs_v1",
        "symbol": symbol,
        "entry": entry,
        "highlighted_zone_ids": highlighted_ids,
        "charts": charts,
    }


def build_pair_artifact(conn: sqlite3.Connection, symbol: str, profile_id: str) -> dict[str, Any]:
    zones = fetch_symbol_zones(conn, symbol)
    if not zones:
        raise ValueError(f"No persisted SR zones found for {symbol}")
    entry = float(zones[0].get("zone_mid") or 0.0)
    candles_by_tf, availability = build_structure_inputs(symbol)
    analytics = build_pair_analytics_snapshot(
        symbol=symbol,
        profile_id=profile_id,
        entry=entry,
        zones=zones,
        candles_by_tf=candles_by_tf,
        timeframe_availability=availability,
    )
    chart_ready = build_chart_ready_payload(symbol, entry, analytics, zones)
    nearest = analytics.get("sr", {}).get("nearest_levels", {})
    return {
        "contract": "zone_engine_v3_validation_pair_artifact_v1",
        "symbol": symbol,
        "entry": entry,
        "source_corpus": {
            "contract": "canonical_okx_ccxt_1d_4h_v1",
            "1D": availability.get("1D", {}),
            "4H": availability.get("4H", {}),
        },
        "pair_analytics": analytics,
        "audit_chart_inputs": chart_ready,
        "review_focus": {
            "nearest_support": nearest.get("nearest_support", {}).get("zone_id") if isinstance(nearest.get("nearest_support"), dict) else None,
            "next_support": nearest.get("next_support", {}).get("zone_id") if isinstance(nearest.get("next_support"), dict) else None,
            "nearest_resistance": nearest.get("nearest_resistance", {}).get("zone_id") if isinstance(nearest.get("nearest_resistance"), dict) else None,
            "next_resistance": nearest.get("next_resistance", {}).get("zone_id") if isinstance(nearest.get("next_resistance"), dict) else None,
            "majors_count": len(analytics.get("sr", {}).get("majors", [])),
            "operational_count": len(analytics.get("sr", {}).get("operational", [])),
            "market_structure_availability": analytics.get("market_structure", {}).get("availability", []),
        },
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _relativize_path(value: Any) -> Any:
    if not isinstance(value, str) or not value:
        return value
    path = Path(value)
    try:
        return str(path.relative_to(repo_root())) if path.is_absolute() else value
    except ValueError:
        return value


def build_summary(run_dir: Path, symbols: list[str], bootstrap_snapshot: dict[str, Any], pair_paths: dict[str, str]) -> dict[str, Any]:
    summary_rows: list[dict[str, Any]] = []
    for symbol in symbols:
        snap = bootstrap_snapshot.get("symbols", {}).get(symbol, {})
        pair_rel = pair_paths[symbol]
        tfs = snap.get("timeframes", {})
        summary_rows.append(
            {
                "symbol": symbol,
                "pair_artifact": pair_rel,
                "last_price": snap.get("last_price"),
                "zone_count": snap.get("zone_count"),
                "touch_count": snap.get("touch_count"),
                "source_1d": _relativize_path(tfs.get("1D", {}).get("source_csv")),
                "source_4h": _relativize_path(tfs.get("4H", {}).get("source_csv")),
                "candles_1d": tfs.get("1D", {}).get("candles_used"),
                "candles_4h": tfs.get("4H", {}).get("candles_used"),
            }
        )
    return {
        "contract": "zone_engine_v3_validation_sweep_index_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir.relative_to(repo_root())),
        "universe": symbols,
        "bootstrap_snapshot": str((run_dir / "sr" / "bootstrap_snapshot.json").relative_to(repo_root())),
        "pairs": summary_rows,
    }


def write_markdown_index(run_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Phase 2 Zone Engine V3 MVP Validation Sweep",
        "",
        f"Run dir: `{summary['run_dir']}`",
        "",
        "## Universe",
    ]
    for symbol in summary["universe"]:
        lines.append(f"- {symbol}")
    lines.extend(["", "## Pair artifacts"])
    for row in summary["pairs"]:
        lines.append(
            f"- {row['symbol']}: `{row['pair_artifact']}` | "
            f"1D `{row['source_1d']}` | 4H `{row['source_4h']}` | "
            f"zones {row['zone_count']} | touches {row['touch_count']}"
        )
    (run_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Generate deterministic Phase 2 Zone Engine V3 validation sweep artifacts")
    ap.add_argument("--db", default="data/liquidsniper.sqlite")
    ap.add_argument("--artifact-root", default="artifacts/validation")
    ap.add_argument("--profile", default="I", choices=["S", "I", "C"])
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    symbols = list(MVP_13_PAIR_UNIVERSE)
    mapping, missing = discover_symbol_tf_files(symbols=symbols)
    if missing:
        raise SystemExit(json.dumps({"missing_flat_files": missing}, indent=2))
    if sorted(mapping.keys()) != sorted(symbols):
        raise SystemExit(json.dumps({"resolved_symbols": sorted(mapping.keys()), "expected_symbols": symbols}, indent=2))

    run_dir = repo_root() / args.artifact_root / f"zone_engine_v3_mvp_validation_sweep_{utc_stamp()}"
    run_dir.mkdir(parents=True, exist_ok=True)

    bootstrap_snapshot = run_bootstrap(
        db_path=args.db,
        artifact_root=str(run_dir),
        symbols=symbols,
        profile_id=args.profile,
        symbol_tf_files=mapping,
    )

    conn = sqlite3.connect(args.db)
    try:
        pair_paths: dict[str, str] = {}
        for symbol in symbols:
            payload = build_pair_artifact(conn, symbol, args.profile)
            pair_path = run_dir / "pairs" / f"{symbol}.json"
            write_json(pair_path, payload)
            pair_paths[symbol] = str(pair_path.relative_to(repo_root()))
    finally:
        conn.close()

    summary = build_summary(run_dir, symbols, bootstrap_snapshot, pair_paths)
    write_json(run_dir / "index.json", summary)
    write_markdown_index(run_dir, summary)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
