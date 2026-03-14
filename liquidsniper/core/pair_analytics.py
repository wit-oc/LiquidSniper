from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from IntradayTrading.engine.htf_phase1 import run_phase1_htf_structure

from liquidsniper.core.zone_engine_v3 import nearest_four_levels

PAIR_ANALYTICS_CONTRACT = "pair_analytics_v2"
STRUCTURE_DIAGNOSTIC_CONTRACT = "market_structure_diagnostic_v2"


def _as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_zone_for_pair_analytics(zone: dict[str, Any] | None) -> dict[str, Any] | None:
    if not zone:
        return None
    bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else {}
    diagnostics = zone.get("diagnostics") if isinstance(zone.get("diagnostics"), dict) else {}
    arbitration = zone.get("arbitration_diagnostics") if isinstance(zone.get("arbitration_diagnostics"), dict) else diagnostics.get("arbitration_diagnostics")
    low = bounds.get("low", zone.get("zone_low"))
    mid = bounds.get("mid", zone.get("zone_mid"))
    high = bounds.get("high", zone.get("zone_high"))
    source_family = zone.get("source_family") or diagnostics.get("source_family")
    candidate_families = zone.get("candidate_families") or diagnostics.get("candidate_families") or zone.get("candidate_sources") or ([] if source_family is None else [source_family])
    family_provenance = zone.get("family_provenance") if isinstance(zone.get("family_provenance"), dict) else diagnostics.get("family_provenance")
    provenance_summary = zone.get("provenance_summary") if isinstance(zone.get("provenance_summary"), dict) else diagnostics.get("provenance_summary")
    price_anchor = zone.get("price_anchor") if isinstance(zone.get("price_anchor"), dict) else diagnostics.get("price_anchor")
    return {
        "zone_id": zone.get("zone_id"),
        "tf": zone.get("tf"),
        "status": zone.get("status"),
        "kind": zone.get("kind") or zone.get("zone_kind"),
        "distance_bps": zone.get("distance_bps"),
        "bounds": {
            "low": low,
            "mid": mid,
            "high": high,
        },
        "strength": zone.get("strength") or zone.get("strength_score"),
        "selection_score": zone.get("selection_score") or diagnostics.get("selection_score"),
        "touch_count": zone.get("touch_count"),
        "meaningful_touch_count": zone.get("meaningful_touch_count"),
        "first_retest_status": zone.get("first_retest_status") or zone.get("first_retest_result"),
        "source_family": source_family,
        "candidate_families": candidate_families,
        "family_stamp_contract": zone.get("family_stamp_contract") or diagnostics.get("family_stamp_contract"),
        "family_provenance": family_provenance or {},
        "provenance_summary": provenance_summary or {},
        "source_versions": zone.get("source_versions") or diagnostics.get("source_versions") or {},
        "generator_contracts": zone.get("generator_contracts") or diagnostics.get("generator_contracts") or {},
        "family_badges": [badge for badge in [source_family, *candidate_families] if badge],
        "price_anchor": price_anchor or {
            "kind": "zone_mid",
            "zone_mid": mid,
            "zone_low": low,
            "zone_high": high,
            "entry": zone.get("entry"),
        },
        "arbitration": arbitration,
        "diagnostics": diagnostics,
    }


def build_market_structure_diagnostic(*, candles: list[dict[str, Any]], tf: str) -> dict[str, Any]:
    contract = {
        "contract": STRUCTURE_DIAGNOSTIC_CONTRACT,
        "timeframe": tf,
    }
    if len(candles) < 8:
        return {
            **contract,
            "status": "insufficient_candles",
            "trend": None,
            "confidence": None,
            "last_transition_reason": None,
            "active_choch_level": None,
            "event_counts": {},
            "latest_event": None,
            "diagnostics": {"reason": "need >= 8 candles for phase1 structure adapter"},
        }

    highs = [_as_float(row.get("high")) or 0.0 for row in candles]
    lows = [_as_float(row.get("low")) or 0.0 for row in candles]
    closes = [_as_float(row.get("close")) or 0.0 for row in candles]
    bars, events, _swings = run_phase1_htf_structure(
        highs,
        lows,
        closes,
        left=2,
        right=2,
        n_init=min(25, len(candles)),
        break_min_frac_of_candle=0.20,
        choch_break_min_frac_of_candle=0.15,
        strict_gating=False,
        bos_require_fresh_cross=True,
        enable_continuation_break=True,
    )
    latest_bar = bars[-1] if bars else {}
    event_counts: dict[str, int] = {}
    for event in events:
        key = str(event.get("event") or "")
        if key:
            event_counts[key] = event_counts.get(key, 0) + 1
    latest_event = events[-1] if events else None
    return {
        **contract,
        "status": "ok",
        "trend": latest_bar.get("regime_direction"),
        "confidence": latest_bar.get("regime_confidence"),
        "last_transition_reason": latest_bar.get("regime_reason") or latest_bar.get("transition_reason"),
        "active_choch_level": latest_bar.get("active_choch_level"),
        "protected_high": latest_bar.get("protected_high"),
        "protected_low": latest_bar.get("protected_low"),
        "event_counts": event_counts,
        "latest_event": latest_event,
        "diagnostics": {
            "bar_index": latest_bar.get("index"),
            "bos_check": latest_bar.get("bos_check"),
            "choch_check": latest_bar.get("choch_check"),
            "cb_check": latest_bar.get("cb_check"),
        },
    }


def build_pair_analytics_snapshot(
    *,
    symbol: str,
    profile_id: str,
    entry: float,
    zones: list[dict[str, Any]],
    candles_by_tf: dict[str, list[dict[str, Any]]] | None = None,
    timeframe_availability: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    nearest = nearest_four_levels(profile_id=profile_id, entry=entry, zones=zones)
    zone_by_id = {str(z.get("zone_id") or ""): z for z in zones}

    def _hydrate_nearest(zone: dict[str, Any] | None) -> dict[str, Any] | None:
        if not zone:
            return None
        source = zone_by_id.get(str(zone.get("zone_id") or ""), {})
        merged = dict(source)
        merged.update(zone)
        if not isinstance(merged.get("price_anchor"), dict) and isinstance(source.get("price_anchor"), dict):
            merged["price_anchor"] = source.get("price_anchor")
        if merged.get("source_family") is None and source.get("source_family") is not None:
            merged["source_family"] = source.get("source_family")
        if not merged.get("candidate_sources") and source.get("candidate_sources") is not None:
            merged["candidate_sources"] = source.get("candidate_sources")
        if not merged.get("candidate_families") and source.get("candidate_families") is not None:
            merged["candidate_families"] = source.get("candidate_families")
        if not isinstance(merged.get("family_provenance"), dict) and source.get("family_provenance") is not None:
            merged["family_provenance"] = source.get("family_provenance")
        if not isinstance(merged.get("provenance_summary"), dict) and source.get("provenance_summary") is not None:
            merged["provenance_summary"] = source.get("provenance_summary")
        if merged.get("family_stamp_contract") is None and source.get("family_stamp_contract") is not None:
            merged["family_stamp_contract"] = source.get("family_stamp_contract")
        if not isinstance(merged.get("source_versions"), dict) and source.get("source_versions") is not None:
            merged["source_versions"] = source.get("source_versions")
        if not isinstance(merged.get("generator_contracts"), dict) and source.get("generator_contracts") is not None:
            merged["generator_contracts"] = source.get("generator_contracts")
        if not isinstance(merged.get("arbitration_diagnostics"), dict) and source.get("arbitration_diagnostics") is not None:
            merged["arbitration_diagnostics"] = source.get("arbitration_diagnostics")
        return merged

    majors = sorted(
        [z for z in zones if str(z.get("tf") or "").upper() == "1D"],
        key=lambda z: float(z.get("selection_score") or z.get("strength_score") or 0.0),
        reverse=True,
    )
    operational = sorted(
        [z for z in zones if str(z.get("tf") or "").upper() == "4H"],
        key=lambda z: float(z.get("selection_score") or z.get("strength_score") or 0.0),
        reverse=True,
    )
    structure_by_tf: dict[str, Any] = {}
    availability = {str(tf).upper(): dict(payload) for tf, payload in (timeframe_availability or {}).items()}
    for tf, candles in (candles_by_tf or {}).items():
        tf_key = str(tf).upper()
        structure_by_tf[tf_key] = build_market_structure_diagnostic(candles=candles, tf=tf_key)
        availability.setdefault(tf_key, {})
        availability[tf_key].update({
            "timeframe": tf_key,
            "status": "ready",
            "candle_count": len(candles),
            "diagnostic_contract": STRUCTURE_DIAGNOSTIC_CONTRACT,
        })

    return {
        "contract": PAIR_ANALYTICS_CONTRACT,
        "symbol": symbol,
        "profile_id": profile_id,
        "entry": entry,
        "sr": {
            "nearest_four": nearest,
            "nearest_levels": {
                "nearest_support": summarize_zone_for_pair_analytics(_hydrate_nearest(nearest.get("nearest_support"))),
                "next_support": summarize_zone_for_pair_analytics(_hydrate_nearest(nearest.get("next_support"))),
                "nearest_resistance": summarize_zone_for_pair_analytics(_hydrate_nearest(nearest.get("nearest_resistance"))),
                "next_resistance": summarize_zone_for_pair_analytics(_hydrate_nearest(nearest.get("next_resistance"))),
            },
            "majors": [summarize_zone_for_pair_analytics(z) for z in majors[:8]],
            "operational": [summarize_zone_for_pair_analytics(z) for z in operational[:8]],
        },
        "market_structure": {
            "contract": STRUCTURE_DIAGNOSTIC_CONTRACT,
            "timeframes": structure_by_tf,
            "available_timeframes": sorted(structure_by_tf.keys()),
            "availability": [availability[key] for key in sorted(availability.keys())],
        },
    }


def load_candles_from_csv(path: str | Path, *, limit: int = 600) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(
                {
                    "open": _as_float(row.get("open")),
                    "high": _as_float(row.get("high")),
                    "low": _as_float(row.get("low")),
                    "close": _as_float(row.get("close")),
                    "volume": _as_float(row.get("volume")),
                    "timestamp": row.get("timestamp") or row.get("ts") or row.get("datetime"),
                }
            )
    if limit > 0 and len(rows) > limit:
        rows = rows[-limit:]
    return rows
