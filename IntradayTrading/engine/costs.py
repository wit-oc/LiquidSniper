from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostModel:
    taker_bps: float = 5.0
    maker_bps: float = 2.0
    funding_bps_per_8h: float = 1.0
    slippage_bps: float = 2.0


def bps_to_frac(bps: float) -> float:
    return bps / 10_000.0


def estimated_round_trip_cost_frac(model: CostModel, use_taker: bool = True) -> float:
    fee_bps = model.taker_bps if use_taker else model.maker_bps
    # entry + exit + one-sided slippage for conservative baseline
    return bps_to_frac((2 * fee_bps) + model.slippage_bps)


def funding_cost_frac(model: CostModel, hold_hours: float) -> float:
    return bps_to_frac(model.funding_bps_per_8h * (hold_hours / 8.0))
