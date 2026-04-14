from intraday_revisit.engine.risk import RiskConfig, RiskEngine, at_risk_count


def test_position_size_basic():
    engine = RiskEngine(RiskConfig(risk_per_trade_pct=1.0))
    size = engine.position_size(equity=10_000, entry=100.0, stop=99.0)
    assert round(size, 6) == 100.0


def test_breakers_trip_at_thresholds():
    engine = RiskEngine(RiskConfig(daily_loss_limit_pct=6.0, weekly_dd_limit_pct=20.0))

    state = engine.update_breakers(day_pnl_pct=-6.0, week_pnl_pct=-10.0)
    assert state.daily_locked is True
    assert state.weekly_locked is False

    state = engine.update_breakers(day_pnl_pct=-1.0, week_pnl_pct=-20.0)
    assert state.daily_locked is False
    assert state.weekly_locked is True


def test_at_risk_count_excludes_be_positions():
    positions = [
        {"id": 1, "is_at_risk": True},
        {"id": 2, "is_at_risk": False},
        {"id": 3, "is_at_risk": True},
    ]
    assert at_risk_count(positions) == 2
