from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STRATEGY_BY_PROFILE = {
    "C": "scalp",
    "I": "intraday",
    "S": "swing",
}


@dataclass(frozen=True)
class StrategySummary:
    strategy: str
    profile_id: str
    runs_total: int
    executed_total: int
    rejected_total: int
    open_positions: int
    latest_run_ts: str | None


@dataclass(frozen=True)
class OrderFlowRow:
    run_id: str
    timestamp: str
    strategy: str
    profile_id: str
    symbol: str
    side: str
    decision_tier: str | None
    execution_decision: str
    proposal_decision: str
    test_id: str | None


@dataclass(frozen=True)
class PositionRow:
    strategy: str
    profile_id: str
    symbol: str
    side: str
    entry: float | None
    stop_loss_initial: float | None
    risk_usd: float | None
    run_id: str
    timestamp: str


@dataclass(frozen=True)
class GateEventRow:
    run_id: str
    timestamp: str
    strategy: str
    profile_id: str
    symbol: str
    event_type: str
    code: str
    gate_passed: bool
    test_id: str | None


SNAPSHOT_SCHEMA: dict[str, Any] = {
    "strategies": "list[StrategySummary]",
    "orders": "list[OrderFlowRow]",
    "positions": "list[PositionRow]",
    "events": "list[GateEventRow]",
    "meta": {
        "read_only": True,
        "filters": {
            "strategy": "scalp|intraday|swing",
            "run_id": "string",
            "test_id": "string",
            "limit": "int",
        },
    },
}
