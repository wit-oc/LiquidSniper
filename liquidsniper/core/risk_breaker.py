from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass
class GlobalDrawdownState:
    trading_day: str
    starting_equity_usd: float
    realized_pnl_usd: float = 0.0
    unrealized_pnl_usd: float = 0.0
    tripped: bool = False
    trip_reason: str = ""

    @property
    def total_pnl_usd(self) -> float:
        return float(self.realized_pnl_usd) + float(self.unrealized_pnl_usd)

    @property
    def drawdown_usd(self) -> float:
        return max(0.0, -self.total_pnl_usd)


def utc_day(now: datetime | None = None) -> str:
    dt = now or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date().isoformat()


def _default_state(starting_equity_usd: float, day: str) -> GlobalDrawdownState:
    return GlobalDrawdownState(trading_day=day, starting_equity_usd=float(starting_equity_usd))


def load_state(path: Path, *, starting_equity_usd: float, day: str | None = None) -> GlobalDrawdownState:
    target_day = day or utc_day()
    if not path.exists():
        return _default_state(starting_equity_usd, target_day)

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        state = GlobalDrawdownState(
            trading_day=str(payload["trading_day"]),
            starting_equity_usd=float(payload["starting_equity_usd"]),
            realized_pnl_usd=float(payload.get("realized_pnl_usd", 0.0)),
            unrealized_pnl_usd=float(payload.get("unrealized_pnl_usd", 0.0)),
            tripped=bool(payload.get("tripped", False)),
            trip_reason=str(payload.get("trip_reason", "")),
        )
    except Exception as exc:
        raise ValueError("BREAKER_STATE_UNREADABLE") from exc

    if state.trading_day != target_day:
        return _default_state(starting_equity_usd, target_day)
    return state


def persist_state(path: Path, state: GlobalDrawdownState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def evaluate_drawdown(
    state: GlobalDrawdownState,
    *,
    max_daily_drawdown_usd: float | None,
    max_daily_drawdown_pct: float | None,
) -> tuple[bool, str]:
    drawdown_usd = state.drawdown_usd
    abs_limit = float(max_daily_drawdown_usd) if max_daily_drawdown_usd is not None else None
    pct_limit = None
    if max_daily_drawdown_pct is not None:
        pct_limit = max(0.0, float(max_daily_drawdown_pct)) * max(0.0, state.starting_equity_usd)

    if abs_limit is not None and drawdown_usd >= abs_limit:
        return True, "GLOBAL_DRAWDOWN_TRIPPED_ABSOLUTE"
    if pct_limit is not None and drawdown_usd >= pct_limit:
        return True, "GLOBAL_DRAWDOWN_TRIPPED_PERCENT"
    return False, ""


def apply_pnl(state: GlobalDrawdownState, *, realized_delta_usd: float = 0.0, unrealized_pnl_usd: float | None = None) -> GlobalDrawdownState:
    state.realized_pnl_usd = round(float(state.realized_pnl_usd) + float(realized_delta_usd), 8)
    if unrealized_pnl_usd is not None:
        state.unrealized_pnl_usd = round(float(unrealized_pnl_usd), 8)
    return state
