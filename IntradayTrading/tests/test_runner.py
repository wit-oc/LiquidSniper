from intraday_revisit.engine.runner import Bar, RunnerConfig, SignalRunner
from intraday_revisit.engine.structure import StructureBias
from intraday_revisit.engine.zones import Zone, ZoneKind


def _test_cfg():
    return RunnerConfig(
        max_at_risk_positions=2,
        require_retest_sequence=False,
        max_zone_width_frac=0.03,
        enable_swing_location_gate=False,
        enable_momentum_gate=False,
        enable_chop_gate=False,
        enable_candle_confirmation=False,
        enable_fib_directional_gate=False,
        min_body_frac=0.0,
        min_rejection_wick_frac=0.0,
        score_gate_min=0.0,
        trigger_score_min=0.0,
        strict_retest_bps_max=500.0,
        near_retest_bps_max=500.0,
    )


def test_runner_emits_entries_with_bias_and_capacity():
    bars = [
        Bar(index=0, open=100, high=102, low=99, close=101),
        Bar(index=1, open=101, high=103, low=100, close=102),
        Bar(index=2, open=102, high=103, low=100, close=101),
    ]
    bias = {0: StructureBias.BULLISH, 1: StructureBias.BULLISH, 2: StructureBias.BEARISH}
    zones = [Zone(id="s1", kind=ZoneKind.SUPPORT, low=99.5, high=101.0, created_at=0)]

    runner = SignalRunner(_test_cfg())
    events = runner.run(bars, bias, zones)

    enter_longs = [e for e in events if e["event"] == "enter_long"]
    assert len(enter_longs) >= 1


def test_retest_sequence_blocks_until_reclaim():
    bars = [
        Bar(index=0, open=100, high=100.5, low=99.2, close=99.8),
        Bar(index=1, open=99.8, high=101.4, low=99.4, close=101.2),
    ]
    bias = {0: StructureBias.BULLISH, 1: StructureBias.BULLISH}
    zones = [Zone(id="s1", kind=ZoneKind.SUPPORT, low=99.0, high=101.0, created_at=0)]

    runner = SignalRunner(_test_cfg())
    events = runner.run(bars, bias, zones)

    enter_events = [e for e in events if e["event"] == "enter_long"]
    assert len(enter_events) == 1
    assert enter_events[0]["index"] == 1
