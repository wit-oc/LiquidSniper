from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BankrollSnapshot:
    starting_equity_usd: float
    available_usd: float
    reserved_risk_usd: float
    realized_pnl_usd: float


class BankrollState:
    def __init__(self, starting_equity_usd: float) -> None:
        if float(starting_equity_usd) <= 0:
            raise ValueError("starting_equity_usd must be > 0")
        self._starting = float(starting_equity_usd)
        self._available = float(starting_equity_usd)
        self._reserved = 0.0
        self._realized = 0.0

    def reserve_risk(self, risk_usd: float) -> bool:
        risk = float(risk_usd)
        if risk <= 0:
            raise ValueError("risk_usd must be > 0")
        if risk > self._available:
            return False
        self._available -= risk
        self._reserved += risk
        return True

    def release_reserved(self, risk_usd: float) -> None:
        risk = float(risk_usd)
        if risk < 0:
            raise ValueError("risk_usd must be >= 0")
        if risk > self._reserved:
            raise ValueError("cannot release more than reserved")
        self._reserved -= risk
        self._available += risk

    def realize_pnl(self, pnl_usd: float) -> None:
        pnl = float(pnl_usd)
        self._realized += pnl
        self._available += pnl

    def snapshot(self) -> BankrollSnapshot:
        return BankrollSnapshot(
            starting_equity_usd=self._starting,
            available_usd=round(self._available, 8),
            reserved_risk_usd=round(self._reserved, 8),
            realized_pnl_usd=round(self._realized, 8),
        )
