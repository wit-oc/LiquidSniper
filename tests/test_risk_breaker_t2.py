from pathlib import Path

from liquidsniper.core.risk_breaker import (
    apply_pnl,
    evaluate_drawdown,
    load_state,
    persist_state,
)


def test_global_breaker_tracks_realized_plus_unrealized_and_absolute_precedence(tmp_path: Path):
    p = tmp_path / "state.json"
    state = load_state(p, starting_equity_usd=1000, day="2026-02-20")
    apply_pnl(state, realized_delta_usd=-120, unrealized_pnl_usd=-85)

    tripped, reason = evaluate_drawdown(state, max_daily_drawdown_usd=200, max_daily_drawdown_pct=0.30)
    assert tripped is True
    assert reason == "GLOBAL_DRAWDOWN_TRIPPED_ABSOLUTE"


def test_global_breaker_percent_threshold(tmp_path: Path):
    p = tmp_path / "state.json"
    state = load_state(p, starting_equity_usd=1000, day="2026-02-20")
    apply_pnl(state, realized_delta_usd=-150, unrealized_pnl_usd=-160)

    tripped, reason = evaluate_drawdown(state, max_daily_drawdown_usd=400, max_daily_drawdown_pct=0.30)
    assert tripped is True
    assert reason == "GLOBAL_DRAWDOWN_TRIPPED_PERCENT"


def test_state_persists_and_resets_by_day(tmp_path: Path):
    p = tmp_path / "state.json"
    state = load_state(p, starting_equity_usd=500, day="2026-02-20")
    apply_pnl(state, realized_delta_usd=-55, unrealized_pnl_usd=-5)
    persist_state(p, state)

    same_day = load_state(p, starting_equity_usd=500, day="2026-02-20")
    assert same_day.realized_pnl_usd == -55
    assert same_day.unrealized_pnl_usd == -5

    next_day = load_state(p, starting_equity_usd=500, day="2026-02-21")
    assert next_day.realized_pnl_usd == 0
    assert next_day.unrealized_pnl_usd == 0
