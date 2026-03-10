from __future__ import annotations

from typing import Any


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


def side_aware_interaction(*, zone: dict[str, Any], price: float, side: str) -> dict[str, Any]:
    """Return reusable side-aware interaction diagnostics.

    For longs, support-style zones below/around price are the natural interaction.
    For shorts, resistance-style zones above/around price are the natural interaction.
    """
    normalized_side = (side or "").lower()
    relation = zone_interaction_side(zone=zone, price=price)
    kind = str(zone.get("zone_kind") or "mixed").lower()
    expected_relation = "above" if normalized_side == "buy" else "below" if normalized_side == "sell" else "inside"
    aligned_kind = (
        (normalized_side == "buy" and kind in {"support", "mixed"})
        or (normalized_side == "sell" and kind in {"resistance", "mixed"})
        or normalized_side not in {"buy", "sell"}
    )
    relation_ok = relation in {expected_relation, "inside"}
    return {
        "side": normalized_side,
        "zone_kind": kind,
        "price_relation": relation,
        "expected_relation": expected_relation,
        "interaction_bias": "aligned" if (aligned_kind and relation_ok) else "counter",
        "is_aligned": bool(aligned_kind and relation_ok),
    }
