from liquidsniper.ops.sr_bootstrap import (
    _apply_daily_soft_retest_weights,
    _select_daily_local_band_representatives,
)


def _zone(mid: float, *, zone_id: str, selection_score: float, strength: float = 80.0, retest: str = "reject") -> dict:
    return {
        "zone_id": zone_id,
        "zone_mid": mid,
        "zone_low": mid - 100.0,
        "zone_high": mid + 100.0,
        "strength_score": strength,
        "reaction_score": 70.0,
        "reaction_efficiency_score": 60.0,
        "carry_score": 55.0,
        "body_respect_score": 60.0,
        "close_inside_rate": 0.2,
        "counter_close_rate": 0.05,
        "meaningful_touch_count": 10,
        "selection_score": selection_score,
        "first_retest_result": retest,
    }


def test_daily_soft_retest_weights_penalize_accept_without_binary_kill() -> None:
    zones = [
        _zone(100000.0, zone_id="z-reject", selection_score=0.0, strength=90.0, retest="reject"),
        _zone(100500.0, zone_id="z-deviation", selection_score=0.0, strength=90.0, retest="deviation"),
        _zone(101000.0, zone_id="z-accept", selection_score=0.0, strength=90.0, retest="accept"),
    ]

    scored = _apply_daily_soft_retest_weights(zones, strict_mode=True)
    by_id = {z["zone_id"]: z for z in scored}

    assert by_id["z-reject"]["retest_weight"] == 1.0
    assert by_id["z-deviation"]["retest_weight"] > by_id["z-accept"]["retest_weight"]
    assert by_id["z-accept"]["retest_weight"] > 0.8
    assert by_id["z-reject"]["selection_score"] > by_id["z-deviation"]["selection_score"] > by_id["z-accept"]["selection_score"]


def test_daily_local_band_arbitration_keeps_top_representative_per_dense_band() -> None:
    zones = [
        _zone(100000.0, zone_id="dense-a", selection_score=75.0),
        _zone(104000.0, zone_id="dense-b", selection_score=92.0),
        _zone(108000.0, zone_id="dense-c", selection_score=84.0),
        _zone(130000.0, zone_id="far-a", selection_score=88.0),
    ]

    kept = _select_daily_local_band_representatives(
        zones,
        max_zones=8,
        min_zone_separation_bps=250.0,
    )

    kept_ids = {z["zone_id"] for z in kept}
    assert "dense-b" in kept_ids
    assert "far-a" in kept_ids
    assert len(kept_ids.intersection({"dense-a", "dense-b", "dense-c"})) == 1
