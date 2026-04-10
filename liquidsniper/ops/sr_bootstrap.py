from __future__ import annotations

import argparse
import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from liquidsniper.core.db import init_db
from liquidsniper.core.pair_analytics import summarize_zone_for_pair_analytics
from liquidsniper.core.sr_engine_v2 import build_zones_for_tf, persist_sr_state
from liquidsniper.core.sr_universe import (
    CANONICAL_SR_SOURCE,
    default_sr_symbol_tf_files,
    discover_symbol_tf_files,
    load_validation_basket,
)
from liquidsniper.core.zone_engine_v3 import (
    build_base_candidates,
    build_reaction_candidates,
    build_structure_candidates,
    merge_candidate_zones,
    nearest_four_levels as nearest_four_levels_v3,
    score_zone as score_zone_v3,
    select_daily_majors as select_daily_majors_v3,
    select_operational_zones as select_operational_zones_v3,
)
from liquidsniper.core.zone_selectors import (
    apply_daily_soft_retest_weights as _apply_daily_soft_retest_weights,
    nearest_four_levels,
    select_daily_local_band_representatives as _select_daily_local_band_representatives,
    select_daily_majors,
    select_operational_zones,
)


DEFAULT_SYMBOL_TF_FILES: dict[str, dict[str, str]] = default_sr_symbol_tf_files()

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
        "max_zones": 8,
        "min_strength": 70.0,
        "require_first_retest_quality": True,
    },
    # 4H operational context: denser than 1D but still controlled.
    "4H": {
        "cluster_eps": 1.10,
        "reaction_atr_min": 0.45,
        "min_meaningful_touches": 4,
        "min_zone_separation_bps": 180.0,
        "max_zones": 12,
        "min_strength": 65.0,
        "require_first_retest_quality": False,
    },
}

DEFAULT_SYMBOLS_ARG = "BTCUSDT,ETHUSDT"


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
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _load_bootstrap_config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Bootstrap config file not found: {p}")
    obj = json.loads(p.read_text(encoding="utf-8"))
    return obj if isinstance(obj, dict) else {}


def _resolve_symbol_tf_files_from_config(cfg: dict[str, Any], requested_symbols: list[str]) -> tuple[list[str], dict[str, dict[str, str]], list[str]]:
    cfg_symbols = cfg.get("symbols", {}) if isinstance(cfg, dict) else {}
    if isinstance(cfg_symbols, dict) and cfg_symbols:
        mapping = {
            str(sym).upper(): {str(tf).upper(): str(path) for tf, path in tf_map.items()}
            for sym, tf_map in cfg_symbols.items()
            if isinstance(tf_map, dict)
        }
        selected = [s for s in requested_symbols if s in mapping] if requested_symbols else sorted(mapping.keys())
        return selected, mapping, []

    universe_cfg = cfg.get("universe", {}) if isinstance(cfg, dict) else {}
    basket_path = universe_cfg.get("basket_path") if isinstance(universe_cfg, dict) else None
    source = str(universe_cfg.get("source") or CANONICAL_SR_SOURCE) if isinstance(universe_cfg, dict) else CANONICAL_SR_SOURCE
    basket_symbols = [row.symbol for row in load_validation_basket(basket_path)]
    selected = [s for s in requested_symbols if s in basket_symbols] if requested_symbols else basket_symbols
    mapping, missing = discover_symbol_tf_files(symbols=selected, source=source)
    selected = [s for s in selected if s in mapping]
    return selected, mapping, missing


def _write_run_status(artifact_root: str, payload: dict[str, Any]) -> None:
    status_path = Path(artifact_root) / "sr" / "run_status.json"
    _write_json(status_path, payload)


def _write_shadow_run_status(artifact_root: str, payload: dict[str, Any]) -> None:
    status_path = Path(artifact_root) / "sr" / "shadow" / "v3" / "run_status.json"
    _write_json(status_path, payload)


def _shadow_artifact_dir(artifact_root: str) -> Path:
    return Path(artifact_root) / "sr" / "shadow" / "v3"


def _authoritative_group_key(zone: dict[str, Any]) -> tuple[float, float, str]:
    bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else {}

    def _num(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("inf")

    low = bounds.get("low", zone.get("zone_low"))
    mid = bounds.get("mid", zone.get("zone_mid"))
    zone_id = str(zone.get("zone_id") or "")
    return (_num(low), _num(mid), zone_id)



def _build_authoritative_surface(
    zones: list[dict[str, Any]],
    *,
    entry: float | None,
    tf: str,
    selector_surface: str,
) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    for zone in zones:
        row = summarize_zone_for_pair_analytics(dict(zone), reference_price=entry)
        if not row:
            continue
        row["tf"] = tf
        row["selector_surface"] = selector_surface
        normalized.append(row)

    grouped: dict[str, list[dict[str, Any]]] = {"above": [], "inside": [], "below": []}
    for row in normalized:
        position = str(row.get("relative_position") or "unknown").strip().lower()
        if position in grouped:
            grouped[position].append(row)

    return {
        "contract": "authoritative_levels_view_v1",
        "tf": tf,
        "selector_surface": selector_surface,
        "group_perspective": "zone_relative_to_price",
        "entry": entry,
        "groups": {
            "below_price": sorted(grouped["above"], key=_authoritative_group_key),
            "contains_price": sorted(grouped["inside"], key=_authoritative_group_key),
            "above_price": sorted(grouped["below"], key=_authoritative_group_key),
        },
    }



def _build_v3_shadow_snapshot(
    *,
    run_id: str,
    generated_at: str,
    profile_id: str,
    symbols: list[str],
    symbol_inputs: dict[str, dict[str, Any]],
    daily_major_mode: bool,
    daily_min_strength: float,
    daily_min_zone_separation_bps: float,
    daily_max_zones: int,
    daily_require_first_retest_quality: bool,
    min_strength_4h: float,
    min_zone_separation_bps: float,
    max_zones_4h: int,
) -> dict[str, Any]:
    shadow_snapshot: dict[str, Any] = {
        "contract": "zone_snapshot_v2_shadow",
        "source_version": "zone_engine_v3_shadow_v1",
        "baseline_run_id": run_id,
        "generated_at": generated_at,
        "profile_id": profile_id,
        "mode": "shadow",
        "symbols": {},
    }

    for symbol in symbols:
        payload = symbol_inputs.get(symbol, {})
        tf_inputs = payload.get("timeframes", {}) if isinstance(payload, dict) else {}
        last_price = payload.get("last_price")
        symbol_zones: list[dict[str, Any]] = []
        tf_stats: dict[str, Any] = {}
        major_surface: list[dict[str, Any]] = []
        operational_surface: list[dict[str, Any]] = []

        for tf, tf_payload in tf_inputs.items():
            candles = tf_payload.get("candles") if isinstance(tf_payload, dict) else None
            if not isinstance(candles, list) or not candles:
                continue
            candidate_kwargs = {
                "cluster_eps": tf_payload.get("cluster_eps"),
                "reaction_atr_min": tf_payload.get("reaction_atr_min"),
                "min_meaningful_touches": tf_payload.get("min_meaningful_touches"),
            }
            structure = build_structure_candidates(symbol, tf, candles, **candidate_kwargs)
            base = build_base_candidates(symbol, tf, candles, **candidate_kwargs)
            reaction = build_reaction_candidates(symbol, tf, candles, **candidate_kwargs)
            merged = merge_candidate_zones(structure, base, reaction)
            scored = [score_zone_v3(zone, last_price=float(last_price or 0.0)) for zone in merged]

            if tf == "1D" and daily_major_mode:
                kept = select_daily_majors_v3(
                    scored,
                    min_strength=float(daily_min_strength),
                    min_zone_separation_bps=float(daily_min_zone_separation_bps),
                    max_zones=int(daily_max_zones),
                    strict_retest_quality=bool(daily_require_first_retest_quality),
                    reference_price=float(last_price) if last_price is not None else None,
                )
                major_surface = [dict(zone) for zone in kept]
                selection_mode = "shadow_daily_major_v3"
            else:
                kept = select_operational_zones_v3(
                    scored,
                    min_strength=float(min_strength_4h) if tf == "4H" else 0.0,
                    min_zone_separation_bps=float(min_zone_separation_bps),
                    max_zones=int(max_zones_4h if tf == "4H" else daily_max_zones),
                )
                selection_mode = "shadow_operational_v3"
                if tf == "4H":
                    operational_surface = [dict(zone) for zone in kept]

            for zone in kept:
                zz = dict(zone)
                zz.setdefault("selector_surface", "daily_major" if tf == "1D" else "operational")
                symbol_zones.append(zz)

            tf_stats[tf] = {
                "candles_used": len(candles),
                "candidate_counts": {
                    "structure": len(structure),
                    "base": len(base),
                    "reaction": len(reaction),
                    "merged": len(merged),
                },
                "zones_kept": len(kept),
                "selection_mode": selection_mode,
                "source_csv": tf_payload.get("source_csv"),
                "zones": kept,
            }

        nearest_payload = nearest_four_levels_v3(
            profile_id=profile_id,
            entry=float(last_price or 0.0),
            zones=symbol_zones,
        )
        authoritative_view = {
            "contract": "authoritative_levels_view_v1",
            "source": "shadow_selected_surfaces",
            "entry": last_price,
            "timeframes": {
                "1D": _build_authoritative_surface(
                    major_surface,
                    entry=float(last_price) if last_price is not None else None,
                    tf="1D",
                    selector_surface="daily_major",
                ),
                "4H": _build_authoritative_surface(
                    operational_surface,
                    entry=float(last_price) if last_price is not None else None,
                    tf="4H",
                    selector_surface="operational_4h",
                ),
            },
        }
        shadow_snapshot["symbols"][symbol] = {
            "last_price": last_price,
            "zone_count": len(symbol_zones),
            "timeframes": tf_stats,
            "surfaces": {
                "majors": major_surface,
                "operational": operational_surface,
            },
            "authoritative_view": authoritative_view,
            "nearest": nearest_payload,
        }

    return shadow_snapshot


def run_bootstrap(
    *,
    db_path: str,
    artifact_root: str,
    symbols: list[str],
    profile_id: str = "I",
    symbol_tf_files: dict[str, dict[str, str]] | None = None,
    # Operational (4H / default) tuning
    cluster_eps: float = 1.10,
    reaction_atr_min: float = 0.45,
    min_meaningful_touches: int = 4,
    min_zone_separation_bps: float = 180.0,
    min_strength_4h: float = 65.0,
    # Daily major-mode tuning (no decay)
    daily_major_mode: bool = True,
    daily_cluster_eps: float = 1.25,
    daily_reaction_atr_min: float = 0.60,
    daily_min_meaningful_touches: int = 5,
    daily_min_zone_separation_bps: float = 250.0,
    daily_min_strength: float = 70.0,
    daily_max_zones: int = 8,
    daily_require_first_retest_quality: bool = True,
    shadow_mode_v3: bool = False,
    # Global caps/lookbacks
    max_zones_per_symbol: int = 24,
    max_zones_4h: int = 12,
    lookback_1d: int = 0,
    lookback_4h: int = 800,
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    run_id = f"sr-{uuid.uuid4()}"

    _write_run_status(
        artifact_root,
        {
            "run_id": run_id,
            "state": "running",
            "started_at": now_iso,
            "profile_id": profile_id,
            "symbols": symbols,
            "shadow_mode_v3": bool(shadow_mode_v3),
        },
    )

    all_zones: list[dict[str, Any]] = []
    all_touches: list[dict[str, Any]] = []
    shadow_symbol_inputs: dict[str, dict[str, Any]] = {}
    snapshot: dict[str, Any] = {
        "contract": "zone_snapshot_v1",
        "run_id": run_id,
        "generated_at": now_iso,
        "profile_id": profile_id,
        "tuning": {
            "cluster_eps": cluster_eps,
            "reaction_atr_min": reaction_atr_min,
            "min_meaningful_touches": min_meaningful_touches,
            "min_zone_separation_bps": min_zone_separation_bps,
            "min_strength_4h": min_strength_4h,
            "daily_major_mode": daily_major_mode,
            "daily_cluster_eps": daily_cluster_eps,
            "daily_reaction_atr_min": daily_reaction_atr_min,
            "daily_min_meaningful_touches": daily_min_meaningful_touches,
            "daily_min_zone_separation_bps": daily_min_zone_separation_bps,
            "daily_min_strength": daily_min_strength,
            "daily_max_zones": daily_max_zones,
            "daily_require_first_retest_quality": daily_require_first_retest_quality,
            "shadow_mode_v3": shadow_mode_v3,
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
    tf_files = symbol_tf_files or DEFAULT_SYMBOL_TF_FILES

    for symbol in symbols:
        tf_map = tf_files.get(symbol)
        if not tf_map:
            raise ValueError(f"No CSV map configured for symbol={symbol}")

        symbol_zones_raw: list[dict[str, Any]] = []
        symbol_touches_raw: list[dict[str, Any]] = []
        symbol_zones: list[dict[str, Any]] = []
        symbol_touches: list[dict[str, Any]] = []
        tf_stats: dict[str, Any] = {}
        symbol_shadow_inputs: dict[str, dict[str, Any]] = {}
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

            zones_tf_confirmed = [z for z in zones_tf_raw if z.get("status") == "confirmed"]

            if tf == "1D" and daily_major_mode:
                zones_tf_kept = select_daily_majors(
                    zones_tf_raw,
                    min_strength=float(daily_min_strength),
                    min_zone_separation_bps=tf_min_sep_bps,
                    max_zones=tf_max_zones,
                    strict_retest_quality=tf_require_first_retest_quality,
                    reference_price=float(last_price) if last_price is not None else None,
                )
                zones_tf_scored = [z for z in zones_tf_kept if "selection_score" in z]
                strength_min = float(daily_min_strength)
            else:
                strength_min = float(min_strength_4h) if tf == "4H" else 0.0
                zones_tf_kept = select_operational_zones(
                    zones_tf_raw,
                    min_strength=strength_min,
                    min_zone_separation_bps=tf_min_sep_bps,
                    max_zones=tf_max_zones,
                )
                zones_tf_scored = zones_tf_kept

            zones_tf_prefilter = [z for z in zones_tf_scored if float(z.get("strength_score") or 0.0) >= strength_min]
            zones_tf_collapsed = zones_tf_kept
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
                "zones_collapsed": len(zones_tf_collapsed),
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
                    "min_strength": strength_min,
                    "selection_mode": "daily_band_arbitrated" if (tf == "1D" and daily_major_mode) else "ranked_collapse",
                    "require_first_retest_quality": tf_require_first_retest_quality,
                },
            }
            symbol_shadow_inputs[tf] = {
                "candles": candles,
                "source_csv": str(csv_path),
                "cluster_eps": tf_cluster_eps,
                "reaction_atr_min": tf_reaction_atr_min,
                "min_meaningful_touches": tf_min_meaningful_touches,
            }
            last_price = float(candles[-1]["close"])

        all_zones.extend(symbol_zones)
        all_touches.extend(symbol_touches)

        nearest_payload = nearest_four_levels(
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
        shadow_symbol_inputs[symbol] = {
            "last_price": last_price,
            "timeframes": symbol_shadow_inputs,
        }

    try:
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

        shadow_snapshot_path: str | None = None
        if shadow_mode_v3:
            shadow_snapshot = _build_v3_shadow_snapshot(
                run_id=run_id,
                generated_at=now_iso,
                profile_id=profile_id,
                symbols=symbols,
                symbol_inputs=shadow_symbol_inputs,
                daily_major_mode=daily_major_mode,
                daily_min_strength=daily_min_strength,
                daily_min_zone_separation_bps=daily_min_zone_separation_bps,
                daily_max_zones=daily_max_zones,
                daily_require_first_retest_quality=daily_require_first_retest_quality,
                min_strength_4h=min_strength_4h,
                min_zone_separation_bps=min_zone_separation_bps,
                max_zones_4h=max_zones_4h,
            )
            shadow_dir = _shadow_artifact_dir(artifact_root)
            _write_json(shadow_dir / "bootstrap_snapshot.json", shadow_snapshot)
            for symbol, payload in shadow_snapshot["symbols"].items():
                _write_json(shadow_dir / f"nearest_{symbol}.json", payload["nearest"])
            _write_shadow_run_status(
                artifact_root,
                {
                    "run_id": f"{run_id}:shadow:v3",
                    "baseline_run_id": run_id,
                    "state": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "profile_id": profile_id,
                    "symbols": symbols,
                    "snapshot": str(shadow_dir / "bootstrap_snapshot.json"),
                },
            )
            shadow_snapshot_path = str(shadow_dir / "bootstrap_snapshot.json")

        _write_run_status(
            artifact_root,
            {
                "run_id": run_id,
                "state": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "profile_id": profile_id,
                "symbols": symbols,
                "zone_count": len(all_zones),
                "touch_count": len(all_touches),
                "snapshot": str((Path(artifact_root) / "sr" / "bootstrap_snapshot.json")),
                "shadow_mode_v3": bool(shadow_mode_v3),
                "shadow_snapshot": shadow_snapshot_path,
            },
        )
        return snapshot
    except Exception as exc:
        if shadow_mode_v3:
            _write_shadow_run_status(
                artifact_root,
                {
                    "run_id": f"{run_id}:shadow:v3",
                    "baseline_run_id": run_id,
                    "state": "failed",
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                    "profile_id": profile_id,
                    "symbols": symbols,
                    "error": str(exc),
                },
            )
        _write_run_status(
            artifact_root,
            {
                "run_id": run_id,
                "state": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "profile_id": profile_id,
                "symbols": symbols,
                "error": str(exc),
                "shadow_mode_v3": bool(shadow_mode_v3),
            },
        )
        raise


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap SR snapshots for BTC/ETH verification")
    parser.add_argument("--db", default="data/liquidsniper.sqlite", help="SQLite DB path")
    parser.add_argument("--artifact-root", default="data/artifacts", help="Artifact root directory")
    parser.add_argument("--symbols", default=DEFAULT_SYMBOLS_ARG, help="Comma-separated symbols")
    parser.add_argument("--profile", default="I", choices=["S", "I", "C"], help="Nearest SR profile")
    parser.add_argument("--config", default=None, help="Optional JSON config path for symbol map + tuning")

    # Operational (4H/default) knobs
    parser.add_argument("--cluster-eps", type=float, default=1.10, help="ATR-normalized cluster epsilon")
    parser.add_argument("--reaction-atr-min", type=float, default=0.45, help="Min ATR reaction for meaningful touch")
    parser.add_argument("--min-meaningful-touches", type=int, default=4, help="Min meaningful touches for confirmed zone")
    parser.add_argument("--min-zone-separation-bps", type=float, default=180.0, help="Min separation between kept zones")
    parser.add_argument("--min-strength-4h", type=float, default=65.0, help="Minimum strength score for 4H zones")
    parser.add_argument("--max-zones-per-symbol", type=int, default=24, help="Max zones retained per symbol after collapse")
    parser.add_argument("--max-zones-4h", type=int, default=12, help="Max zones retained for 4H after collapse")

    # Daily major-mode knobs
    parser.add_argument("--daily-major-mode", action="store_true", default=True, help="Enable strict daily major-mode filtering")
    parser.add_argument("--no-daily-major-mode", action="store_false", dest="daily_major_mode", help="Disable strict daily major-mode filtering")
    parser.add_argument("--daily-cluster-eps", type=float, default=1.25, help="1D ATR-normalized cluster epsilon")
    parser.add_argument("--daily-reaction-atr-min", type=float, default=0.60, help="1D min ATR reaction for meaningful touch")
    parser.add_argument("--daily-min-meaningful-touches", type=int, default=5, help="1D min meaningful touches")
    parser.add_argument("--daily-min-zone-separation-bps", type=float, default=250.0, help="1D minimum separation between kept zones")
    parser.add_argument("--daily-min-strength", type=float, default=70.0, help="Minimum strength score for 1D major zones")
    parser.add_argument("--daily-max-zones", type=int, default=8, help="1D max retained major zones")
    parser.add_argument("--daily-require-first-retest-quality", action="store_true", default=True, help="Require 1D first retest to be reject/deviation")
    parser.add_argument("--no-daily-require-first-retest-quality", action="store_false", dest="daily_require_first_retest_quality", help="Do not require quality first retest for 1D")
    parser.add_argument("--shadow-v3", action="store_true", default=False, help="Emit zone_engine_v3 shadow artifacts beside the current baseline path")
    parser.add_argument("--no-shadow-v3", action="store_false", dest="shadow_v3", help="Disable zone_engine_v3 shadow artifacts")

    parser.add_argument("--lookback-1d", type=int, default=0, help="1D candles used in bootstrap (0=all available)")
    parser.add_argument("--lookback-4h", type=int, default=800, help="4H candles used in bootstrap")
    return parser.parse_args()


def _resolve_requested_symbols(symbols_arg: str, cfg: dict[str, Any]) -> list[str]:
    normalized = [s.strip().upper() for s in symbols_arg.split(",") if s.strip()]
    if not cfg:
        return normalized
    cfg_symbols = cfg.get("symbols", {}) if isinstance(cfg, dict) else {}
    universe_cfg = cfg.get("universe", {}) if isinstance(cfg, dict) else {}
    has_cfg_symbol_source = (isinstance(cfg_symbols, dict) and bool(cfg_symbols)) or (isinstance(universe_cfg, dict) and bool(universe_cfg))
    if has_cfg_symbol_source and symbols_arg.replace(" ", "").upper() == DEFAULT_SYMBOLS_ARG:
        return []
    return normalized


def main() -> None:
    args = _parse_args()
    cfg = _load_bootstrap_config(args.config)
    cfg_tuning = cfg.get("tuning", {}) if isinstance(cfg, dict) else {}

    symbols = _resolve_requested_symbols(args.symbols, cfg)
    symbol_tf_files: dict[str, dict[str, str]] | None = None
    if cfg:
        symbols, symbol_tf_files, missing = _resolve_symbol_tf_files_from_config(cfg, symbols)
        if missing:
            print(json.dumps({"missing_flat_files": missing}, indent=2))

    def _cfg(name: str, cli_value: Any) -> Any:
        return cfg_tuning.get(name, cli_value)

    snapshot = run_bootstrap(
        db_path=args.db,
        artifact_root=args.artifact_root,
        symbols=symbols,
        profile_id=args.profile.upper(),
        symbol_tf_files=symbol_tf_files,
        cluster_eps=float(_cfg("cluster_eps", args.cluster_eps)),
        reaction_atr_min=float(_cfg("reaction_atr_min", args.reaction_atr_min)),
        min_meaningful_touches=int(_cfg("min_meaningful_touches", args.min_meaningful_touches)),
        min_zone_separation_bps=float(_cfg("min_zone_separation_bps", args.min_zone_separation_bps)),
        min_strength_4h=float(_cfg("min_strength_4h", args.min_strength_4h)),
        daily_major_mode=bool(_cfg("daily_major_mode", args.daily_major_mode)),
        daily_cluster_eps=float(_cfg("daily_cluster_eps", args.daily_cluster_eps)),
        daily_reaction_atr_min=float(_cfg("daily_reaction_atr_min", args.daily_reaction_atr_min)),
        daily_min_meaningful_touches=int(_cfg("daily_min_meaningful_touches", args.daily_min_meaningful_touches)),
        daily_min_zone_separation_bps=float(_cfg("daily_min_zone_separation_bps", args.daily_min_zone_separation_bps)),
        daily_min_strength=float(_cfg("daily_min_strength", args.daily_min_strength)),
        daily_max_zones=int(_cfg("daily_max_zones", args.daily_max_zones)),
        daily_require_first_retest_quality=bool(_cfg("daily_require_first_retest_quality", args.daily_require_first_retest_quality)),
        shadow_mode_v3=bool(_cfg("shadow_mode_v3", args.shadow_v3)),
        max_zones_per_symbol=int(_cfg("max_zones_per_symbol", args.max_zones_per_symbol)),
        max_zones_4h=int(_cfg("max_zones_4h", args.max_zones_4h)),
        lookback_1d=int(_cfg("lookback_1d", args.lookback_1d)),
        lookback_4h=int(_cfg("lookback_4h", args.lookback_4h)),
    )
    print(json.dumps({"ok": True, "symbols": list(snapshot["symbols"].keys())}, indent=2))


if __name__ == "__main__":
    main()
