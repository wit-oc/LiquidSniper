from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from IntradayTrading.engine.phase1_contract import (
    PHASE1_STRUCTURE_CONTRACT,
    PHASE1_STRUCTURE_CONTRACT_LEGACY,
    PHASE1_STRUCTURE_PROFILE_CANONICAL,
    PHASE1_STRUCTURE_PROFILE_LEGACY,
    run_phase1_structure_contract_from_candles,
)

from liquidsniper.core.zone_engine_v3 import nearest_four_levels
from liquidsniper.core.zone_primitives import ROLE_SEMANTICS_CONTRACT, derive_role_semantics

PAIR_ANALYTICS_CONTRACT = "pair_analytics_v3"
STRUCTURE_DIAGNOSTIC_CONTRACT = "market_structure_diagnostic_v2"
STRUCTURE_COMPARISON_CONTRACT = "market_structure_comparison_v1"
DISPLAY_WIDTH_FLOOR_CONTRACT = "display_width_floor_v1"


def _as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _apply_low_price_daily_display_floor(
    *,
    tf: str | None,
    display_bounds_kind: str | None,
    effective_bounds: dict[str, Any],
    macro_bounds: dict[str, Any],
    reference_price: float | None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    normalized_tf = str(tf or "").upper()
    if normalized_tf != "1D" or display_bounds_kind != "core":
        return effective_bounds, None

    price_anchor = _as_float(reference_price)
    if price_anchor is None or price_anchor <= 0 or price_anchor > 1.0:
        return effective_bounds, None

    low = _as_float(effective_bounds.get("low"))
    high = _as_float(effective_bounds.get("high"))
    mid = _as_float(effective_bounds.get("mid"))
    macro_low = _as_float(macro_bounds.get("low"))
    macro_high = _as_float(macro_bounds.get("high"))
    macro_mid = _as_float(macro_bounds.get("mid"))
    if None in {low, high, macro_low, macro_high}:
        return effective_bounds, None
    if high <= low or macro_high <= macro_low:
        return effective_bounds, None

    core_width_bps = (high - low) / price_anchor * 10000.0
    macro_width_bps = (macro_high - macro_low) / price_anchor * 10000.0
    if core_width_bps >= 120.0 or macro_width_bps < 1000.0:
        return effective_bounds, None

    target_width_bps = min(180.0, max(120.0, macro_width_bps * 0.05))
    target_half_width = (target_width_bps / 10000.0 * price_anchor) / 2.0
    center = mid if mid is not None else (macro_mid if macro_mid is not None else ((low + high) / 2.0))
    floored_low = max(macro_low, center - target_half_width)
    floored_high = min(macro_high, center + target_half_width)
    if floored_high <= floored_low:
        return effective_bounds, None

    adjusted = {
        "low": round(floored_low, 8),
        "mid": round((floored_low + floored_high) / 2.0, 8),
        "high": round(floored_high, 8),
    }
    diagnostics = {
        "contract": DISPLAY_WIDTH_FLOOR_CONTRACT,
        "applied": True,
        "reason": "low_price_daily_core_floor",
        "target_width_bps": round(target_width_bps, 4),
        "original_width_bps": round(core_width_bps, 4),
        "macro_width_bps": round(macro_width_bps, 4),
        "price_anchor": round(price_anchor, 8),
        "raw_display_bounds": {
            "low": round(low, 8),
            "mid": round(mid if mid is not None else ((low + high) / 2.0), 8),
            "high": round(high, 8),
        },
    }
    return adjusted, diagnostics


def summarize_zone_for_pair_analytics(
    zone: dict[str, Any] | None,
    *,
    reference_price: float | None = None,
) -> dict[str, Any] | None:
    if not zone:
        return None
    bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else {}
    diagnostics = zone.get("diagnostics") if isinstance(zone.get("diagnostics"), dict) else {}
    arbitration = zone.get("arbitration_diagnostics") if isinstance(zone.get("arbitration_diagnostics"), dict) else diagnostics.get("arbitration_diagnostics")
    low = bounds.get("low", zone.get("zone_low"))
    mid = bounds.get("mid", zone.get("zone_mid"))
    high = bounds.get("high", zone.get("zone_high"))
    core_low = _as_float(zone.get("core_low"))
    core_high = _as_float(zone.get("core_high"))
    core_mid = _as_float(zone.get("core_mid"))
    core_definition = zone.get("core_definition")
    source_family = zone.get("source_family") or diagnostics.get("source_family")
    candidate_families = zone.get("candidate_families") or diagnostics.get("candidate_families") or zone.get("candidate_sources") or ([] if source_family is None else [source_family])
    family_provenance = zone.get("family_provenance") if isinstance(zone.get("family_provenance"), dict) else diagnostics.get("family_provenance")
    provenance_summary = zone.get("provenance_summary") if isinstance(zone.get("provenance_summary"), dict) else diagnostics.get("provenance_summary")
    price_anchor = zone.get("price_anchor") if isinstance(zone.get("price_anchor"), dict) else diagnostics.get("price_anchor")
    semantics = {
        "origin_kind": zone.get("origin_kind") or zone.get("zone_kind"),
        "current_role": zone.get("current_role"),
        "relative_position": zone.get("relative_position"),
        "role_semantics_contract": zone.get("role_semantics_contract"),
    }
    if reference_price is not None and (not semantics["current_role"] or not semantics["relative_position"]):
        derived = derive_role_semantics(zone=zone, price=float(reference_price))
        semantics = {
            "origin_kind": semantics["origin_kind"] or derived.get("origin_kind") or zone.get("zone_kind"),
            "current_role": semantics["current_role"] or derived.get("current_role"),
            "relative_position": semantics["relative_position"] or derived.get("relative_position"),
            "role_semantics_contract": semantics["role_semantics_contract"] or derived.get("role_semantics_contract") or ROLE_SEMANTICS_CONTRACT,
        }
    primary_role = semantics["current_role"] or zone.get("kind") or zone.get("zone_kind")
    macro_bounds = {
        "low": _as_float(zone.get("zone_low")),
        "mid": _as_float(zone.get("zone_mid")),
        "high": _as_float(zone.get("zone_high")),
    }
    display_bounds_kind = zone.get("display_bounds_kind")
    if display_bounds_kind not in {"core", "macro"}:
        tf = str(zone.get("tf") or "").upper()
        display_bounds_kind = "core" if tf == "1D" and core_low is not None and core_high is not None else "macro"
    effective_bounds = {
        "low": low,
        "mid": mid,
        "high": high,
    }
    if display_bounds_kind == "core" and core_low is not None and core_high is not None:
        effective_bounds = {
            "low": core_low,
            "mid": core_mid,
            "high": core_high,
        }
    effective_bounds, display_width_floor = _apply_low_price_daily_display_floor(
        tf=zone.get("tf"),
        display_bounds_kind=display_bounds_kind,
        effective_bounds=effective_bounds,
        macro_bounds=macro_bounds,
        reference_price=reference_price,
    )

    return {
        "zone_id": zone.get("zone_id"),
        "tf": zone.get("tf"),
        "status": zone.get("status"),
        "kind": primary_role,
        "origin_kind": semantics["origin_kind"] or zone.get("zone_kind"),
        "current_role": semantics["current_role"],
        "relative_position": semantics["relative_position"],
        "role_semantics_contract": semantics["role_semantics_contract"],
        "role_semantics": {
            "origin_kind": semantics["origin_kind"] or zone.get("zone_kind"),
            "current_role": semantics["current_role"],
            "relative_position": semantics["relative_position"],
            "review_label": primary_role,
            "contract": semantics["role_semantics_contract"],
        },
        "distance_bps": zone.get("distance_bps"),
        "bounds": effective_bounds,
        "macro_bounds": macro_bounds,
        "core_bounds": {
            "low": core_low,
            "mid": core_mid,
            "high": core_high,
        }
        if any(value is not None for value in (core_low, core_mid, core_high))
        else None,
        "display_bounds_kind": display_bounds_kind,
        "display_width_floor": display_width_floor,
        "display_width_floor_applied": bool(display_width_floor),
        "core_definition": core_definition,
        "strength": zone.get("strength") or zone.get("strength_score"),
        "selection_score": zone.get("selection_score") or diagnostics.get("selection_score"),
        "selector_surface": zone.get("selector_surface"),
        "selector_status": zone.get("selector_status"),
        "selector_reason": zone.get("selector_reason"),
        "selector_rank": zone.get("selector_rank"),
        "touch_count": zone.get("touch_count"),
        "meaningful_touch_count": zone.get("meaningful_touch_count"),
        "first_retest_status": zone.get("first_retest_status") or zone.get("first_retest_result"),
        "source_family": source_family,
        "candidate_families": candidate_families,
        "family_stamp_contract": zone.get("family_stamp_contract") or diagnostics.get("family_stamp_contract"),
        "provenance": {
            "source_family": source_family,
            "candidate_families": candidate_families,
            "family_stamp_contract": zone.get("family_stamp_contract") or diagnostics.get("family_stamp_contract"),
            "family_provenance": family_provenance or {},
            "provenance_summary": provenance_summary or {},
            "source_versions": zone.get("source_versions") or diagnostics.get("source_versions") or {},
            "generator_contracts": zone.get("generator_contracts") or diagnostics.get("generator_contracts") or {},
        },
        "family_provenance": family_provenance or {},
        "provenance_summary": provenance_summary or {},
        "source_versions": zone.get("source_versions") or diagnostics.get("source_versions") or {},
        "generator_contracts": zone.get("generator_contracts") or diagnostics.get("generator_contracts") or {},
        "family_badges": [badge for badge in [source_family, *candidate_families] if badge],
        "local_cluster_contract": zone.get("local_cluster_contract"),
        "local_cluster_role": zone.get("local_cluster_role"),
        "local_cluster_id": zone.get("local_cluster_id"),
        "local_cluster_member_count": zone.get("local_cluster_member_count"),
        "local_cluster_member_ids": zone.get("local_cluster_member_ids"),
        "local_cluster_demoted_ids": zone.get("local_cluster_demoted_ids"),
        "local_cluster_bounds": zone.get("local_cluster_bounds"),
        "local_cluster_demotions": zone.get("local_cluster_demotions"),
        "local_cluster_competition_basis": zone.get("local_cluster_competition_basis"),
        "local_cluster_representative_weight": zone.get("local_cluster_representative_weight"),
        "local_cluster_representative_diagnostics": zone.get("local_cluster_representative_diagnostics"),
        "daily_pocket_contract": zone.get("daily_pocket_contract"),
        "daily_pocket_id": zone.get("daily_pocket_id"),
        "daily_pocket_member_count": zone.get("daily_pocket_member_count"),
        "daily_pocket_member_ids": zone.get("daily_pocket_member_ids"),
        "daily_pocket_demoted_ids": zone.get("daily_pocket_demoted_ids"),
        "daily_pocket_reason": zone.get("daily_pocket_reason"),
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


def build_market_structure_diagnostic(
    *,
    candles: list[dict[str, Any]],
    tf: str,
    phase1_profile: str = PHASE1_STRUCTURE_PROFILE_CANONICAL,
) -> dict[str, Any]:
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

    bars, events, _swings = run_phase1_structure_contract_from_candles(candles, profile=phase1_profile)
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
        "phase1_profile": phase1_profile,
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
            "phase1_structure_contract": PHASE1_STRUCTURE_CONTRACT if phase1_profile == PHASE1_STRUCTURE_PROFILE_CANONICAL else PHASE1_STRUCTURE_CONTRACT_LEGACY,
            "bos_check": latest_bar.get("bos_check"),
            "choch_check": latest_bar.get("choch_check"),
            "cb_check": latest_bar.get("cb_check"),
        },
    }


def build_market_structure_comparison(*, candles: list[dict[str, Any]], tf: str) -> dict[str, Any]:
    legacy = build_market_structure_diagnostic(candles=candles, tf=tf, phase1_profile=PHASE1_STRUCTURE_PROFILE_LEGACY)
    canonical = build_market_structure_diagnostic(candles=candles, tf=tf, phase1_profile=PHASE1_STRUCTURE_PROFILE_CANONICAL)

    diffs: list[dict[str, Any]] = []
    for field in ["trend", "confidence", "last_transition_reason", "active_choch_level", "protected_high", "protected_low"]:
        legacy_value = legacy.get(field)
        canonical_value = canonical.get(field)
        if legacy_value != canonical_value:
            diffs.append({
                "field": field,
                "legacy": legacy_value,
                "canonical": canonical_value,
            })

    legacy_counts = legacy.get("event_counts") if isinstance(legacy.get("event_counts"), dict) else {}
    canonical_counts = canonical.get("event_counts") if isinstance(canonical.get("event_counts"), dict) else {}
    count_keys = sorted(set(legacy_counts.keys()) | set(canonical_counts.keys()))
    event_count_diffs = [
        {
            "event": key,
            "legacy": int(legacy_counts.get(key) or 0),
            "canonical": int(canonical_counts.get(key) or 0),
            "delta": int(canonical_counts.get(key) or 0) - int(legacy_counts.get(key) or 0),
        }
        for key in count_keys
        if int(legacy_counts.get(key) or 0) != int(canonical_counts.get(key) or 0)
    ]

    return {
        "contract": STRUCTURE_COMPARISON_CONTRACT,
        "timeframe": tf,
        "legacy": legacy,
        "canonical": canonical,
        "field_diffs": diffs,
        "event_count_diffs": event_count_diffs,
        "changed": bool(diffs or event_count_diffs),
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
    structure_comparison_by_tf: dict[str, Any] = {}
    availability = {str(tf).upper(): dict(payload) for tf, payload in (timeframe_availability or {}).items()}
    for tf, candles in (candles_by_tf or {}).items():
        tf_key = str(tf).upper()
        structure_by_tf[tf_key] = build_market_structure_diagnostic(candles=candles, tf=tf_key)
        structure_comparison_by_tf[tf_key] = build_market_structure_comparison(candles=candles, tf=tf_key)
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
                "nearest_support": summarize_zone_for_pair_analytics(_hydrate_nearest(nearest.get("nearest_support")), reference_price=entry),
                "next_support": summarize_zone_for_pair_analytics(_hydrate_nearest(nearest.get("next_support")), reference_price=entry),
                "nearest_resistance": summarize_zone_for_pair_analytics(_hydrate_nearest(nearest.get("nearest_resistance")), reference_price=entry),
                "next_resistance": summarize_zone_for_pair_analytics(_hydrate_nearest(nearest.get("next_resistance")), reference_price=entry),
            },
            "majors": [summarize_zone_for_pair_analytics(z, reference_price=entry) for z in majors[:8]],
            "operational": [summarize_zone_for_pair_analytics(z, reference_price=entry) for z in operational[:8]],
        },
        "market_structure": {
            "contract": STRUCTURE_DIAGNOSTIC_CONTRACT,
            "timeframes": structure_by_tf,
            "comparison_contract": STRUCTURE_COMPARISON_CONTRACT,
            "comparisons": structure_comparison_by_tf,
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
