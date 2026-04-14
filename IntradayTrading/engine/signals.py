from __future__ import annotations

from dataclasses import dataclass

from .risk import BreakerState
from .structure import StructureBias


@dataclass
class SignalContext:
    structure_bias: StructureBias
    zone_touched: bool
    reclaim_confirmed: bool
    filters_passed: bool
    breaker: BreakerState
    at_risk_count: int
    max_at_risk: int


def should_enter_long(ctx: SignalContext) -> bool:
    return (
        ctx.structure_bias in (StructureBias.BULLISH,)
        and ctx.zone_touched
        and ctx.reclaim_confirmed
        and ctx.filters_passed
        and ctx.breaker.is_open
        and (ctx.at_risk_count < ctx.max_at_risk)
    )


def should_enter_short(ctx: SignalContext) -> bool:
    return (
        ctx.structure_bias in (StructureBias.BEARISH,)
        and ctx.zone_touched
        and ctx.reclaim_confirmed
        and ctx.filters_passed
        and ctx.breaker.is_open
        and (ctx.at_risk_count < ctx.max_at_risk)
    )


def apply_tp1_to_be(position: dict, costs_buffer_frac: float = 0.0) -> dict:
    """Mutates + returns position with BE stop behavior after TP1.

    Expected keys: side, entry, stop, tp1_hit, is_at_risk
    """
    if not position.get("tp1_hit", False):
        return position

    entry = float(position["entry"])
    side = position.get("side", "long")
    if side == "long":
        position["stop"] = entry * (1 + costs_buffer_frac)
    else:
        position["stop"] = entry * (1 - costs_buffer_frac)

    position["is_at_risk"] = False
    return position
