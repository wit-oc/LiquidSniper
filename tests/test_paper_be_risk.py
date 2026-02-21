from datetime import datetime, timezone

from liquidsniper.core.paper_policy import ThrottleState, count_active_risk_positions
from liquidsniper.ops.paper_daemon import _promote_positions_to_be


def test_tp1_promotion_reduces_active_risk_count() -> None:
    state = ThrottleState(
        trading_day="2026-02-20",
        last_entry_ts=None,
        trades_open=2,
        executed_today=2,
        realized_pnl_today_usd=0.0,
        seen_idempotency_keys=[],
        open_positions=[
            {"position_id": "p1", "symbol": "BTCUSDT", "strategy": "intraday", "status": "open", "stop_state": "initial", "opened_cycle": 1, "tp1_ts": None},
            {"position_id": "p2", "symbol": "ETHUSDT", "strategy": "intraday", "status": "open", "stop_state": "be", "opened_cycle": 1, "tp1_ts": "2026-02-20T00:00:00+00:00"},
        ],
    )

    assert count_active_risk_positions(state) == 1
    promoted, _ = _promote_positions_to_be(state, now=datetime(2026, 2, 20, 15, 0, tzinfo=timezone.utc), cycle_count=2)
    assert promoted == 1
    assert count_active_risk_positions(state) == 0
