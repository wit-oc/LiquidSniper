from __future__ import annotations

from datetime import datetime, timezone

from liquidsniper.core.paper_policy import ThrottleState, load_profile_policy
from liquidsniper.ops import paper_daemon


def _state_with_position(*, side: str) -> ThrottleState:
    return ThrottleState(
        trading_day="2026-02-25",
        last_entry_ts=None,
        trades_open=1,
        executed_today=1,
        realized_pnl_today_usd=0.0,
        seen_idempotency_keys=[],
        open_positions=[
            {
                "position_id": "p1",
                "run_id": "r1",
                "symbol": "BTCUSDT",
                "strategy": "intraday",
                "side": side,
                "status": "open",
                "stop_state": "initial",
                "opened_cycle": 1,
                "opened_ts": "2026-02-25T00:00:00+00:00",
                "entry": 100.0,
                "stop_loss_initial": 98.0 if side == "buy" else 102.0,
                "tp_levels": [101.0, 102.0] if side == "buy" else [99.0, 98.0],
                "risk_usd": 25.0,
                "tp1_ts": None,
                "closed_ts": None,
                "exit_reason": None,
                "exit_price": None,
                "realized_pnl_usd": None,
            }
        ],
    )


def test_build_proposal_short_tp_levels_are_below_entry(monkeypatch):
    monkeypatch.setenv("LIQUIDSNIPER_PROFILE_ID", "I")
    policy = load_profile_policy()

    proposal, _ = paper_daemon._build_proposal(
        "BTCUSDT",
        strategy="intraday",
        now=datetime(2026, 2, 25, 12, 0, tzinfo=timezone.utc),
        cycle_count=1,
        profile_policy=policy,
        market_snapshot={
            "side": "sell",
            "entry": 100.0,
            "candle_ts": "2026-02-25T12:00:00+00:00",
            "htf_chop": 50.0,
            "secondary_hits": 2,
            "htf_chop_penalty": 0.0,
            "sr_penalty": 0.0,
        },
        gate_reason_codes=(),
        gate_checks={},
    )

    tp_levels = proposal["tp_levels"]
    assert tp_levels == [99.0, 98.0]
    assert all(float(x) < 100.0 for x in tp_levels)


def test_be_promotion_occurs_on_tp1_touch_for_long(tmp_path, monkeypatch):
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path))
    state = _state_with_position(side="buy")

    now = datetime(2026, 2, 25, 12, 0, tzinfo=timezone.utc)
    closed = paper_daemon._close_open_positions_for_symbol(state, symbol="BTCUSDT", mark_price=101.0, now=now)

    assert closed == []
    pos = state.open_positions[0]
    assert pos["status"] == "open"
    assert pos["stop_state"] == "be"
    assert pos["tp1_ts"] is not None


def test_be_stop_closes_position_after_promotion_for_long(tmp_path, monkeypatch):
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path))
    state = _state_with_position(side="buy")

    now = datetime(2026, 2, 25, 12, 0, tzinfo=timezone.utc)
    paper_daemon._close_open_positions_for_symbol(state, symbol="BTCUSDT", mark_price=101.0, now=now)
    closed = paper_daemon._close_open_positions_for_symbol(state, symbol="BTCUSDT", mark_price=100.0, now=now)

    assert len(closed) == 1
    assert closed[0]["exit_reason"] == "BE_STOP_HIT"
