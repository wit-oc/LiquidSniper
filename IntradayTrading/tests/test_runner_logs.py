from intraday_revisit.engine.runner import Bar, RunnerConfig, SignalRunner
from intraday_revisit.engine.structure import StructureBias
from intraday_revisit.engine.zones import Zone, ZoneKind


def test_runner_emits_per_bar_logs():
    bars = [
        Bar(index=0, open=100, high=102, low=99, close=101),
        Bar(index=1, open=101, high=103, low=100, close=102),
    ]
    bias = {0: StructureBias.BULLISH, 1: StructureBias.BULLISH}
    zones = [Zone(id="s1", kind=ZoneKind.SUPPORT, low=99.5, high=101.0, created_at=0)]

    runner = SignalRunner(
        RunnerConfig(
            max_zone_width_frac=0.03,
            require_retest_sequence=False,
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
    )
    events, logs = runner.run_with_logs(bars, bias, zones, symbol="BTC", tf="1h")

    assert len(logs) == len(bars)
    assert logs[0]["symbol"] == "BTC"
    assert logs[0]["tf"] == "1h"
    assert "action" in logs[0]
    assert "regime_state" in logs[0]
    assert "fsm_transition" in logs[0]
    assert len(events) >= 1
