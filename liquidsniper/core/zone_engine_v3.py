"""Zone Engine V3 scaffold / bridge module.

This module is intentionally the thin architectural seam for the Phase 2 V3
shadow-mode migration. The doctrinal target is a family-fusion engine with
separate generation, arbitration, scoring, and selector layers, but the current
branch must preserve the existing nearest-four execution payload concept while
that migration happens.

Why this file exists in its current form:
- keep the seam names and contracts stable for bootstrap/tests
- allow structure/base/reaction families to converge behind one engine surface
- preserve selector separation instead of burying policy in bootstrap logic
- stay reversible while V3 remains shadow-first and non-default

Implementation note:
The functions below are bridge implementations, not the final doctrinal endpoint.
They should be treated as scaffold seams that future work can replace family by
family without breaking downstream callers.
"""

from __future__ import annotations

from typing import Any

from liquidsniper.core.sr_engine_v2 import _zone_fmt_with_distance, build_zones_for_tf, profile_anchor_and_eligible
from liquidsniper.core.zone_primitives import local_atr, side_aware_interaction
from liquidsniper.core.zone_selectors import select_daily_majors, select_operational_zones


V3A_CONTRACT = "zone_engine_v3a"
V3B_CONTRACT = "zone_engine_v3b"
V3D_CONTRACT = "zone_engine_v3d"


def _zone_bounds(zone: dict[str, Any]) -> tuple[float, float, float]:
    """Normalize a candidate/merged zone into low/high/mid bounds.

    This helper keeps downstream seam functions agnostic to whether an upstream
    family emitted explicit low/high bounds or only a midpoint.
    """
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

    The first bridge version overfit any narrow window with a breakout. This pass
    raises the doctrinal bar: a base needs compression plus repeated overlap,
    visible edge participation, and a close-based breakout beyond the shelf.
    """
    _ = kwargs
    if len(candles) < 14:
        return []

    atr_ref = local_atr(candles, period=14)
    if atr_ref <= 0.0:
        return []

    window = 5
    breakout_lookahead = 3
    compression_max_atr = 1.10
    breakout_min_atr = 0.80
    breakout_close_min_atr = 0.35
    overlap_min_ratio = 0.45
    min_overlap_links = 2
    touch_tol = atr_ref * 0.10
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

        overlap_links = 0
        for prev, cur in zip(base, base[1:]):
            prev_high = float(prev.get("high") or 0.0)
            prev_low = float(prev.get("low") or 0.0)
            cur_high = float(cur.get("high") or 0.0)
            cur_low = float(cur.get("low") or 0.0)
            overlap = max(0.0, min(prev_high, cur_high) - max(prev_low, cur_low))
            smaller_range = max(min(prev_high - prev_low, cur_high - cur_low), 1e-9)
            if (overlap / smaller_range) >= overlap_min_ratio:
                overlap_links += 1
        if overlap_links < min_overlap_links:
            continue

        upper_touches = 0
        lower_touches = 0
        for row in base:
            high = float(row.get("high") or 0.0)
            low = float(row.get("low") or 0.0)
            close = float(row.get("close") or 0.0)
            if abs(high - base_high) <= touch_tol or abs(close - base_high) <= touch_tol:
                upper_touches += 1
            if abs(low - base_low) <= touch_tol or abs(close - base_low) <= touch_tol:
                lower_touches += 1
        edge_touch_total = upper_touches + lower_touches
        if edge_touch_total < 4:
            continue
        if upper_touches < 1 or lower_touches < 1:
            continue

        post_high = max(float(r.get("high") or 0.0) for r in post)
        post_low = min(float(r.get("low") or 0.0) for r in post)
        post_close_high = max(float(r.get("close") or 0.0) for r in post)
        post_close_low = min(float(r.get("close") or 0.0) for r in post)
        up_break = post_high - base_high
        down_break = base_low - post_low
        close_up_break = post_close_high - base_high
        close_down_break = base_low - post_close_low
        breakout_up_atr = max(0.0, up_break) / atr_ref
        breakout_down_atr = max(0.0, down_break) / atr_ref
        close_breakout_up_atr = max(0.0, close_up_break) / atr_ref
        close_breakout_down_atr = max(0.0, close_down_break) / atr_ref
        breakout_atr = max(breakout_up_atr, breakout_down_atr)
        close_breakout_atr = max(close_breakout_up_atr, close_breakout_down_atr)
        if breakout_atr < breakout_min_atr or close_breakout_atr < breakout_close_min_atr:
            continue

        kind = "support" if close_breakout_up_atr >= close_breakout_down_atr else "resistance"
        compression_bonus = max(0.0, 1.0 - min(span_atr / compression_max_atr, 1.0))
        overlap_score = min(1.0, overlap_links / max(window - 1, 1))
        edge_balance = min(upper_touches, lower_touches)
        edge_score = min(1.0, edge_touch_total / float(window + 1))
        battle_score = min(1.0, (edge_balance + overlap_links) / float(window + 1))
        score = min(
            100.0,
            28.0
            + (24.0 * breakout_atr)
            + (18.0 * close_breakout_atr)
            + (14.0 * overlap_score)
            + (12.0 * edge_score)
            + (10.0 * compression_bonus)
            + (8.0 * battle_score),
        )
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
                "reaction_score": round(min(100.0, 44.0 + breakout_atr * 22.0 + close_breakout_atr * 10.0), 4),
                "reaction_efficiency_score": round(min(100.0, 42.0 + close_breakout_atr * 24.0 + overlap_score * 12.0), 4),
                "carry_score": round(min(100.0, 34.0 + edge_touch_total * 7.0 + overlap_links * 6.0), 4),
                "body_respect_score": round(min(100.0, 40.0 + compression_bonus * 20.0 + battle_score * 18.0), 4),
                "meaningful_touch_count": edge_touch_total,
                "zone_width_bps": round((base_span / max(abs((base_low + base_high) / 2.0), 1e-9)) * 10000.0, 4),
                "candidate_family": "base",
                "source_family": "base_shelf_v3b",
                "source_version": "zone_engine_v3b_base_v2",
                "engine_contract": V3B_CONTRACT,
                "atr_local": round(atr_ref, 8),
                "compression_span_atr": round(span_atr, 6),
                "breakout_atr": round(breakout_atr, 6),
                "close_breakout_atr": round(close_breakout_atr, 6),
                "overlap_links": overlap_links,
                "upper_edge_touches": upper_touches,
                "lower_edge_touches": lower_touches,
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


def _normalized_zone_kind(zone: dict[str, Any]) -> str:
    return str(zone.get("zone_kind") or zone.get("kind") or "mixed").strip().lower() or "mixed"


def _zone_kinds_compatible(a: dict[str, Any], b: dict[str, Any]) -> bool:
    kind_a = _normalized_zone_kind(a)
    kind_b = _normalized_zone_kind(b)
    if kind_a == kind_b:
        return True
    if "mixed" in {kind_a, kind_b}:
        explicit = {kind for kind in {kind_a, kind_b} if kind != "mixed"}
        return len(explicit) <= 1
    return False


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
            if not _zone_kinds_compatible(seed, zone):
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
        ranked_cluster = sorted(
            cluster,
            key=lambda z: (
                float(z.get("selection_score") or z.get("strength_score") or 0.0),
                float(z.get("reaction_efficiency_score") or 0.0),
                float(z.get("carry_score") or 0.0),
            ),
            reverse=True,
        )
        best = dict(ranked_cluster[0])
        families = sorted({str(z.get("candidate_family") or z.get("source_family") or "unknown") for z in cluster})
        lows, highs, mids = zip(*[_zone_bounds(z) for z in cluster])
        arbitration_rows: list[dict[str, Any]] = []
        for idx, candidate in enumerate(ranked_cluster):
            candidate_low, candidate_high, candidate_mid = _zone_bounds(candidate)
            family = str(candidate.get("candidate_family") or candidate.get("source_family") or "unknown")
            base_score = float(candidate.get("selection_score") or candidate.get("strength_score") or 0.0)
            arbitration_rows.append(
                {
                    "zone_id": str(candidate.get("zone_id") or candidate.get("candidate_id") or ""),
                    "family": family,
                    "source_family": candidate.get("source_family"),
                    "tf": candidate.get("tf"),
                    "status": candidate.get("status"),
                    "mid": round(candidate_mid, 8),
                    "low": round(candidate_low, 8),
                    "high": round(candidate_high, 8),
                    "base_score": round(base_score, 4),
                    "strength_score": round(float(candidate.get("strength_score") or 0.0), 4),
                    "reaction_efficiency_score": round(float(candidate.get("reaction_efficiency_score") or 0.0), 4),
                    "carry_score": round(float(candidate.get("carry_score") or 0.0), 4),
                    "kept": idx == 0,
                    "kept_reason": "top_ranked_in_cluster" if idx == 0 else "clustered_under_stronger_candidate",
                }
            )
        family_bonus = max(0, len(families) - 1) * 4.0
        explicit_kinds = sorted({_normalized_zone_kind(z) for z in cluster if _normalized_zone_kind(z) != "mixed"})
        merged_kind = explicit_kinds[0] if len(explicit_kinds) == 1 else _normalized_zone_kind(best)
        best["zone_low"] = round(min(lows), 8)
        best["zone_high"] = round(max(highs), 8)
        best["zone_mid"] = round(sum(mids) / len(mids), 8)
        best["zone_kind"] = merged_kind
        best["candidate_sources"] = families
        best["merged_from_zone_ids"] = [row["zone_id"] for row in arbitration_rows]
        best["merge_family_count"] = len(families)
        best["merge_candidate_count"] = len(cluster)
        best["source_family"] = best.get("source_family") or (families[0] if families else None)
        best["strength_score"] = round(max(float(z.get("strength_score") or 0.0) for z in cluster), 4)
        best["selection_score"] = round(
            max(float(z.get("selection_score") or z.get("strength_score") or 0.0) for z in cluster)
            + family_bonus,
            4,
        )
        best["family_confluence_bonus"] = round(family_bonus, 4)
        best["price_anchor"] = {
            "kind": "merged_zone_mid",
            "zone_mid": best["zone_mid"],
            "zone_low": best["zone_low"],
            "zone_high": best["zone_high"],
        }
        best["arbitration_diagnostics"] = {
            "engine_contract": V3D_CONTRACT,
            "cluster_size": len(cluster),
            "families": families,
            "kept_zone_id": arbitration_rows[0]["zone_id"] if arbitration_rows else None,
            "kept_source_family": best.get("source_family"),
            "family_confluence_bonus": round(family_bonus, 4),
            "score_components": {
                "winner_base_score": arbitration_rows[0]["base_score"] if arbitration_rows else 0.0,
                "family_confluence_bonus": round(family_bonus, 4),
                "final_selection_score": best["selection_score"],
            },
            "candidates": arbitration_rows,
        }
        merged.append(best)
    return merged


def classify_zone_state(zone: dict[str, Any], *, last_price: float | None = None, atr: float | None = None) -> dict[str, Any]:
    """Return role-aware lifecycle semantics without mutating doctrinal storage.

    Zones remain neutral in storage. Lifecycle is derived from approach-side
    interaction so MAP/LIVE consumers can reason about support, resistance, and
    flip behavior without forcing a permanent zone polarity.
    """
    state = dict(zone)
    atr_ref = max(float(atr or state.get("atr_local") or state.get("atr_ref") or 0.0), 0.0)
    if last_price is None:
        state.setdefault("lifecycle_state", str(state.get("first_touch_state") or "unknown"))
        return state

    buy_view = side_aware_interaction(zone=state, price=float(last_price), side="buy", atr=atr_ref or None)
    sell_view = side_aware_interaction(zone=state, price=float(last_price), side="sell", atr=atr_ref or None)
    state["interaction_buy"] = buy_view
    state["interaction_sell"] = sell_view

    preferred = buy_view if buy_view.get("is_aligned") else sell_view if sell_view.get("is_aligned") else buy_view
    state["lifecycle_state"] = str(preferred.get("lifecycle_state") or "unknown")
    state["first_touch_state"] = state["lifecycle_state"]
    state["interaction_role"] = str(preferred.get("role") or "neutral")
    return state


def score_zone(zone: dict[str, Any], *, last_price: float | None = None, atr: float | None = None) -> dict[str, Any]:
    """Apply bridge-era scoring without changing the selector/output seam.

    The score is intentionally a reversible composition of current bridge
    signals: strength/reaction/carry, width sanity, lifecycle state, and family
    confluence. Future doctrinal revisions can replace the scoring internals
    while keeping the surrounding V3 contract stable for shadow comparisons.
    """
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
        scored = classify_zone_state(scored, last_price=float(last_price), atr=atr_ref or None)
        buy_view = scored.get("interaction_buy") or {}
        sell_view = scored.get("interaction_sell") or {}
        buy_state = str(buy_view.get("lifecycle_state") or "")
        sell_state = str(sell_view.get("lifecycle_state") or "")
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


def build_structure_candidates(symbol: str, tf: str, candles: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    """Required V3 seam alias for structure-family candidate generation."""
    return zone_candidates_from_structure(symbol, tf, candles, **kwargs)


def build_base_candidates(symbol: str, tf: str, candles: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    """Required V3 seam alias for base/shelf candidate generation."""
    return zone_candidates_from_base(symbol, tf, candles, **kwargs)


def build_reaction_candidates(symbol: str, tf: str, candles: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    """Required V3 seam alias for reaction-family candidate generation."""
    return zone_candidates_from_reaction(symbol, tf, candles, **kwargs)


def nearest_four_levels(*, profile_id: str, entry: float, zones: list[dict[str, Any]]) -> dict[str, Any]:
    """Role-aware nearest-four wrapper for V3 shadow paths.

    Baseline `nearest_sr_levels_v1` allows overlapping zones to appear on both
    sides. That is acceptable for older mixed zones, but shadow V3 candidates
    carry explicit `zone_kind` more often, so we filter support/resistance slots
    through side-aware interaction before ranking.
    """
    anchor_tf, eligible_tfs = profile_anchor_and_eligible(profile_id)
    allowed = [z for z in zones if z.get("status") == "confirmed" and str(z.get("tf")) in eligible_tfs]

    def _distance_bps(distance: float) -> float:
        return (max(distance, 0.0) / max(abs(float(entry)), 1e-9)) * 10000.0

    support_rows: list[tuple[float, float, dict[str, Any], dict[str, Any]]] = []
    resistance_rows: list[tuple[float, float, dict[str, Any], dict[str, Any]]] = []
    for zone in allowed:
        buy_view = side_aware_interaction(zone=zone, price=float(entry), side="buy")
        sell_view = side_aware_interaction(zone=zone, price=float(entry), side="sell")
        strength = float(zone.get("selection_score") or zone.get("strength_score") or 0.0)
        if buy_view.get("is_aligned"):
            support_rows.append((_distance_bps(float(buy_view.get("distance_to_zone") or 0.0)), -strength, dict(zone), buy_view))
        if sell_view.get("is_aligned"):
            resistance_rows.append((_distance_bps(float(sell_view.get("distance_to_zone") or 0.0)), -strength, dict(zone), sell_view))

    support_rows.sort(key=lambda row: (row[0], row[1]))
    resistance_rows.sort(key=lambda row: (row[0], row[1]))

    def _pick_unique(candidates: list[tuple[float, float, dict[str, Any], dict[str, Any]]], used_ids: set[str]) -> tuple[float, float, dict[str, Any], dict[str, Any]] | None:
        for row in candidates:
            zid = str(row[2].get("zone_id") or "")
            if zid and zid not in used_ids:
                used_ids.add(zid)
                return row
        return None

    def _fmt(row: tuple[float, float, dict[str, Any], dict[str, Any]] | None) -> dict[str, Any] | None:
        if not row:
            return None
        zone = dict(row[2])
        payload = _zone_fmt_with_distance(zone, distance_bps=row[0], entry=float(entry)) or {}
        payload["kind"] = zone.get("zone_kind")
        payload["source_family"] = zone.get("source_family")
        payload["candidate_families"] = zone.get("candidate_sources")
        payload["selection_score"] = zone.get("selection_score")
        payload["interaction"] = row[3]
        return payload

    used_ids: set[str] = set()
    nearest_support = _pick_unique(support_rows, used_ids)
    next_support = _pick_unique(support_rows, used_ids)
    nearest_resistance = _pick_unique(resistance_rows, used_ids)
    next_resistance = _pick_unique(resistance_rows, used_ids)

    return {
        "contract": "nearest_four_levels_v3a",
        "sr_anchor_tf": anchor_tf,
        "sr_eligible_tfs": list(eligible_tfs),
        "entry": float(entry),
        "nearest_support": _fmt(nearest_support),
        "next_support": _fmt(next_support),
        "nearest_resistance": _fmt(nearest_resistance),
        "next_resistance": _fmt(next_resistance),
        "available_confirmed_zones": len(allowed),
        "buy_interaction": nearest_support[3] if nearest_support else None,
        "sell_interaction": nearest_resistance[3] if nearest_resistance else None,
    }


__all__ = [
    "V3A_CONTRACT",
    "V3B_CONTRACT",
    "V3D_CONTRACT",
    "local_atr",
    "side_aware_interaction",
    "zone_candidates_from_structure",
    "zone_candidates_from_base",
    "zone_candidates_from_reaction",
    "build_structure_candidates",
    "build_base_candidates",
    "build_reaction_candidates",
    "merge_candidate_zones",
    "classify_zone_state",
    "score_zone",
    "select_daily_majors",
    "select_operational_zones",
    "nearest_four_levels",
]
