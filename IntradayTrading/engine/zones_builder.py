from __future__ import annotations

from typing import List

from .structure import detect_pivots
from .zones import Zone, ZoneEngine, ZoneKind


def build_zones_from_candles(
    highs: List[float],
    lows: List[float],
    left: int = 2,
    right: int = 2,
    width_frac: float = 0.001,
    merge_overlap_ratio: float = 0.2,
) -> List[Zone]:
    """Build deterministic SR zones from pivot highs/lows."""
    pivots = detect_pivots(highs, lows, left=left, right=right)
    engine = ZoneEngine(merge_overlap_ratio=merge_overlap_ratio)

    for p in pivots:
        half_width = max(abs(p.price) * width_frac, 1e-9)
        z = Zone(
            id=f"z_{p.kind}_{p.index}",
            kind=ZoneKind.RESISTANCE if p.kind == "high" else ZoneKind.SUPPORT,
            low=p.price - half_width,
            high=p.price + half_width,
            created_at=p.index,
        )
        engine.add_zone(z)

    return engine.active_zones()
