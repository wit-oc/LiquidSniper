from __future__ import annotations

from typing import Any

from liquidsniper.core.sr_engine_v2 import build_zones_for_tf
from liquidsniper.core.zone_primitives import local_atr, side_aware_interaction
from liquidsniper.core.zone_selectors import nearest_four_levels, select_daily_majors, select_operational_zones


V3A_CONTRACT = "zone_engine_v3a"


def zone_candidates_from_structure(symbol: str, tf: str, candles: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    """V3-A structure candidate adapter.

    First pass keeps structure generation deliberately thin by adapting the existing
    reaction-family pipeline. Later passes can replace this with native structure-only
    candidate generation without disturbing selector/output contracts.
    """
    zones, _ = build_zones_for_tf(symbol, tf, candles, **kwargs)
    out: list[dict[str, Any]] = []
    for zone in zones:
        zz = dict(zone)
        zz["candidate_family"] = "structure"
        zz["source_family"] = "reaction_family"
        zz["engine_contract"] = V3A_CONTRACT
        out.append(zz)
    return out


def zone_candidates_from_base(symbol: str, tf: str, candles: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    """Stub for future base/shelf detection.

    TODO(v3-b): implement explicit base/shelf detection from compression/imbalance segments.
    V3-A intentionally returns no base candidates yet while freezing the contract.
    """
    _ = (symbol, tf, candles, kwargs)
    return []


def zone_candidates_from_reaction(symbol: str, tf: str, candles: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    """Expose sr_engine_v2 as the current reaction-family candidate generator."""
    zones, _ = build_zones_for_tf(symbol, tf, candles, **kwargs)
    out: list[dict[str, Any]] = []
    for zone in zones:
        zz = dict(zone)
        zz["candidate_family"] = "reaction"
        zz["source_family"] = "reaction_family"
        zz["source_version"] = zz.get("source_version") or "sr_engine_v2_reaction_family"
        zz["engine_contract"] = V3A_CONTRACT
        out.append(zz)
    return out


def merge_candidate_zones(*candidate_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for group in candidate_groups:
        for zone in group:
            zone_id = str(zone.get("zone_id") or zone.get("candidate_id") or "")
            if not zone_id:
                zone_id = f"{zone.get('symbol','?')}:{zone.get('tf','?')}:{zone.get('zone_mid','?')}:{zone.get('candidate_family','?')}"
            if zone_id not in merged:
                merged[zone_id] = dict(zone)
                merged[zone_id].setdefault("candidate_sources", [zone.get("candidate_family")])
            else:
                existing = merged[zone_id]
                existing["candidate_sources"] = sorted({*existing.get("candidate_sources", []), zone.get("candidate_family")})
                existing["strength_score"] = max(float(existing.get("strength_score") or 0.0), float(zone.get("strength_score") or 0.0))
    return list(merged.values())


def score_zone(zone: dict[str, Any], *, last_price: float | None = None) -> dict[str, Any]:
    scored = dict(zone)
    strength = float(scored.get("strength_score") or 0.0)
    reaction = float(scored.get("reaction_score") or 0.0)
    efficiency = float(scored.get("reaction_efficiency_score") or 0.0)
    carry = float(scored.get("carry_score") or 0.0)
    scored["selection_score"] = round((0.58 * strength) + (0.16 * reaction) + (0.16 * efficiency) + (0.10 * carry), 4)
    if last_price is not None:
        scored["interaction_buy"] = side_aware_interaction(zone=scored, price=float(last_price), side="buy")
        scored["interaction_sell"] = side_aware_interaction(zone=scored, price=float(last_price), side="sell")
    return scored


__all__ = [
    "V3A_CONTRACT",
    "local_atr",
    "side_aware_interaction",
    "zone_candidates_from_structure",
    "zone_candidates_from_base",
    "zone_candidates_from_reaction",
    "merge_candidate_zones",
    "score_zone",
    "select_daily_majors",
    "select_operational_zones",
    "nearest_four_levels",
]
