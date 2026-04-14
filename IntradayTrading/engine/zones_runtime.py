from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .zones import Zone, ZoneKind, ZoneState


@dataclass
class ZoneInteraction:
    zone_id: str
    kind: ZoneKind
    low: float
    high: float
    touched: bool
    reclaimed: bool
    distance_bps: float


def find_interaction(
    zones: List[Zone],
    close_price: float,
    high_price: float,
    low_price: float,
    max_zone_width_frac: float = 0.02,
    reclaim_buffer_frac: float = 0.0005,
    near_retest_bps_max: float = 0.0,
) -> Optional[ZoneInteraction]:
    """Return best active zone interaction for current bar.

    Filters:
    - Skip oversized zones (zone_width / close > max_zone_width_frac)
    - Prefer closest zone by center distance to close
    """
    candidates: list[tuple[float, Zone, bool]] = []
    for z in zones:
        if z.state not in (ZoneState.ACTIVE, ZoneState.FLIPPED):
            continue

        zone_width_frac = (z.high - z.low) / max(abs(close_price), 1e-9)
        if zone_width_frac > max_zone_width_frac:
            continue

        touched = (low_price <= z.high) and (high_price >= z.low)
        if touched:
            distance_bps = 0.0
        elif close_price > z.high:
            distance_bps = ((close_price - z.high) / max(abs(close_price), 1e-9)) * 10_000.0
        else:
            distance_bps = ((z.low - close_price) / max(abs(close_price), 1e-9)) * 10_000.0

        if not touched and distance_bps > near_retest_bps_max:
            continue

        candidates.append((distance_bps, z, touched))

    if not candidates:
        return None

    distance_bps, z, touched = sorted(candidates, key=lambda x: x[0])[0]
    if z.kind == ZoneKind.SUPPORT:
        reclaimed = close_price >= (z.high * (1 + reclaim_buffer_frac))
    else:
        reclaimed = close_price <= (z.low * (1 - reclaim_buffer_frac))

    return ZoneInteraction(zone_id=z.id, kind=z.kind, low=z.low, high=z.high, touched=touched, reclaimed=reclaimed, distance_bps=distance_bps)
