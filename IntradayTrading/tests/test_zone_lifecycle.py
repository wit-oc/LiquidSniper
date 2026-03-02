from intraday_revisit.engine.zones import Zone, ZoneEngine, ZoneKind, ZoneState


def test_zone_merge_same_kind_overlap():
    engine = ZoneEngine(merge_overlap_ratio=0.1)
    a = Zone(id="z1", kind=ZoneKind.SUPPORT, low=100.0, high=105.0, created_at=1)
    b = Zone(id="z2", kind=ZoneKind.SUPPORT, low=104.0, high=108.0, created_at=2)

    engine.add_zone(a)
    merged = engine.add_zone(b)

    assert merged.id == "z1"
    assert merged.low == 100.0
    assert merged.high == 108.0
    assert len(engine.zones) == 1


def test_zone_invalidate_and_flip():
    engine = ZoneEngine()
    z = Zone(id="z1", kind=ZoneKind.RESISTANCE, low=200.0, high=210.0, created_at=1)
    engine.add_zone(z)

    engine.flip_zone("z1")
    assert engine.zones[0].kind == ZoneKind.SUPPORT
    assert engine.zones[0].state == ZoneState.FLIPPED

    engine.invalidate_zone("z1")
    assert engine.zones[0].state == ZoneState.INVALIDATED
