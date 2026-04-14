from intraday_revisit.engine.zones import Zone, ZoneKind
from intraday_revisit.engine.zones_runtime import find_interaction


def test_find_support_interaction_and_reclaim():
    zones = [Zone(id="z1", kind=ZoneKind.SUPPORT, low=100.0, high=101.0, created_at=1)]
    out = find_interaction(zones, close_price=101.2, high_price=101.5, low_price=100.2)
    assert out is not None
    assert out.zone_id == "z1"
    assert out.reclaimed is True


def test_find_resistance_interaction_and_reclaim():
    zones = [Zone(id="z2", kind=ZoneKind.RESISTANCE, low=200.0, high=201.0, created_at=1)]
    out = find_interaction(zones, close_price=199.8, high_price=200.5, low_price=199.5)
    assert out is not None
    assert out.zone_id == "z2"
    assert out.reclaimed is True
