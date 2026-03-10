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


def apply_daily_soft_retest_weights(zones: list[dict[str, Any]], *, strict_mode: bool) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for z in zones:
        zz = dict(z)
        weight = daily_retest_weight(zz, strict_mode=strict_mode)
        strength = float(zz.get("strength_score") or 0.0)
        reaction = float(zz.get("reaction_score") or 0.0)
        efficiency = float(zz.get("reaction_efficiency_score") or 0.0)
        carry = float(zz.get("carry_score") or 0.0)
        body_respect = float(zz.get("body_respect_score") or 0.0)
        zz["retest_weight"] = round(weight, 4)
        zz["selection_score"] = round((strength * weight) + (0.08 * reaction) + (0.16 * efficiency) + (0.06 * carry) + (0.10 * body_respect), 4)
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
    return select_spatially_diverse_zones(collapsed, max_zones=max_zones)


def select_operational_zones(
    zones: list[dict[str, Any]],
    *,
    min_strength: float,
    min_zone_separation_bps: float,
    max_zones: int,
) -> list[dict[str, Any]]:
    confirmed = [z for z in zones if z.get("status") == "confirmed"]
    prefilter = [z for z in confirmed if float(z.get("strength_score") or 0.0) >= min_strength]
    return collapse_zones_by_distance(
        prefilter,
        min_zone_separation_bps=min_zone_separation_bps,
        max_zones_per_symbol=max_zones,
    )


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
