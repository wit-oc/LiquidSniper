from __future__ import annotations

from liquidsniper.core.zone_engine_v3 import (
    V3B_CONTRACT,
    merge_candidate_zones,
    nearest_four_levels,
    score_zone,
    select_daily_majors,
    select_operational_zones,
    zone_candidates_from_base,
)
from liquidsniper.core.zone_primitives import local_atr, side_aware_interaction


def _zone(zone_id: str, mid: float, *, tf: str = "1D", kind: str = "support", status: str = "confirmed", strength: float = 80.0, selection: float | None = None, retest: str = "reject") -> dict:
    return {
        "zone_id": zone_id,
        "symbol": "BTCUSDT",
        "tf": tf,
        "status": status,
        "zone_low": mid - 1.0,
        "zone_high": mid + 1.0,
        "zone_mid": mid,
        "zone_kind": kind,
        "strength_score": strength,
        "selection_score": selection if selection is not None else strength,
        "reaction_score": 70.0,
        "reaction_efficiency_score": 75.0,
        "carry_score": 65.0,
        "body_respect_score": 68.0,
        "meaningful_touch_count": 5,
        "zone_width_bps": 45.0,
        "close_inside_rate": 0.05,
        "counter_close_rate": 0.02,
        "first_retest_result": retest,
        "atr_local": 4.0,
    }


def test_local_atr_matches_simple_average_true_range_window():
    candles = [
        {"high": 10.0, "low": 8.0, "close": 9.0},
        {"high": 11.0, "low": 9.0, "close": 10.0},
        {"high": 13.0, "low": 10.0, "close": 12.0},
        {"high": 14.0, "low": 11.0, "close": 13.0},
    ]
    assert round(local_atr(candles, period=3), 6) == round((2.0 + 3.0 + 3.0) / 3.0, 6)


def test_side_aware_interaction_flags_alignment_by_side_and_position():
    support = _zone("s1", 100.0, kind="support")
    resistance = _zone("r1", 110.0, kind="resistance")

    buy_hit = side_aware_interaction(zone=support, price=103.0, side="buy", atr=4.0)
    sell_hit = side_aware_interaction(zone=resistance, price=107.0, side="sell", atr=4.0)
    wrong_way = side_aware_interaction(zone=support, price=103.0, side="sell", atr=4.0)

    assert buy_hit["is_aligned"] is True
    assert buy_hit["lifecycle_state"] == "virgin"
    assert sell_hit["is_aligned"] is True
    assert sell_hit["lifecycle_state"] == "virgin"
    assert wrong_way["is_aligned"] is False
    assert wrong_way["lifecycle_state"] == "counter_side"


def test_side_aware_interaction_marks_deep_test_and_broken():
    support = _zone("s1", 100.0, kind="support")
    deep = side_aware_interaction(zone=support, price=100.0, side="buy", atr=2.0)
    broken = side_aware_interaction(zone=support, price=97.5, side="buy", atr=2.0)
    assert deep["lifecycle_state"] == "deep_test"
    assert broken["lifecycle_state"] == "broken"


def test_merge_candidate_zones_combines_duplicate_zone_ids_and_tracks_sources():
    merged = merge_candidate_zones(
        [{**_zone("z1", 100.0), "candidate_family": "reaction"}],
        [{**_zone("z1", 100.0, strength=88.0), "candidate_family": "structure"}],
    )
    assert len(merged) == 1
    assert merged[0]["strength_score"] == 88.0
    assert merged[0]["candidate_sources"] == ["reaction", "structure"]


def test_select_daily_majors_uses_selector_layer_contract():
    zones = [
        _zone("d1", 100.0, tf="1D", strength=85.0, retest="reject"),
        _zone("d2", 101.0, tf="1D", strength=84.0, retest="deviation"),
        _zone("d3", 130.0, tf="1D", strength=79.0, retest="accept"),
        _zone("d4", 160.0, tf="1D", strength=82.0, retest="reject"),
    ]
    selected = select_daily_majors(
        zones,
        min_strength=70.0,
        min_zone_separation_bps=120.0,
        max_zones=2,
        strict_retest_quality=True,
    )
    assert len(selected) == 2
    assert all(z["status"] == "confirmed" for z in selected)
    assert all("selection_score" in z for z in selected)


def test_select_operational_zones_collapses_nearby_levels():
    zones = [
        _zone("o1", 100.0, tf="4H", strength=82.0),
        _zone("o2", 100.5, tf="4H", strength=81.0),
        _zone("o3", 115.0, tf="4H", strength=78.0),
    ]
    selected = select_operational_zones(
        zones,
        min_strength=70.0,
        min_zone_separation_bps=80.0,
        max_zones=4,
    )
    assert [z["zone_id"] for z in selected] == ["o1", "o3"]


def test_nearest_four_levels_adds_side_aware_payloads():
    zones = [
        _zone("s1", 98.0, tf="1D", kind="support"),
        _zone("s2", 92.0, tf="1D", kind="support"),
        _zone("r1", 105.0, tf="1D", kind="resistance"),
        _zone("r2", 112.0, tf="1D", kind="resistance"),
    ]
    payload = nearest_four_levels(profile_id="I", entry=100.0, zones=zones)
    assert payload["contract"] == "nearest_four_levels_v3a"
    assert payload["nearest_support"]["zone_id"] == "s1"
    assert payload["nearest_resistance"]["zone_id"] == "r1"
    assert payload["buy_interaction"]["is_aligned"] is True
    assert payload["sell_interaction"]["is_aligned"] is True


def test_score_zone_uses_atr_and_lifecycle_in_selection_score():
    virgin = score_zone(_zone("sc1", 100.0), last_price=103.5, atr=4.0)
    broken = score_zone(_zone("sc2", 100.0), last_price=97.0, atr=4.0)
    assert virgin["interaction_buy"]["lifecycle_state"] == "virgin"
    assert broken["interaction_buy"]["lifecycle_state"] == "broken"
    assert virgin["selection_score"] > broken["selection_score"]
    assert virgin["zone_width_atr"] > 0


def test_zone_candidates_from_base_emits_simple_breakout_shelf_candidates():
    candles = [
        {"open": 100.0, "high": 101.0, "low": 99.5, "close": 100.4},
        {"open": 100.4, "high": 101.2, "low": 99.8, "close": 100.6},
        {"open": 100.6, "high": 101.1, "low": 99.9, "close": 100.5},
        {"open": 100.5, "high": 101.0, "low": 99.7, "close": 100.3},
        {"open": 100.3, "high": 101.0, "low": 99.8, "close": 100.4},
        {"open": 100.4, "high": 100.9, "low": 99.9, "close": 100.2},
        {"open": 100.2, "high": 100.8, "low": 99.8, "close": 100.1},
        {"open": 100.1, "high": 100.7, "low": 99.9, "close": 100.3},
        {"open": 100.3, "high": 103.4, "low": 100.1, "close": 103.0},
        {"open": 103.0, "high": 104.0, "low": 102.7, "close": 103.7},
        {"open": 103.7, "high": 104.4, "low": 103.2, "close": 104.0},
        {"open": 104.0, "high": 104.6, "low": 103.7, "close": 104.3},
    ]
    zones = zone_candidates_from_base("BTCUSDT", "4H", candles)
    assert zones
    best = zones[0]
    assert best["candidate_family"] == "base"
    assert best["engine_contract"] == V3B_CONTRACT
    assert best["zone_kind"] == "support"
    assert best["breakout_atr"] >= 0.85
