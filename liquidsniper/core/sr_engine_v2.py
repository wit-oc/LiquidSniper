from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


TF_PRIORITY = {"1H": 1, "4H": 2, "1D": 3, "1W": 4}
PROFILE_ELIGIBILITY = {
    "S": ("1D", "1W"),
    "I": ("4H", "1D", "1W"),
    "C": ("1H", "4H", "1D", "1W"),
}


@dataclass(frozen=True)
class Pivot:
    candle_ts: str
    price: float
    kind: str  # support|resistance


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _log_norm(value: float, cap: float) -> float:
    safe_v = max(0.0, float(value))
    safe_cap = max(1.0, float(cap))
    return _clamp01(math.log1p(safe_v) / math.log1p(safe_cap))


def _zone_scores(
    *,
    meaningful_touch_count: int,
    touch_count: int,
    pivot_count: int,
    max_reaction_atr: float,
    carry_score: float,
    body_respect_score: float,
    first_retest_result: str | None,
    zone_width_bps: float,
) -> tuple[float, float, float, float]:
    """Return (strength_score, reaction_score, reaction_efficiency_score, spent_zone_penalty).

    Design goals:
    - avoid saturation from very high touch counts,
    - reward strong reaction behavior and follow-through,
    - penalize over-tested (spent), overly-wide, and chop-heavy zones.
    """

    touch_component = 20.0 * _log_norm(float(meaningful_touch_count), 40.0)
    pivot_component = 16.0 * _log_norm(float(pivot_count), 18.0)
    reaction_component = 28.0 * _clamp01(float(max_reaction_atr) / 2.5)
    carry_component = 16.0 * _clamp01(float(carry_score) / 100.0)
    body_component = 10.0 * _clamp01(float(body_respect_score) / 100.0)

    touch_load = max(float(meaningful_touch_count), float(touch_count), 1.0)
    efficiency_ratio = (0.65 * float(max_reaction_atr) + 0.35 * ((float(carry_score) / 100.0) * 3.0)) / max(math.log1p(touch_load), 1e-9)
    reaction_efficiency = _clamp01(efficiency_ratio / 0.95)
    efficiency_component = 12.0 * reaction_efficiency

    retest_component = 0.0
    if first_retest_result == "reject":
        retest_component = 12.0
    elif first_retest_result == "deviation":
        retest_component = 7.0

    touch_excess = _clamp01((touch_load - 10.0) / 34.0)
    spent_zone_penalty = 28.0 * touch_excess * (1.0 - (0.55 * reaction_efficiency + 0.45 * _clamp01(float(carry_score) / 100.0)))
    width_penalty = 12.0 * _clamp01((float(zone_width_bps) - 300.0) / 220.0)
    chop_penalty = 10.0 * _clamp01((55.0 - float(body_respect_score)) / 55.0)

    strength_raw = 16.0 + touch_component + pivot_component + reaction_component + carry_component + body_component + efficiency_component + retest_component - spent_zone_penalty - width_penalty - chop_penalty
    strength = _clamp01(strength_raw / 100.0) * 100.0
    reaction = _clamp01(float(max_reaction_atr) / 3.0) * 100.0
    return round(strength, 4), round(reaction, 4), round(reaction_efficiency * 100.0, 4), round(spent_zone_penalty, 4)


def atr(candles: list[dict[str, Any]], period: int = 14) -> float:
    if len(candles) < 3:
        return 0.0
    trs: list[float] = []
    prev_close = _as_float(candles[0].get("close"), 0.0)
    for row in candles[1:]:
        high = _as_float(row.get("high"), prev_close)
        low = _as_float(row.get("low"), prev_close)
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(max(0.0, tr))
        prev_close = _as_float(row.get("close"), prev_close)
    tail = trs[-period:] if len(trs) >= period else trs
    return (sum(tail) / len(tail)) if tail else 0.0


def extract_pivots(candles: list[dict[str, Any]], *, k: int = 3) -> list[Pivot]:
    if len(candles) < (2 * k + 1):
        return []
    out: list[Pivot] = []
    for i in range(k, len(candles) - k):
        w = candles[i - k : i + k + 1]
        h = _as_float(candles[i].get("high"))
        l = _as_float(candles[i].get("low"))
        max_h = max(_as_float(x.get("high")) for x in w)
        min_l = min(_as_float(x.get("low")) for x in w)
        ts = str(candles[i].get("close_time") or candles[i].get("candle_ts") or candles[i].get("ts") or "")
        if h >= max_h:
            out.append(Pivot(candle_ts=ts, price=h, kind="resistance"))
        if l <= min_l:
            out.append(Pivot(candle_ts=ts, price=l, kind="support"))
    return out


def _quantile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    idx = (len(sorted_vals) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


def cluster_pivots(
    pivots: list[Pivot],
    *,
    atr_value: float,
    eps: float = 0.75,
    pct_floor: float = 0.0005,
    atr_floor_mult: float = 0.25,
) -> list[dict[str, Any]]:
    if not pivots:
        return []
    safe_atr = max(atr_value, 1e-9)
    ordered = sorted(pivots, key=lambda p: p.price)
    clusters: list[list[Pivot]] = [[ordered[0]]]
    for p in ordered[1:]:
        center = sum(x.price for x in clusters[-1]) / len(clusters[-1])
        if abs(p.price - center) / safe_atr <= eps:
            clusters[-1].append(p)
        else:
            clusters.append([p])

    zones: list[dict[str, Any]] = []
    for idx, c in enumerate(clusters, start=1):
        prices = sorted(x.price for x in c)
        low = _quantile(prices, 0.2)
        high = _quantile(prices, 0.8)
        mid = (low + high) / 2.0
        width = max(high - low, (mid * pct_floor), (safe_atr * atr_floor_mult))
        low = mid - (width / 2.0)
        high = mid + (width / 2.0)
        kinds = {x.kind for x in c}
        kind = "support" if kinds == {"support"} else "resistance" if kinds == {"resistance"} else "mixed"
        zones.append(
            {
                "zone_local_id": idx,
                "zone_low": round(low, 8),
                "zone_high": round(high, 8),
                "zone_mid": round(mid, 8),
                "pivot_count": len(c),
                "zone_kind": kind,
                "source_pivots": c,
            }
        )
    return zones


def _is_meaningful_touch(
    candles: list[dict[str, Any]],
    i: int,
    zone_low: float,
    zone_high: float,
    reaction_atr_min: float,
    atr_value: float,
) -> tuple[bool, str, float, float, float]:
    row = candles[i]
    low = _as_float(row.get("low"))
    high = _as_float(row.get("high"))
    if high < zone_low or low > zone_high:
        return (False, "none", 0.0, 0.0, 0.0)

    close = _as_float(row.get("close"))
    future = candles[i + 1 : i + 4]
    if not future:
        return (False, "none", 0.0, 0.0, 0.0)

    max_up = max(_as_float(x.get("high")) - close for x in future)
    max_dn = max(close - _as_float(x.get("low")) for x in future)
    reaction = max(max_up, max_dn)
    reaction_atr = reaction / max(atr_value, 1e-9)
    meaningful = reaction_atr >= reaction_atr_min
    if max_up > max_dn:
        reaction_type = "reject_up"
    elif max_dn > max_up:
        reaction_type = "reject_down"
    else:
        reaction_type = "flat"

    carry_window = candles[i + 1 : i + 8]
    if carry_window:
        carry_up = max(_as_float(x.get("high")) - close for x in carry_window)
        carry_dn = max(close - _as_float(x.get("low")) for x in carry_window)
    else:
        carry_up = max_up
        carry_dn = max_dn

    if reaction_type == "reject_up":
        carry_atr = carry_up / max(atr_value, 1e-9)
        adverse_atr = carry_dn / max(atr_value, 1e-9)
    elif reaction_type == "reject_down":
        carry_atr = carry_dn / max(atr_value, 1e-9)
        adverse_atr = carry_up / max(atr_value, 1e-9)
    else:
        carry_atr = reaction_atr
        adverse_atr = reaction_atr

    return (meaningful, reaction_type, reaction_atr, carry_atr, adverse_atr)


def evaluate_zone_lifecycle(
    zone: dict[str, Any],
    candles: list[dict[str, Any]],
    *,
    reaction_atr_min: float = 0.35,
    atr_value: float,
    min_meaningful_touches: int = 3,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    low = _as_float(zone.get("zone_low"))
    high = _as_float(zone.get("zone_high"))
    touches: list[dict[str, Any]] = []
    meaningful_count = 0
    confirmed_idx: int | None = None

    carry_samples: list[float] = []
    adverse_samples: list[float] = []
    body_overlap_count = 0
    wick_only_count = 0
    close_inside_count = 0
    directional_close_count = 0
    counter_close_count = 0

    for i, row in enumerate(candles):
        meaningful, reaction_type, reaction_atr, carry_atr, adverse_atr = _is_meaningful_touch(candles, i, low, high, reaction_atr_min, atr_value)
        if reaction_type == "none":
            continue
        ts = str(row.get("close_time") or row.get("candle_ts") or row.get("ts") or "")
        row_open = _as_float(row.get("open"))
        row_close = _as_float(row.get("close"))
        body_low = min(row_open, row_close)
        body_high = max(row_open, row_close)
        body_overlap = not (body_high < low or body_low > high)
        close_inside = low <= row_close <= high
        directional_close = (reaction_type == "reject_up" and row_close >= high) or (reaction_type == "reject_down" and row_close <= low)
        counter_close = (reaction_type == "reject_up" and row_close <= low) or (reaction_type == "reject_down" and row_close >= high)
        touches.append(
            {
                "candle_ts": ts,
                "touch_type": "intersect",
                "reaction_type": reaction_type,
                "reaction_magnitude_atr": round(reaction_atr, 6),
                "carry_magnitude_atr": round(carry_atr, 6),
                "adverse_magnitude_atr": round(adverse_atr, 6),
                "body_overlap": 1 if body_overlap else 0,
                "wick_only": 0 if body_overlap else 1,
                "close_inside": 1 if close_inside else 0,
                "directional_close": 1 if directional_close else 0,
                "counter_close": 1 if counter_close else 0,
                "is_meaningful": 1 if meaningful else 0,
            }
        )
        if meaningful:
            meaningful_count += 1
            carry_samples.append(float(carry_atr))
            adverse_samples.append(float(adverse_atr))
            body_overlap_count += 1 if body_overlap else 0
            wick_only_count += 0 if body_overlap else 1
            close_inside_count += 1 if close_inside else 0
            directional_close_count += 1 if directional_close else 0
            counter_close_count += 1 if counter_close else 0
            if meaningful_count >= min_meaningful_touches and confirmed_idx is None:
                confirmed_idx = i

    carry_ref = _quantile(sorted(carry_samples), 0.8) if carry_samples else 0.0
    adverse_ref = _quantile(sorted(adverse_samples), 0.8) if adverse_samples else 0.0
    meaningful_denom = max(float(meaningful_count), 1.0)
    body_overlap_rate = body_overlap_count / meaningful_denom if meaningful_count else 0.0
    wick_only_rate = wick_only_count / meaningful_denom if meaningful_count else 0.0
    close_inside_rate = close_inside_count / meaningful_denom if meaningful_count else 0.0
    directional_close_rate = directional_close_count / meaningful_denom if meaningful_count else 0.0
    counter_close_rate = counter_close_count / meaningful_denom if meaningful_count else 0.0
    carry_score = _clamp01((carry_ref - (0.35 * adverse_ref)) / 3.0) * 100.0
    body_respect_raw = 0.25 + (0.35 * body_overlap_rate) + (0.45 * directional_close_rate) - (0.45 * close_inside_rate) - (0.70 * counter_close_rate) - (0.20 * wick_only_rate)
    body_respect_score = _clamp01(body_respect_raw) * 100.0

    out = dict(zone)
    out["touch_count"] = len(touches)
    out["meaningful_touch_count"] = meaningful_count
    out["carry_score"] = round(carry_score, 4)
    out["body_respect_score"] = round(body_respect_score, 4)
    out["close_inside_rate"] = round(close_inside_rate, 4)
    out["body_overlap_rate"] = round(body_overlap_rate, 4)
    out["wick_only_rate"] = round(wick_only_rate, 4)
    out["directional_close_rate"] = round(directional_close_rate, 4)
    out["counter_close_rate"] = round(counter_close_rate, 4)
    out["status"] = "confirmed" if meaningful_count >= min_meaningful_touches else "candidate"
    out["first_retest_pending"] = 1 if out["status"] == "confirmed" else 0
    out["first_retest_ts"] = None
    out["first_retest_result"] = None

    if confirmed_idx is not None:
        evt = classify_retest_events(out, candles, confirmed_idx)
        out.update(evt)

    return out, touches


def classify_retest_events(zone: dict[str, Any], candles: list[dict[str, Any]], confirmed_idx: int) -> dict[str, Any]:
    low = _as_float(zone.get("zone_low"))
    high = _as_float(zone.get("zone_high"))
    mid = _as_float(zone.get("zone_mid"))
    first_retest_ts = None
    first_retest_result = None
    deviation_retest = 0

    for i in range(confirmed_idx + 1, len(candles)):
        row = candles[i]
        c_low = _as_float(row.get("low"))
        c_high = _as_float(row.get("high"))
        c_close = _as_float(row.get("close"))
        if c_high < low or c_low > high:
            continue
        ts = str(row.get("close_time") or row.get("candle_ts") or row.get("ts") or "")
        first_retest_ts = ts
        if c_close > high:
            first_retest_result = "reject"
        elif c_close < low:
            first_retest_result = "accept"
        else:
            first_retest_result = "deviation"

        if i + 2 < len(candles):
            n1 = _as_float(candles[i + 1].get("close"))
            n2 = _as_float(candles[i + 2].get("close"))
            if (c_close < low and n1 > high and n2 > mid) or (c_close > high and n1 < low and n2 < mid):
                deviation_retest = 1
        break

    return {
        "first_retest_pending": 0 if first_retest_ts else 1,
        "first_retest_ts": first_retest_ts,
        "first_retest_result": first_retest_result,
        "deviation_retest": deviation_retest,
    }


def build_zones_for_tf(
    symbol: str,
    tf: str,
    candles: list[dict[str, Any]],
    *,
    pivot_k: int = 3,
    cluster_eps: float = 0.75,
    reaction_atr_min: float = 0.35,
    min_meaningful_touches: int = 3,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pivots = extract_pivots(candles, k=pivot_k)
    tf_atr = atr(candles)
    zones = cluster_pivots(pivots, atr_value=tf_atr, eps=cluster_eps)
    final_zones: list[dict[str, Any]] = []
    touches: list[dict[str, Any]] = []
    for idx, zone in enumerate(zones, start=1):
        z, t = evaluate_zone_lifecycle(
            zone,
            candles,
            atr_value=tf_atr,
            reaction_atr_min=reaction_atr_min,
            min_meaningful_touches=min_meaningful_touches,
        )
        zone_id = f"{symbol}:{tf}:{idx}:{round(z['zone_mid'], 4)}"
        reaction_samples = sorted(float(x.get("reaction_magnitude_atr") or 0.0) for x in t)
        reaction_ref_atr = _quantile(reaction_samples, 0.8) if reaction_samples else 0.0
        zone_mid = float(z.get("zone_mid") or 0.0)
        zone_low = float(z.get("zone_low") or 0.0)
        zone_high = float(z.get("zone_high") or 0.0)
        zone_width_bps = ((zone_high - zone_low) / max(abs(zone_mid), 1e-9)) * 10000.0 if zone_mid > 0 else 0.0
        carry_score = float(z.get("carry_score") or 0.0)
        body_respect_score = float(z.get("body_respect_score") or 0.0)
        strength_score, reaction_score, reaction_efficiency_score, spent_zone_penalty = _zone_scores(
            meaningful_touch_count=int(z.get("meaningful_touch_count") or 0),
            touch_count=int(z.get("touch_count") or 0),
            pivot_count=int(z.get("pivot_count") or 0),
            max_reaction_atr=float(reaction_ref_atr),
            carry_score=carry_score,
            body_respect_score=body_respect_score,
            first_retest_result=z.get("first_retest_result") if isinstance(z.get("first_retest_result"), str) else None,
            zone_width_bps=float(zone_width_bps),
        )
        z.update(
            {
                "zone_id": zone_id,
                "symbol": symbol,
                "tf": tf,
                "strength_score": strength_score,
                "reaction_score": reaction_score,
                "reaction_efficiency_score": reaction_efficiency_score,
                "spent_zone_penalty": spent_zone_penalty,
                "retest_weight": 1.0,
                "selection_score": strength_score,
                "zone_width_bps": round(zone_width_bps, 4),
                "carry_score": round(carry_score, 4),
                "body_respect_score": round(body_respect_score, 4),
                "source_version": "sr_engine_v2",
            }
        )
        for j, touch in enumerate(t, start=1):
            touch["touch_id"] = f"{zone_id}:{j}"
            touch["zone_id"] = zone_id
            touch["symbol"] = symbol
            touch["tf"] = tf
        final_zones.append(z)
        touches.extend(t)
    return final_zones, touches


def profile_anchor_and_eligible(profile_id: str) -> tuple[str, tuple[str, ...]]:
    p = (profile_id or "I").upper()
    eligible = PROFILE_ELIGIBILITY.get(p, PROFILE_ELIGIBILITY["I"])
    return eligible[0], eligible


def _zone_fmt_with_distance(z: dict[str, Any] | None, *, distance_bps: float | None = None, entry: float | None = None) -> dict[str, Any] | None:
    if not z:
        return None

    if distance_bps is None:
        mid = _as_float(z.get("zone_mid"), entry if entry is not None else 0.0)
        e = _as_float(entry, mid)
        distance_bps = abs(e - mid) / max(abs(mid), 1e-9) * 10000.0

    return {
        "zone_id": z.get("zone_id"),
        "tf": z.get("tf"),
        "status": z.get("status"),
        "bounds": {
            "low": z.get("zone_low"),
            "high": z.get("zone_high"),
            "mid": z.get("zone_mid"),
        },
        "strength": z.get("strength_score"),
        "touch_count": z.get("touch_count"),
        "meaningful_touch_count": z.get("meaningful_touch_count"),
        "first_retest_status": z.get("first_retest_result"),
        "distance_bps": round(float(distance_bps), 4),
        "diagnostics": {
            "reaction_score": z.get("reaction_score"),
            "reaction_efficiency_score": z.get("reaction_efficiency_score"),
            "carry_score": z.get("carry_score"),
            "body_respect_score": z.get("body_respect_score"),
            "spent_zone_penalty": z.get("spent_zone_penalty"),
            "retest_weight": z.get("retest_weight"),
            "selection_score": z.get("selection_score"),
            "zone_width_bps": z.get("zone_width_bps"),
            "close_inside_rate": z.get("close_inside_rate"),
            "body_overlap_rate": z.get("body_overlap_rate"),
            "wick_only_rate": z.get("wick_only_rate"),
            "directional_close_rate": z.get("directional_close_rate"),
            "counter_close_rate": z.get("counter_close_rate"),
        },
    }


def nearest_sr_levels_v1(*, profile_id: str, entry: float, zones: list[dict[str, Any]]) -> dict[str, Any]:
    """Return nearest-4 S/R payload for verification UI and downstream services.

    Selection:
    - nearest + next support
    - nearest + next resistance
    Distance is edge-based, with overlapping zones scored as 0 bps.
    """

    anchor_tf, eligible_tfs = profile_anchor_and_eligible(profile_id)
    allowed = [z for z in zones if z.get("status") == "confirmed" and str(z.get("tf")) in eligible_tfs]

    def _support_distance_bps(z: dict[str, Any]) -> float:
        low = _as_float(z.get("zone_low"), entry)
        high = _as_float(z.get("zone_high"), entry)
        overlap = low <= entry <= high
        if overlap:
            return 0.0
        if high <= entry:
            return ((entry - high) / max(abs(entry), 1e-9)) * 10000.0
        return 999999.0

    def _resistance_distance_bps(z: dict[str, Any]) -> float:
        low = _as_float(z.get("zone_low"), entry)
        high = _as_float(z.get("zone_high"), entry)
        overlap = low <= entry <= high
        if overlap:
            return 0.0
        if low >= entry:
            return ((low - entry) / max(abs(entry), 1e-9)) * 10000.0
        return 999999.0

    supports_ranked: list[tuple[float, float, dict[str, Any]]] = []
    resistances_ranked: list[tuple[float, float, dict[str, Any]]] = []

    for z in allowed:
        strength = _as_float(z.get("strength_score"), 0.0)
        d_sup = _support_distance_bps(z)
        if d_sup < 999999.0:
            supports_ranked.append((d_sup, -strength, z))

        d_res = _resistance_distance_bps(z)
        if d_res < 999999.0:
            resistances_ranked.append((d_res, -strength, z))

    supports_ranked.sort(key=lambda x: (x[0], x[1]))
    resistances_ranked.sort(key=lambda x: (x[0], x[1]))

    def _pick_unique(candidates: list[tuple[float, float, dict[str, Any]]], used_ids: set[str]) -> tuple[float, float, dict[str, Any]] | None:
        for row in candidates:
            zid = str(row[2].get("zone_id") or "")
            if zid and zid not in used_ids:
                used_ids.add(zid)
                return row
        return None

    used_ids: set[str] = set()
    nearest_support = _pick_unique(supports_ranked, used_ids)
    next_support = _pick_unique(supports_ranked, used_ids)
    nearest_resistance = _pick_unique(resistances_ranked, used_ids)
    next_resistance = _pick_unique(resistances_ranked, used_ids)

    return {
        "contract": "nearest_sr_v1",
        "sr_anchor_tf": anchor_tf,
        "sr_eligible_tfs": list(eligible_tfs),
        "entry": float(entry),
        "nearest_support": _zone_fmt_with_distance(nearest_support[2], distance_bps=nearest_support[0], entry=entry) if nearest_support else None,
        "next_support": _zone_fmt_with_distance(next_support[2], distance_bps=next_support[0], entry=entry) if next_support else None,
        "nearest_resistance": _zone_fmt_with_distance(nearest_resistance[2], distance_bps=nearest_resistance[0], entry=entry) if nearest_resistance else None,
        "next_resistance": _zone_fmt_with_distance(next_resistance[2], distance_bps=next_resistance[0], entry=entry) if next_resistance else None,
        "available_confirmed_zones": len(allowed),
    }


def nearest_sr_query(*, profile_id: str, side: str, entry: float, zones: list[dict[str, Any]]) -> dict[str, Any]:
    nearest4 = nearest_sr_levels_v1(profile_id=profile_id, entry=entry, zones=zones)
    nearest_support = nearest4.get("nearest_support")
    nearest_resistance = nearest4.get("nearest_resistance")

    primary = nearest_support if side == "buy" else nearest_resistance
    distance_bps = float(primary.get("distance_bps")) if isinstance(primary, dict) else 999999.0
    first_retest_ok = bool(primary and primary.get("first_retest_status") in {"reject", "deviation"})

    reasons: list[str] = []
    if primary is None:
        reasons.append("SR_ZONE_NOT_FOUND")
    elif not first_retest_ok:
        reasons.append("SR_RETEST_NOT_ELIGIBLE")

    return {
        "sr_anchor_tf": nearest4.get("sr_anchor_tf"),
        "sr_eligible_tfs": nearest4.get("sr_eligible_tfs", []),
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "distance_bps": round(distance_bps, 4),
        "first_retest_eligible": first_retest_ok,
        "gate_eligible": not reasons,
        "reason_codes": reasons,
    }


def persist_sr_state(conn: Any, zones: list[dict[str, Any]], touches: list[dict[str, Any]]) -> None:
    with conn:
        for z in zones:
            conn.execute(
                """
                INSERT INTO sr_zones(
                    zone_id, symbol, tf, zone_low, zone_high, zone_mid, status,
                    touch_count, meaningful_touch_count, first_retest_pending, first_retest_ts,
                    first_retest_result, strength_score, reaction_score,
                    reaction_efficiency_score, spent_zone_penalty, retest_weight, selection_score, zone_width_bps,
                    carry_score, body_respect_score, close_inside_rate, body_overlap_rate, wick_only_rate,
                    directional_close_rate, counter_close_rate,
                    created_ts, updated_ts, source_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
                ON CONFLICT(zone_id) DO UPDATE SET
                    zone_low=excluded.zone_low,
                    zone_high=excluded.zone_high,
                    zone_mid=excluded.zone_mid,
                    status=excluded.status,
                    touch_count=excluded.touch_count,
                    meaningful_touch_count=excluded.meaningful_touch_count,
                    first_retest_pending=excluded.first_retest_pending,
                    first_retest_ts=excluded.first_retest_ts,
                    first_retest_result=excluded.first_retest_result,
                    strength_score=excluded.strength_score,
                    reaction_score=excluded.reaction_score,
                    reaction_efficiency_score=excluded.reaction_efficiency_score,
                    spent_zone_penalty=excluded.spent_zone_penalty,
                    retest_weight=excluded.retest_weight,
                    selection_score=excluded.selection_score,
                    zone_width_bps=excluded.zone_width_bps,
                    carry_score=excluded.carry_score,
                    body_respect_score=excluded.body_respect_score,
                    close_inside_rate=excluded.close_inside_rate,
                    body_overlap_rate=excluded.body_overlap_rate,
                    wick_only_rate=excluded.wick_only_rate,
                    directional_close_rate=excluded.directional_close_rate,
                    counter_close_rate=excluded.counter_close_rate,
                    updated_ts=datetime('now'),
                    source_version=excluded.source_version;
                """,
                (
                    z.get("zone_id"), z.get("symbol"), z.get("tf"), z.get("zone_low"), z.get("zone_high"), z.get("zone_mid"), z.get("status"),
                    int(z.get("touch_count") or 0), int(z.get("meaningful_touch_count") or 0), int(z.get("first_retest_pending") or 0), z.get("first_retest_ts"),
                    z.get("first_retest_result"), z.get("strength_score"), z.get("reaction_score"),
                    z.get("reaction_efficiency_score"), z.get("spent_zone_penalty"), z.get("retest_weight"), z.get("selection_score"), z.get("zone_width_bps"),
                    z.get("carry_score"), z.get("body_respect_score"), z.get("close_inside_rate"), z.get("body_overlap_rate"), z.get("wick_only_rate"),
                    z.get("directional_close_rate"), z.get("counter_close_rate"),
                    z.get("source_version"),
                ),
            )

        for t in touches:
            conn.execute(
                """
                INSERT OR REPLACE INTO sr_zone_touches(
                    touch_id, zone_id, symbol, tf, candle_ts, touch_type,
                    reaction_type, reaction_magnitude_atr, is_meaningful
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    t.get("touch_id"), t.get("zone_id"), t.get("symbol"), t.get("tf"), t.get("candle_ts"),
                    t.get("touch_type"), t.get("reaction_type"), t.get("reaction_magnitude_atr"), int(t.get("is_meaningful") or 0),
                ),
            )
