from __future__ import annotations

from typing import Any

from liquidsniper.core.sr_engine_v2 import build_zones_for_tf
from liquidsniper.core.zone_primitives import local_atr, side_aware_interaction
from liquidsniper.core.zone_selectors import nearest_four_levels, select_daily_majors, select_operational_zones


V3A_CONTRACT = "zone_engine_v3a"
V3B_CONTRACT = "zone_engine_v3b"


def _zone_bounds(zone: dict[str, Any]) -> tuple[float, float, float]:
    low = float(zone.get("zone_low") or zone.get("zone_mid") or 0.0)
    high = float(zone.get("zone_high") or zone.get("zone_mid") or low)
    if high < low:
        low, high = high, low
    mid = float(zone.get("zone_mid") or ((low + high) / 2.0))
    return low, high, mid


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
        zz["engine_contract"] = V3B_CONTRACT
        out.append(zz)
    return out


def zone_candidates_from_base(symbol: str, tf: str, candles: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    """Narrow V3-B base/shelf generator.

    This intentionally starts simple: detect compressed shelves followed by directional
    breakout, then emit support/resistance candidates from the compressed band.
    """
    _ = kwargs
    if len(candles) < 12:
        return []

    atr_ref = local_atr(candles, period=14)
    if atr_ref <= 0.0:
        return []

    window = 4
    breakout_lookahead = 3
    compression_max_atr = 1.35
    breakout_min_atr = 0.85
    touch_tol = atr_ref * 0.12
    out: list[dict[str, Any]] = []

    for start in range(0, len(candles) - window - breakout_lookahead + 1):
        base = candles[start : start + window]
        post = candles[start + window : start + window + breakout_lookahead]
        base_high = max(float(r.get("high") or 0.0) for r in base)
        base_low = min(float(r.get("low") or 0.0) for r in base)
        base_span = max(base_high - base_low, 0.0)
        span_atr = base_span / atr_ref
        if span_atr <= 0.0 or span_atr > compression_max_atr:
            continue

        up_break = max(float(r.get("high") or 0.0) for r in post) - base_high
        down_break = base_low - min(float(r.get("low") or 0.0) for r in post)
        breakout_up_atr = max(0.0, up_break) / atr_ref
        breakout_down_atr = max(0.0, down_break) / atr_ref
        if max(breakout_up_atr, breakout_down_atr) < breakout_min_atr:
            continue

        kind = "support" if breakout_up_atr >= breakout_down_atr else "resistance"
        breakout_atr = max(breakout_up_atr, breakout_down_atr)
        body_closes = [float(r.get("close") or 0.0) for r in base]
        touches = sum(1 for close in body_closes if (base_low - touch_tol) <= close <= (base_high + touch_tol))
        score = min(100.0, 40.0 + (28.0 * breakout_atr) + (18.0 * (1.0 - min(span_atr / compression_max_atr, 1.0))) + (3.0 * touches))
        zone_id = f"{symbol}:{tf}:base:{start}:{kind}"
        out.append(
            {
                "zone_id": zone_id,
                "symbol": symbol,
                "tf": tf,
                "status": "confirmed",
                "zone_low": round(base_low, 8),
                "zone_high": round(base_high, 8),
                "zone_mid": round((base_low + base_high) / 2.0, 8),
                "zone_kind": kind,
                "strength_score": round(score, 4),
                "reaction_score": round(min(100.0, 52.0 + breakout_atr * 24.0), 4),
                "reaction_efficiency_score": round(min(100.0, 48.0 + breakout_atr * 20.0), 4),
                "carry_score": round(min(100.0, 40.0 + touches * 8.0), 4),
                "body_respect_score": round(min(100.0, 45.0 + (1.0 - min(span_atr / compression_max_atr, 1.0)) * 35.0), 4),
                "meaningful_touch_count": touches,
                "zone_width_bps": round((base_span / max(abs((base_low + base_high) / 2.0), 1e-9)) * 10000.0, 4),
                "candidate_family": "base",
                "source_family": "base_shelf_v3b",
                "source_version": "zone_engine_v3b_base_v1",
                "engine_contract": V3B_CONTRACT,
                "atr_local": round(atr_ref, 8),
                "compression_span_atr": round(span_atr, 6),
                "breakout_atr": round(breakout_atr, 6),
                "first_touch_state": "virgin",
            }
        )

    return out


def zone_candidates_from_reaction(symbol: str, tf: str, candles: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    """Expose sr_engine_v2 as the current reaction-family candidate generator."""
    zones, _ = build_zones_for_tf(symbol, tf, candles, **kwargs)
    atr_ref = local_atr(candles, period=14)
    out: list[dict[str, Any]] = []
    for zone in zones:
        zz = dict(zone)
        zz["candidate_family"] = "reaction"
        zz["source_family"] = "reaction_family"
        zz["source_version"] = zz.get("source_version") or "sr_engine_v2_reaction_family"
        zz["engine_contract"] = V3B_CONTRACT
        if atr_ref > 0.0:
            zz.setdefault("atr_local", round(atr_ref, 8))
        out.append(zz)
    return out


def merge_candidate_zones(*candidate_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge/arbitrate candidate families by actual zone proximity, not just identical ids."""
    flattened: list[dict[str, Any]] = []
    for group in candidate_groups:
        for zone in group:
            zz = dict(zone)
            family = str(zz.get("candidate_family") or zz.get("source_family") or "unknown")
            zz.setdefault("candidate_sources", [family])
            zz.setdefault("source_family", family)
            flattened.append(zz)
    if not flattened:
        return []

    ranked = sorted(
        flattened,
        key=lambda z: (
            float(z.get("selection_score") or z.get("strength_score") or 0.0),
            float(z.get("reaction_efficiency_score") or 0.0),
            float(z.get("carry_score") or 0.0),
        ),
        reverse=True,
    )

    clusters: list[list[dict[str, Any]]] = []
    for zone in ranked:
        low, high, mid = _zone_bounds(zone)
        atr_ref = max(float(zone.get("atr_local") or zone.get("atr_ref") or 0.0), 0.0)
        width = max(high - low, 0.0)
        attached = False
        for cluster in clusters:
            seed = cluster[0]
            s_low, s_high, s_mid = _zone_bounds(seed)
            if str(seed.get("symbol") or "") != str(zone.get("symbol") or ""):
                continue
            if str(seed.get("tf") or "") != str(zone.get("tf") or ""):
                continue
            if str(seed.get("zone_kind") or "") != str(zone.get("zone_kind") or ""):
                continue
            seed_atr = max(float(seed.get("atr_local") or seed.get("atr_ref") or 0.0), 0.0)
            merge_tol = max(width, s_high - s_low, atr_ref * 0.35, seed_atr * 0.35, abs(s_mid) * 0.0035)
            overlaps = max(low, s_low) <= min(high, s_high)
            nearby = abs(mid - s_mid) <= merge_tol
            if overlaps or nearby:
                cluster.append(zone)
                attached = True
                break
        if not attached:
            clusters.append([zone])

    merged: list[dict[str, Any]] = []
    for cluster in clusters:
        best = dict(cluster[0])
        families = sorted({str(z.get("candidate_family") or z.get("source_family") or "unknown") for z in cluster})
        lows, highs, mids = zip(*[_zone_bounds(z) for z in cluster])
        best["zone_low"] = round(min(lows), 8)
        best["zone_high"] = round(max(highs), 8)
        best["zone_mid"] = round(sum(mids) / len(mids), 8)
        best["candidate_sources"] = families
        best["merged_from_zone_ids"] = [str(z.get("zone_id") or z.get("candidate_id") or "") for z in cluster]
        best["merge_family_count"] = len(families)
        best["merge_candidate_count"] = len(cluster)
        best["source_family"] = best.get("source_family") or (families[0] if families else None)
        best["strength_score"] = round(max(float(z.get("strength_score") or 0.0) for z in cluster), 4)
        best["selection_score"] = round(
            max(float(z.get("selection_score") or z.get("strength_score") or 0.0) for z in cluster)
            + max(0, len(families) - 1) * 4.0,
            4,
        )
        best["family_confluence_bonus"] = round(max(0, len(families) - 1) * 4.0, 4)
        best["price_anchor"] = {
            "kind": "merged_zone_mid",
            "zone_mid": best["zone_mid"],
            "zone_low": best["zone_low"],
            "zone_high": best["zone_high"],
        }
        merged.append(best)
    return merged


def score_zone(zone: dict[str, Any], *, last_price: float | None = None, atr: float | None = None) -> dict[str, Any]:
    scored = dict(zone)
    strength = float(scored.get("strength_score") or 0.0)
    reaction = float(scored.get("reaction_score") or 0.0)
    efficiency = float(scored.get("reaction_efficiency_score") or 0.0)
    carry = float(scored.get("carry_score") or 0.0)
    low, high, _mid = _zone_bounds(scored)
    width = max(high - low, 0.0)
    atr_ref = max(float(atr or scored.get("atr_local") or scored.get("atr_ref") or 0.0), 0.0)
    width_atr = width / atr_ref if atr_ref > 0 else 0.0

    base_score = (0.54 * strength) + (0.16 * reaction) + (0.16 * efficiency) + (0.10 * carry)
    width_bonus = 0.0
    if atr_ref > 0.0:
        scored["atr_local"] = round(atr_ref, 8)
        scored["zone_width_atr"] = round(width_atr, 6)
        width_bonus = max(-10.0, min(8.0, (1.2 - width_atr) * 4.0))

    lifecycle_bonus = 0.0
    family_bonus = max(0, len(scored.get("candidate_sources") or []) - 1) * 3.0
    if last_price is not None:
        buy_view = side_aware_interaction(zone=scored, price=float(last_price), side="buy", atr=atr_ref or None)
        sell_view = side_aware_interaction(zone=scored, price=float(last_price), side="sell", atr=atr_ref or None)
        scored["interaction_buy"] = buy_view
        scored["interaction_sell"] = sell_view

        buy_state = buy_view["lifecycle_state"]
        sell_state = sell_view["lifecycle_state"]
        scored["first_touch_state"] = buy_state if buy_view["is_aligned"] else sell_state if sell_view["is_aligned"] else "counter_side"
        if "virgin" in {buy_state, sell_state}:
            lifecycle_bonus += 4.0
        if "first_touch" in {buy_state, sell_state}:
            lifecycle_bonus += 2.0
        if "deep_test" in {buy_state, sell_state}:
            lifecycle_bonus -= 4.0
        if "broken" in {buy_state, sell_state}:
            lifecycle_bonus -= 10.0

    scored["family_confluence_bonus"] = round(family_bonus, 4)
    scored["selection_score"] = round(base_score + width_bonus + lifecycle_bonus + family_bonus, 4)
    return scored


__all__ = [
    "V3A_CONTRACT",
    "V3B_CONTRACT",
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
