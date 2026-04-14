from intraday_revisit.engine.risk import BreakerState
from intraday_revisit.engine.signals import (
    SignalContext,
    StructureBias,
    apply_tp1_to_be,
    should_enter_long,
    should_enter_short,
)


def test_should_enter_long_happy_path():
    ctx = SignalContext(
        structure_bias=StructureBias.BULLISH,
        zone_touched=True,
        reclaim_confirmed=True,
        filters_passed=True,
        breaker=BreakerState(daily_locked=False, weekly_locked=False),
        at_risk_count=1,
        max_at_risk=2,
    )
    assert should_enter_long(ctx) is True


def test_should_block_when_breaker_locked():
    ctx = SignalContext(
        structure_bias=StructureBias.BEARISH,
        zone_touched=True,
        reclaim_confirmed=True,
        filters_passed=True,
        breaker=BreakerState(daily_locked=True, weekly_locked=False),
        at_risk_count=0,
        max_at_risk=2,
    )
    assert should_enter_short(ctx) is False


def test_tp1_moves_stop_to_be_and_unflags_at_risk():
    pos = {
        "side": "long",
        "entry": 100.0,
        "stop": 95.0,
        "tp1_hit": True,
        "is_at_risk": True,
    }
    out = apply_tp1_to_be(pos, costs_buffer_frac=0.001)
    assert out["stop"] == 100.1
    assert out["is_at_risk"] is False
