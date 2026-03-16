from __future__ import annotations

from typing import Any


ROLE_SEMANTICS_CONTRACT = "zone_role_semantics_v1"


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def true_range(current: dict[str, Any], previous_close: float) -> float:
    high = as_float(current.get("high"), previous_close)
    low = as_float(current.get("low"), previous_close)
    return max(high - low, abs(high - previous_close), abs(low - previous_close), 0.0)


def local_atr(candles: list[dict[str, Any]], period: int = 14) -> float:
    """Simple local ATR utility for zone engines.

    This intentionally stays dependency-free and local to the zone-engine stack so
    V3 candidate generators/selectors can share a stable volatility primitive.
    """
    if len(candles) < 3:
        return 0.0
    trs: list[float] = []
    prev_close = as_float(candles[0].get("close"), 0.0)
    for row in candles[1:]:
        trs.append(true_range(row, prev_close))
        prev_close = as_float(row.get("close"), prev_close)
    window = trs[-period:] if len(trs) >= period else trs
    return (sum(window) / len(window)) if window else 0.0


def zone_interaction_side(*, zone: dict[str, Any], price: float) -> str:
    low = as_float(zone.get("zone_low"), price)
    high = as_float(zone.get("zone_high"), price)
    if price < low:
        return "below"
    if price > high:
        return "above"
    return "inside"


def derive_role_semantics(*, zone: dict[str, Any], price: float | None = None) -> dict[str, Any]:
    """Derive execution-facing role semantics without mutating origin doctrine.

    `zone_kind` remains the canonical provenance/origin field. Current role is a
    derived interpretation at a specific price: below-price zones act as support,
    above-price zones act as resistance, and containing-price zones are active
    containing bands.
    """
    origin_kind = str(zone.get("origin_kind") or zone.get("zone_kind") or "mixed").lower()
    relative_position = "unknown" if price is None else zone_interaction_side(zone=zone, price=price)

    if relative_position == "below":
        current_role = "resistance"
    elif relative_position == "above":
        current_role = "support"
    elif relative_position == "inside":
        current_role = "containing"
    else:
        current_role = "neutral"

    return {
        "role_semantics_contract": ROLE_SEMANTICS_CONTRACT,
        "origin_kind": origin_kind,
        "relative_position": relative_position,
        "current_role": current_role,
    }


def side_aware_interaction(*, zone: dict[str, Any], price: float, side: str, atr: float | None = None) -> dict[str, Any]:
    """Return reusable side-aware interaction diagnostics.

    For longs, support-style zones below/around price are the natural interaction.
    For shorts, resistance-style zones above/around price are the natural interaction.

    V3-B extends this into a reusable lifecycle primitive so candidate generators,
    scorers, and selectors can reason about whether a zone is untouched, actively
    being defended, or likely spent/broken.
    """
    normalized_side = (side or "").lower()
    semantics = derive_role_semantics(zone=zone, price=price)
    relation = str(semantics.get("relative_position") or "unknown")
    origin_kind = str(semantics.get("origin_kind") or "mixed")
    current_role = str(semantics.get("current_role") or "neutral")
    expected_relation = "above" if normalized_side == "buy" else "below" if normalized_side == "sell" else "inside"
    aligned_role = (
        (normalized_side == "buy" and current_role in {"support", "containing"})
        or (normalized_side == "sell" and current_role in {"resistance", "containing"})
        or normalized_side not in {"buy", "sell"}
    )
    origin_aligned = (
        (normalized_side == "buy" and origin_kind in {"support", "mixed"})
        or (normalized_side == "sell" and origin_kind in {"resistance", "mixed"})
        or normalized_side not in {"buy", "sell"}
    )
    relation_ok = relation in {expected_relation, "inside"}

    low = as_float(zone.get("zone_low"), price)
    high = as_float(zone.get("zone_high"), price)
    mid = as_float(zone.get("zone_mid"), (low + high) / 2.0)
    width = max(high - low, 0.0)
    atr_ref = max(as_float(atr, as_float(zone.get("atr_local") or zone.get("atr_ref"), 0.0)), 1e-9)

    if price < low:
        distance = low - price
    elif price > high:
        distance = price - high
    else:
        distance = 0.0
    distance_atr = distance / atr_ref
    width_atr = width / atr_ref if atr_ref > 0 else 0.0
    if relation == "inside":
        if normalized_side == "buy":
            penetration_atr = (high - price) / atr_ref
        elif normalized_side == "sell":
            penetration_atr = (price - low) / atr_ref
        else:
            penetration_atr = min(price - low, high - price) / atr_ref
    else:
        penetration_atr = 0.0

    if not origin_aligned:
        lifecycle = "counter_side"
    elif relation == expected_relation and distance_atr > 0.35:
        lifecycle = "virgin"
    elif relation == "inside" and penetration_atr <= max(0.18, width_atr * 0.33):
        lifecycle = "first_touch"
    elif relation == "inside":
        lifecycle = "deep_test"
    elif relation == ("below" if expected_relation == "above" else "above"):
        lifecycle = "broken"
    else:
        lifecycle = "transition"

    return {
        "side": normalized_side,
        "zone_kind": origin_kind,
        "origin_kind": origin_kind,
        "current_role": current_role,
        "relative_position": relation,
        "role_semantics_contract": ROLE_SEMANTICS_CONTRACT,
        "price_relation": relation,
        "expected_relation": expected_relation,
        "interaction_bias": "aligned" if (aligned_role and relation_ok) else "counter",
        "is_aligned": bool(aligned_role and relation_ok),
        "distance_to_zone": round(distance, 8),
        "distance_to_zone_atr": round(distance_atr, 6),
        "zone_width_atr": round(width_atr, 6),
        "penetration_atr": round(max(0.0, penetration_atr), 6),
        "reference_price": round(mid, 8),
        "lifecycle_state": lifecycle,
    }
