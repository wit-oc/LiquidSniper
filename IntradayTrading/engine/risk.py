from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BreakerState:
    daily_locked: bool = False
    weekly_locked: bool = False

    @property
    def is_open(self) -> bool:
        return not (self.daily_locked or self.weekly_locked)


@dataclass
class RiskConfig:
    risk_per_trade_pct: float = 1.0
    daily_loss_limit_pct: float = 6.0
    weekly_dd_limit_pct: float = 20.0
    max_at_risk_positions: int = 2


class RiskEngine:
    def __init__(self, cfg: RiskConfig):
        self.cfg = cfg
        self.breaker = BreakerState()

    def position_size(self, equity: float, entry: float, stop: float) -> float:
        risk_amount = equity * (self.cfg.risk_per_trade_pct / 100.0)
        per_unit_risk = abs(entry - stop)
        if per_unit_risk <= 0:
            return 0.0
        return risk_amount / per_unit_risk

    def update_breakers(
        self,
        day_pnl_pct: float,
        week_pnl_pct: float,
    ) -> BreakerState:
        self.breaker.daily_locked = day_pnl_pct <= -self.cfg.daily_loss_limit_pct
        self.breaker.weekly_locked = week_pnl_pct <= -self.cfg.weekly_dd_limit_pct
        return self.breaker


def at_risk_count(positions: list[dict]) -> int:
    """Count only positions still carrying downside risk.

    Convention: each position dict has `is_at_risk: bool`.
    A TP1->BE migration sets it to False.
    """
    return sum(1 for p in positions if p.get("is_at_risk", True))
