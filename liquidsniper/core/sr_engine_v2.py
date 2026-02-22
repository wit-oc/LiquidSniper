from __future__ import annotations

from dataclasses import dataclass
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


def _is_meaningful_touch(candles: list[dict[str, Any]], i: int, zone_low: float, zone_high: float, reaction_atr_min: float, atr_value: float) -> tuple[bool, str, float]:
    row = candles[i]
    low = _as_float(row.get("low"))
    high = _as_float(row.get("high"))
    if high < zone_low or low > zone_high:
        return (False, "none", 0.0)

    close = _as_float(row.get("close"))
    future = candles[i + 1 : i + 4]
    if not future:
        return (False, "none", 0.0)

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
    return (meaningful, reaction_type, reaction_atr)


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

    for i, row in enumerate(candles):
        meaningful, reaction_type, reaction_atr = _is_meaningful_touch(candles, i, low, high, reaction_atr_min, atr_value)
        if reaction_type == "none":
            continue
        ts = str(row.get("close_time") or row.get("candle_ts") or row.get("ts") or "")
        touches.append(
            {
                "candle_ts": ts,
                "touch_type": "intersect",
                "reaction_type": reaction_type,
                "reaction_magnitude_atr": round(reaction_atr, 6),
                "is_meaningful": 1 if meaningful else 0,
            }
        )
        if meaningful:
            meaningful_count += 1
            if meaningful_count >= min_meaningful_touches and confirmed_idx is None:
                confirmed_idx = i

    out = dict(zone)
    out["touch_count"] = len(touches)
    out["meaningful_touch_count"] = meaningful_count
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


def build_zones_for_tf(symbol: str, tf: str, candles: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pivots = extract_pivots(candles)
    tf_atr = atr(candles)
    zones = cluster_pivots(pivots, atr_value=tf_atr)
    final_zones: list[dict[str, Any]] = []
    touches: list[dict[str, Any]] = []
    for idx, zone in enumerate(zones, start=1):
        z, t = evaluate_zone_lifecycle(zone, candles, atr_value=tf_atr)
        zone_id = f"{symbol}:{tf}:{idx}:{round(z['zone_mid'], 4)}"
        z.update(
            {
                "zone_id": zone_id,
                "symbol": symbol,
                "tf": tf,
                "strength_score": round(min(100.0, z["meaningful_touch_count"] * 20.0 + z["pivot_count"] * 5.0), 4),
                "reaction_score": round(min(100.0, max((x.get("reaction_magnitude_atr") or 0.0) for x in t) * 25.0 if t else 0.0), 4),
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


def nearest_sr_query(*, profile_id: str, side: str, entry: float, zones: list[dict[str, Any]]) -> dict[str, Any]:
    anchor_tf, eligible_tfs = profile_anchor_and_eligible(profile_id)
    allowed = [z for z in zones if z.get("status") == "confirmed" and str(z.get("tf")) in eligible_tfs]

    supports = [z for z in allowed if _as_float(z.get("zone_high")) <= entry]
    resistances = [z for z in allowed if _as_float(z.get("zone_low")) >= entry]

    def _dist(z: dict[str, Any]) -> float:
        mid = _as_float(z.get("zone_mid"), entry)
        return abs(entry - mid) / max(abs(mid), 1e-9) * 10000.0

    nearest_support = min(supports, key=_dist) if supports else None
    nearest_resistance = min(resistances, key=_dist) if resistances else None

    primary = nearest_support if side == "buy" else nearest_resistance
    distance_bps = _dist(primary) if primary else 999999.0
    first_retest_ok = bool(primary and primary.get("first_retest_result") in {"reject", "deviation"})

    def _fmt(z: dict[str, Any] | None) -> dict[str, Any] | None:
        if not z:
            return None
        return {
            "zone_id": z.get("zone_id"),
            "tf": z.get("tf"),
            "bounds": {"low": z.get("zone_low"), "high": z.get("zone_high"), "mid": z.get("zone_mid")},
            "strength": z.get("strength_score"),
            "touch_count": z.get("touch_count"),
            "first_retest_status": z.get("first_retest_result"),
            "distance_bps": round(_dist(z), 4),
        }

    reasons: list[str] = []
    if primary is None:
        reasons.append("SR_ZONE_NOT_FOUND")
    elif not first_retest_ok:
        reasons.append("SR_RETEST_NOT_ELIGIBLE")

    return {
        "sr_anchor_tf": anchor_tf,
        "sr_eligible_tfs": list(eligible_tfs),
        "nearest_support": _fmt(nearest_support),
        "nearest_resistance": _fmt(nearest_resistance),
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
                    first_retest_result, strength_score, reaction_score, created_ts, updated_ts, source_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
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
                    updated_ts=datetime('now'),
                    source_version=excluded.source_version;
                """,
                (
                    z.get("zone_id"), z.get("symbol"), z.get("tf"), z.get("zone_low"), z.get("zone_high"), z.get("zone_mid"), z.get("status"),
                    int(z.get("touch_count") or 0), int(z.get("meaningful_touch_count") or 0), int(z.get("first_retest_pending") or 0), z.get("first_retest_ts"),
                    z.get("first_retest_result"), z.get("strength_score"), z.get("reaction_score"), z.get("source_version"),
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
