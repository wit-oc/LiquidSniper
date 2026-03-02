from intraday_revisit.engine.zones_builder import build_zones_from_candles


def test_build_zones_from_candles_generates_levels():
    highs = [100, 102, 105, 101, 100, 103, 106, 102, 100]
    lows = [99, 99, 100, 98, 97, 99, 100, 98, 97]
    zones = build_zones_from_candles(highs, lows, left=1, right=1)
    assert len(zones) >= 2
    assert any(z.kind.value == "support" for z in zones)
    assert any(z.kind.value == "resistance" for z in zones)
