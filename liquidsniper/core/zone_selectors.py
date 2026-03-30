from __future__ import annotations

from typing import Any

from liquidsniper.core.zone_primitives import as_float, side_aware_interaction


def zone_rank_key(z: dict[str, Any]) -> tuple[float, float, float, float, float, float]:
    return (
        float(z.get("selection_score") or z.get("strength_score") or 0.0),
        float(z.get("reaction_efficiency_score") or 0.0),
        float(z.get("body_respect_score") or 0.0),
        float(z.get("carry_score") or 0.0),
        -float(z.get("meaningful_touch_count") or 0.0),
        -float(z.get("zone_width_bps") or 0.0),
    )


def _zone_interval(zone: dict[str, Any]) -> tuple[float, float, float] | None:
    low = as_float(zone.get("zone_low"))
    high = as_float(zone.get("zone_high"))
    mid = as_float(zone.get("zone_mid"))
    if low is None or high is None:
        bounds = zone.get("bounds") if isinstance(zone.get("bounds"), dict) else {}
        low = low if low is not None else as_float(bounds.get("low"))
        high = high if high is not None else as_float(bounds.get("high"))
        mid = mid if mid is not None else as_float(bounds.get("mid"))
    if low is None or high is None or high <= low:
        return None
    if mid is None:
        mid = (low + high) / 2.0
    return low, high, mid


def _mid_gap_bps(a: dict[str, Any], b: dict[str, Any]) -> float:
    ia = _zone_interval(a)
    ib = _zone_interval(b)
    if ia is None or ib is None:
        return float("inf")
    _, _, amid = ia
    _, _, bmid = ib
    anchor = max(abs(amid), abs(bmid), 1e-9)
    return abs(amid - bmid) / anchor * 10000.0


def _edge_gap_bps(a: dict[str, Any], b: dict[str, Any]) -> float:
    ia = _zone_interval(a)
    ib = _zone_interval(b)
    if ia is None or ib is None:
        return float("inf")
    alow, ahigh, amid = ia
    blow, bhigh, bmid = ib
    if ahigh < blow:
        gap = blow - ahigh
    elif bhigh < alow:
        gap = alow - bhigh
    else:
        gap = -min(ahigh, bhigh) + max(alow, blow)
    anchor = max(abs(amid), abs(bmid), 1e-9)
    return gap / anchor * 10000.0


def _interval_overlap_ratio(a: dict[str, Any], b: dict[str, Any]) -> float:
    ia = _zone_interval(a)
    ib = _zone_interval(b)
    if ia is None or ib is None:
        return 0.0
    alow, ahigh, _ = ia
    blow, bhigh, _ = ib
    overlap = min(ahigh, bhigh) - max(alow, blow)
    if overlap <= 0:
        return 0.0
    aw = max(ahigh - alow, 1e-9)
    bw = max(bhigh - blow, 1e-9)
    return overlap / max(min(aw, bw), 1e-9)


def _sources_for_zone(zone: dict[str, Any]) -> list[str]:
    sources = [str(src).strip().lower() for src in (zone.get("candidate_sources") or []) if str(src).strip()]
    families = [str(src).strip().lower() for src in (zone.get("candidate_families") or []) if str(src).strip()]
    source_family = str(zone.get("source_family") or "").strip().lower()
    candidate_family = str(zone.get("candidate_family") or "").strip().lower()
    merged = []
    for item in [*sources, *families, source_family, candidate_family]:
        if item and item not in merged:
            merged.append(item)
    return merged


def _operational_provenance_weight(zone: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    sources = set(_sources_for_zone(zone))
    merge_family_count = int(zone.get("merge_family_count") or len(sources) or 1)
    has_structure = "structure" in sources or bool(zone.get("structure_provenance"))
    has_reaction = "reaction" in sources
    has_base = "base" in sources
    pure_base_only = bool(sources) and sources == {"base"}

    weight = 1.0
    if has_structure:
        weight += 0.06
    if has_reaction:
        weight += 0.02
    if merge_family_count >= 2:
        weight += min(0.05, 0.02 * float(merge_family_count - 1))
    if pure_base_only:
        weight -= 0.05

    diagnostics = {
        "sources": sorted(sources),
        "merge_family_count": merge_family_count,
        "has_structure": has_structure,
        "has_reaction": has_reaction,
        "has_base": has_base,
        "pure_base_only": pure_base_only,
        "weight": round(max(0.88, min(1.15, weight)), 4),
    }
    return max(0.88, min(1.15, weight)), diagnostics


def _operational_representative_rank_key(zone: dict[str, Any]) -> tuple[float, float, float, float, float, float]:
    provenance_weight, _ = _operational_provenance_weight(zone)
    base_score = float(zone.get("selection_score") or zone.get("strength_score") or 0.0)
    weighted_score = base_score * provenance_weight
    reaction_efficiency = float(zone.get("reaction_efficiency_score") or 0.0)
    touch_count = float(zone.get("meaningful_touch_count") or 0.0)
    width_bps = float(zone.get("zone_width_bps") or 0.0)
    merge_family_count = float(zone.get("merge_family_count") or len(_sources_for_zone(zone)) or 1.0)
    return (
        weighted_score,
        merge_family_count,
        reaction_efficiency,
        touch_count,
        -width_bps,
        base_score,
    )


def _neighborhood_envelope(group: list[dict[str, Any]]) -> dict[str, Any] | None:
    intervals = [_zone_interval(zone) for zone in group]
    valid = [row for row in intervals if row is not None]
    if not valid:
        return None
    lows = [row[0] for row in valid]
    highs = [row[1] for row in valid]
    mids = [row[2] for row in valid]
    return {
        "zone_low": min(lows),
        "zone_high": max(highs),
        "zone_mid": sum(mids) / len(mids),
    }


def _belongs_to_same_side_neighborhood(
    group: list[dict[str, Any]],
    zone: dict[str, Any],
    *,
    min_zone_separation_bps: float,
) -> bool:
    envelope = _neighborhood_envelope(group)
    if envelope is None:
        return False
    overlap_ratio = _interval_overlap_ratio(envelope, zone)
    edge_gap_bps = _edge_gap_bps(envelope, zone)
    mid_gap_bps = _mid_gap_bps(envelope, zone)
    edge_threshold_bps = max(float(min_zone_separation_bps) * 1.35, 220.0)
    mid_threshold_bps = max(float(min_zone_separation_bps) * 2.0, 340.0)
    return (
        overlap_ratio >= 0.18
        or edge_gap_bps <= edge_threshold_bps
        or (mid_gap_bps <= mid_threshold_bps and edge_gap_bps <= (edge_threshold_bps * 2.2))
    )


def collapse_zones_by_distance(
    zones: list[dict[str, Any]],
    *,
    min_zone_separation_bps: float,
    max_zones_per_symbol: int,
) -> list[dict[str, Any]]:
    if not zones:
        return []

    ranked = sorted(zones, key=lambda z: zone_rank_key(z), reverse=True)
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


def select_spatially_diverse_zones(zones: list[dict[str, Any]], *, max_zones: int) -> list[dict[str, Any]]:
    if not zones or max_zones <= 0:
        return []
    if len(zones) <= max_zones:
        return sorted(zones, key=lambda z: float(z.get("zone_mid") or 0.0))

    mids = [float(z.get("zone_mid") or 0.0) for z in zones if float(z.get("zone_mid") or 0.0) > 0.0]
    if not mids:
        return []

    lo = min(mids)
    hi = max(mids)
    if hi <= lo:
        ranked = sorted(zones, key=lambda z: zone_rank_key(z), reverse=True)
        return sorted(ranked[:max_zones], key=lambda z: float(z.get("zone_mid") or 0.0))

    chosen: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    width = (hi - lo) / max(max_zones, 1)

    for bi in range(max_zones):
        b0 = lo + (bi * width)
        b1 = hi if bi == max_zones - 1 else lo + ((bi + 1) * width)
        cand = [
            z for z in zones
            if str(z.get("zone_id") or "") not in used_ids
            and (
                (float(z.get("zone_mid") or 0.0) >= b0 and float(z.get("zone_mid") or 0.0) < b1)
                if bi < max_zones - 1
                else (float(z.get("zone_mid") or 0.0) >= b0 and float(z.get("zone_mid") or 0.0) <= b1)
            )
        ]
        if not cand:
            continue
        best = sorted(cand, key=lambda z: zone_rank_key(z), reverse=True)[0]
        chosen.append(best)
        used_ids.add(str(best.get("zone_id") or ""))

    if len(chosen) < max_zones:
        rem = [z for z in zones if str(z.get("zone_id") or "") not in used_ids]
        rem = sorted(rem, key=lambda z: zone_rank_key(z), reverse=True)
        chosen.extend(rem[: max_zones - len(chosen)])

    return sorted(chosen[:max_zones], key=lambda z: float(z.get("zone_mid") or 0.0))


def daily_retest_weight(z: dict[str, Any], *, strict_mode: bool) -> float:
    result = str(z.get("first_retest_result") or "").lower()
    carry = float(z.get("carry_score") or 0.0) / 100.0
    body = float(z.get("body_respect_score") or 0.0) / 100.0
    close_through = float(z.get("counter_close_rate") or 0.0)
    close_inside = float(z.get("close_inside_rate") or 0.0)

    if result == "reject":
        base = 1.0
    elif result == "deviation":
        base = 0.92
    elif result == "accept":
        base = 0.80 if strict_mode else 0.86
    elif result in {"", "none"}:
        base = 0.82 if strict_mode else 0.88
    else:
        base = 0.84

    dynamic = (0.05 * carry) + (0.04 * body) - (0.06 * close_through) - (0.03 * close_inside)
    return max(0.6, min(1.0, base + dynamic))


def daily_major_provenance_weight(z: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Return a small generic Daily-major promotion bias from canonical provenance.

    The goal is not to re-tune selectors generically or encode symbol-specific
    exceptions. It is only to let Daily majors prefer corroborated structural
    truth over pure base-only shelves when the rest of the evidence is close.
    """
    candidate_sources = [str(src) for src in (z.get("candidate_sources") or ([] if z.get("source_family") is None else [z.get("source_family")]))]
    family_set = set(candidate_sources)
    merge_family_count = int(z.get("merge_family_count") or len(family_set))
    has_structure = "structure" in family_set or bool(z.get("structure_provenance"))
    pure_base_only = family_set == {"base"} or (
        str(z.get("source_family") or "") == "base" and merge_family_count <= 1 and not has_structure and not family_set.difference({"base"})
    )

    weight = 1.0
    if has_structure:
        weight += 0.06
    if merge_family_count >= 2:
        weight += min(0.04, 0.02 * float(merge_family_count - 1))
    if pure_base_only:
        weight -= 0.06

    diagnostics = {
        "candidate_sources": sorted(family_set),
        "merge_family_count": merge_family_count,
        "has_structure": has_structure,
        "pure_base_only": pure_base_only,
        "weight": round(max(0.88, min(1.12, weight)), 4),
    }
    return max(0.88, min(1.12, weight)), diagnostics


def apply_daily_soft_retest_weights(zones: list[dict[str, Any]], *, strict_mode: bool) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for z in zones:
        zz = dict(z)
        retest_weight = daily_retest_weight(zz, strict_mode=strict_mode)
        provenance_weight, provenance_diag = daily_major_provenance_weight(zz)
        strength = float(zz.get("strength_score") or 0.0)
        reaction = float(zz.get("reaction_score") or 0.0)
        efficiency = float(zz.get("reaction_efficiency_score") or 0.0)
        carry = float(zz.get("carry_score") or 0.0)
        body_respect = float(zz.get("body_respect_score") or 0.0)
        zz["retest_weight"] = round(retest_weight, 4)
        zz["daily_major_provenance_weight"] = round(provenance_weight, 4)
        zz["daily_major_diagnostics"] = provenance_diag
        zz["selection_score"] = round(
            (strength * retest_weight * provenance_weight)
            + (0.08 * reaction)
            + (0.16 * efficiency)
            + (0.06 * carry)
            + (0.10 * body_respect),
            4,
        )
        out.append(zz)
    return out


def select_daily_local_band_representatives(
    zones: list[dict[str, Any]],
    *,
    max_zones: int,
    min_zone_separation_bps: float,
) -> list[dict[str, Any]]:
    if not zones or max_zones <= 0:
        return []

    ordered = sorted([z for z in zones if float(z.get("zone_mid") or 0.0) > 0.0], key=lambda z: float(z.get("zone_mid") or 0.0))
    if not ordered:
        return []

    band_span_bps = max(float(min_zone_separation_bps) * 2.6, 1100.0)
    bands: list[list[dict[str, Any]]] = [[ordered[0]]]
    for z in ordered[1:]:
        cur_mid = float(z.get("zone_mid") or 0.0)
        last_band = bands[-1]
        center = sum(float(x.get("zone_mid") or 0.0) for x in last_band) / len(last_band)
        dist_bps = abs(cur_mid - center) / max(abs(center), 1e-9) * 10000.0
        if dist_bps <= band_span_bps:
            last_band.append(z)
        else:
            bands.append([z])

    selected: list[dict[str, Any]] = []
    for band in bands:
        ranked = sorted(band, key=lambda z: zone_rank_key(z), reverse=True)
        top = ranked[0]
        selected.append(top)
        if len(ranked) < 2:
            continue
        top_mid = float(top.get("zone_mid") or 0.0)
        top_score = float(top.get("selection_score") or top.get("strength_score") or 0.0)

        def second_candidate_value(z: dict[str, Any]) -> float:
            mid = float(z.get("zone_mid") or 0.0)
            dist_bps = abs(mid - top_mid) / max(abs(top_mid), 1e-9) * 10000.0
            score = float(z.get("selection_score") or z.get("strength_score") or 0.0)
            return (0.75 * score) + (0.25 * dist_bps)

        second = sorted(ranked[1:], key=second_candidate_value, reverse=True)[0]
        second_mid = float(second.get("zone_mid") or 0.0)
        second_score = float(second.get("selection_score") or second.get("strength_score") or 0.0)
        second_dist_bps = abs(second_mid - top_mid) / max(abs(top_mid), 1e-9) * 10000.0
        if second_score >= (top_score * 0.87) and second_dist_bps >= max(float(min_zone_separation_bps) * 1.9, 700.0):
            selected.append(second)

    selected = sorted(selected, key=lambda z: zone_rank_key(z), reverse=True)[:max_zones]
    return sorted(selected, key=lambda z: float(z.get("zone_mid") or 0.0))


def _daily_core_from_arbitration(zone: dict[str, Any]) -> tuple[tuple[float, float] | None, str | None]:
    diagnostics = zone.get("arbitration_diagnostics") if isinstance(zone.get("arbitration_diagnostics"), dict) else {}
    candidates = diagnostics.get("candidates") if isinstance(diagnostics.get("candidates"), list) else []
    intervals: list[tuple[float, float, float]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        try:
            low = float(candidate.get("low"))
            high = float(candidate.get("high"))
            score = float(candidate.get("base_score") or 0.0)
        except (TypeError, ValueError):
            continue
        if high <= low:
            continue
        intervals.append((low, high, score))
    if len(intervals) < 2:
        return None, None

    intervals.sort(key=lambda row: row[2], reverse=True)
    top_score = max(intervals[0][2], 1e-9)
    strong = [row for row in intervals if row[2] >= (top_score * 0.82)]
    if len(strong) < 2:
        strong = intervals[:2]
    overlap_low = max(row[0] for row in strong)
    overlap_high = min(row[1] for row in strong)
    if overlap_high > overlap_low:
        return (overlap_low, overlap_high), "overlap_density_core"

    representative_low, representative_high, _ = intervals[0]
    return (representative_low, representative_high), "representative_family_core"


def _apply_daily_operator_core(zone: dict[str, Any]) -> dict[str, Any]:
    refined = dict(zone)
    try:
        zone_low = float(refined.get("zone_low"))
        zone_high = float(refined.get("zone_high"))
    except (TypeError, ValueError):
        return refined
    if zone_high <= zone_low:
        return refined

    macro_width = zone_high - zone_low
    core_bounds, core_definition = _daily_core_from_arbitration(refined)
    if core_bounds is None:
        midpoint = float(refined.get("zone_mid") or ((zone_low + zone_high) / 2.0))
        half_width = macro_width * 0.275
        core_low = max(zone_low, midpoint - half_width)
        core_high = min(zone_high, midpoint + half_width)
        core_definition = "midpoint_narrowed_core"
    else:
        core_low, core_high = core_bounds
        core_low = max(zone_low, min(core_low, zone_high))
        core_high = max(core_low, min(core_high, zone_high))
        core_width = core_high - core_low
        if core_width >= (macro_width * 0.9):
            midpoint = float(refined.get("zone_mid") or ((zone_low + zone_high) / 2.0))
            half_width = macro_width * 0.275
            core_low = max(zone_low, midpoint - half_width)
            core_high = min(zone_high, midpoint + half_width)
            core_definition = "midpoint_narrowed_core"

    refined["core_low"] = round(core_low, 8)
    refined["core_high"] = round(core_high, 8)
    refined["core_mid"] = round((core_low + core_high) / 2.0, 8)
    refined["core_definition"] = core_definition
    return refined


def select_daily_majors(
    zones: list[dict[str, Any]],
    *,
    min_strength: float,
    min_zone_separation_bps: float,
    max_zones: int,
    strict_retest_quality: bool,
) -> list[dict[str, Any]]:
    confirmed = [z for z in zones if z.get("status") == "confirmed"]
    scored = apply_daily_soft_retest_weights(confirmed, strict_mode=strict_retest_quality)
    prefilter = [z for z in scored if float(z.get("strength_score") or 0.0) >= min_strength]
    band = select_daily_local_band_representatives(
        prefilter,
        max_zones=max(max_zones * 2, max_zones),
        min_zone_separation_bps=min_zone_separation_bps,
    )
    collapsed = collapse_zones_by_distance(
        band,
        min_zone_separation_bps=min_zone_separation_bps,
        max_zones_per_symbol=max_zones,
    )
    selected = select_spatially_diverse_zones(collapsed, max_zones=max_zones)
    surfaced = [_apply_daily_operator_core(zone) for zone in selected]
    ranked = sorted(surfaced, key=lambda z: zone_rank_key(z), reverse=True)
    rank_map = {str(zone.get("zone_id") or ""): idx for idx, zone in enumerate(ranked, start=1)}
    out: list[dict[str, Any]] = []
    for zone in surfaced:
        zz = dict(zone)
        zz["selector_surface"] = "daily_major"
        zz["selector_status"] = "kept"
        zz["selector_reason"] = "kept: daily major anchor after local-band selection"
        zz["selector_rank"] = rank_map.get(str(zone.get("zone_id") or ""))
        out.append(zz)
    return out


def _operational_role_key(zone: dict[str, Any]) -> str:
    role = str(zone.get("current_role") or zone.get("kind") or zone.get("zone_kind") or "unknown").strip().lower()
    if role in {"support", "resistance", "containing"}:
        return role
    origin = str(zone.get("origin_kind") or zone.get("zone_kind") or role).strip().lower()
    if origin in {"support", "resistance"}:
        return origin
    return role or "unknown"



def _select_operational_local_representatives(
    zones: list[dict[str, Any]],
    *,
    min_zone_separation_bps: float,
) -> list[dict[str, Any]]:
    ordered = sorted(
        [z for z in zones if _zone_interval(z) is not None],
        key=lambda z: float((_zone_interval(z) or (0.0, 0.0, 0.0))[0]),
    )
    if not ordered:
        return []

    by_role: dict[str, list[dict[str, Any]]] = {}
    for zone in ordered:
        by_role.setdefault(_operational_role_key(zone), []).append(zone)

    selected: list[dict[str, Any]] = []
    for role_zones in by_role.values():
        neighborhoods: list[list[dict[str, Any]]] = [[role_zones[0]]]
        for zone in role_zones[1:]:
            last_group = neighborhoods[-1]
            if _belongs_to_same_side_neighborhood(
                last_group,
                zone,
                min_zone_separation_bps=min_zone_separation_bps,
            ):
                last_group.append(zone)
            else:
                neighborhoods.append([zone])

        for idx, group in enumerate(neighborhoods, start=1):
            ranked = sorted(group, key=lambda z: _operational_representative_rank_key(z), reverse=True)
            representative = dict(ranked[0])
            provenance_weight, provenance_diag = _operational_provenance_weight(representative)
            representative["local_cluster_contract"] = "operational_local_representative_v1"
            representative["local_cluster_role"] = _operational_role_key(representative)
            representative["local_cluster_id"] = f"{representative.get('tf') or 'tf'}:{representative['local_cluster_role']}:{idx}"
            representative["local_cluster_member_count"] = len(group)
            representative["local_cluster_member_ids"] = [str(z.get("zone_id") or "") for z in sorted(group, key=lambda z: float(z.get("zone_mid") or 0.0))]
            representative["local_cluster_demoted_ids"] = [
                str(z.get("zone_id") or "") for z in sorted(group, key=lambda z: float(z.get("zone_mid") or 0.0)) if str(z.get("zone_id") or "") != str(representative.get("zone_id") or "")
            ]
            representative["local_cluster_bounds"] = {
                "low": round(min(float(z.get("zone_low") or z.get("zone_mid") or 0.0) for z in group), 8),
                "high": round(max(float(z.get("zone_high") or z.get("zone_mid") or 0.0) for z in group), 8),
            }
            representative["local_cluster_demotions"] = [
                {
                    "zone_id": str(z.get("zone_id") or ""),
                    "reason": "too close to stronger same-side representative",
                    "competition_basis": "interval_overlap_or_edge_gap_with_provenance_bias",
                }
                for z in sorted(group, key=lambda z: float(z.get("zone_mid") or 0.0))
                if str(z.get("zone_id") or "") != str(representative.get("zone_id") or "")
            ]
            representative["local_cluster_competition_basis"] = "interval_overlap_or_edge_gap_with_provenance_bias"
            representative["local_cluster_representative_weight"] = round(provenance_weight, 4)
            representative["local_cluster_representative_diagnostics"] = provenance_diag
            representative["selector_surface"] = "operational_4h"
            representative["selector_status"] = "kept"
            representative["selector_reason"] = "kept: representative of same-side local neighborhood"
            selected.append(representative)
    return selected



def select_operational_zones(
    zones: list[dict[str, Any]],
    *,
    min_strength: float,
    min_zone_separation_bps: float,
    max_zones: int,
) -> list[dict[str, Any]]:
    confirmed = [z for z in zones if z.get("status") == "confirmed"]
    prefilter = [z for z in confirmed if float(z.get("strength_score") or 0.0) >= min_strength]
    representatives = _select_operational_local_representatives(
        prefilter,
        min_zone_separation_bps=min_zone_separation_bps,
    )
    ranked = sorted(representatives, key=lambda z: _operational_representative_rank_key(z), reverse=True)[:max_zones]
    out: list[dict[str, Any]] = []
    for idx, zone in enumerate(ranked, start=1):
        zz = dict(zone)
        zz["selector_surface"] = "operational_4h"
        zz["selector_status"] = "kept"
        zz["selector_reason"] = zz.get("selector_reason") or "kept: representative of same-side local neighborhood"
        zz["selector_rank"] = idx
        out.append(zz)
    return sorted(out, key=lambda z: float(z.get("zone_mid") or 0.0))


def nearest_four_levels(*, profile_id: str, entry: float, zones: list[dict[str, Any]]) -> dict[str, Any]:
    from liquidsniper.core.sr_engine_v2 import nearest_sr_levels_v1

    payload = nearest_sr_levels_v1(profile_id=profile_id, entry=entry, zones=zones)
    primary_support = payload.get("nearest_support")
    primary_resistance = payload.get("nearest_resistance")
    return {
        **payload,
        "contract": "nearest_four_levels_v3a",
        "buy_interaction": side_aware_interaction(zone=primary_support or {}, price=entry, side="buy") if primary_support else None,
        "sell_interaction": side_aware_interaction(zone=primary_resistance or {}, price=entry, side="sell") if primary_resistance else None,
    }
