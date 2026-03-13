from __future__ import annotations

from unittest.mock import patch

from liquidsniper.core.zone_engine_v3 import (
    STRUCTURE_SEED_POLICY_VERSION,
    V3A_CONTRACT,
    V3B_CONTRACT,
    V3D_CONTRACT,
    merge_candidate_zones,
    nearest_four_levels,
    score_zone,
    select_daily_majors,
    select_operational_zones,
    zone_candidates_from_base,
    zone_candidates_from_structure,
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


def test_merge_candidate_zones_merges_nearby_cross_family_candidates_and_tracks_arbitration():
    merged = merge_candidate_zones(
        [{**_zone("z1", 100.0), "candidate_family": "reaction"}],
        [{**_zone("z2", 100.2, strength=88.0), "candidate_family": "structure"}],
        [{**_zone("z3", 99.9, strength=84.0), "candidate_family": "base"}],
    )
    assert len(merged) == 1
    assert merged[0]["strength_score"] == 88.0
    assert merged[0]["candidate_sources"] == ["base", "reaction", "structure"]
    assert merged[0]["merge_family_count"] == 3
    assert len(merged[0]["merged_from_zone_ids"]) == 3
    assert merged[0]["family_confluence_bonus"] == 8.0
    arbitration = merged[0]["arbitration_diagnostics"]
    assert arbitration["engine_contract"] == V3D_CONTRACT
    assert arbitration["kept_zone_id"] == "z2"
    assert arbitration["cluster_size"] == 3
    assert arbitration["score_components"]["final_selection_score"] == merged[0]["selection_score"]
    assert arbitration["candidates"][0]["kept"] is True
    assert arbitration["candidates"][1]["kept_reason"] == "clustered_under_stronger_candidate"


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
    assert all("daily_major_provenance_weight" in z for z in selected)



def test_select_daily_majors_prefers_corroborated_structure_participation_over_pure_base_only_when_close():
    pure_base = {
        **_zone("dbase", 100.0, tf="1D", strength=87.0, retest="reject"),
        "candidate_sources": ["base"],
        "merge_family_count": 1,
        "source_family": "base",
    }
    corroborated = {
        **_zone("dcorro", 130.0, tf="1D", strength=84.0, retest="reject"),
        "candidate_sources": ["base", "structure"],
        "merge_family_count": 2,
        "source_family": "structure_anchor_v3a",
        "structure_provenance": {"family": "structure", "seed_kind": "flip_anchor"},
    }
    selected = select_daily_majors(
        [pure_base, corroborated],
        min_strength=70.0,
        min_zone_separation_bps=120.0,
        max_zones=1,
        strict_retest_quality=True,
    )
    assert [z["zone_id"] for z in selected] == ["dcorro"]
    assert selected[0]["daily_major_provenance_weight"] > 1.0
    assert selected[0]["daily_major_diagnostics"]["has_structure"] is True


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


def test_score_zone_uses_atr_lifecycle_and_family_confluence_in_selection_score():
    virgin = score_zone({**_zone("sc1", 100.0), "candidate_sources": ["reaction", "base"]}, last_price=103.5, atr=4.0)
    broken = score_zone(_zone("sc2", 100.0), last_price=97.0, atr=4.0)
    assert virgin["interaction_buy"]["lifecycle_state"] == "virgin"
    assert broken["interaction_buy"]["lifecycle_state"] == "broken"
    assert virgin["selection_score"] > broken["selection_score"]
    assert virgin["zone_width_atr"] > 0
    assert virgin["family_confluence_bonus"] == 3.0


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


def test_zone_candidates_from_structure_emits_native_candidates_with_provenance_and_shadow_diagnostics():
    candles = [
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
        {"open": 100.0, "high": 102.0, "low": 99.5, "close": 101.5},
        {"open": 101.5, "high": 103.0, "low": 100.5, "close": 102.5},
        {"open": 102.5, "high": 104.0, "low": 101.5, "close": 103.5},
        {"open": 103.5, "high": 105.0, "low": 102.5, "close": 104.5},
        {"open": 104.5, "high": 106.0, "low": 103.5, "close": 105.5},
        {"open": 105.5, "high": 107.0, "low": 104.5, "close": 106.5},
        {"open": 106.5, "high": 108.0, "low": 105.5, "close": 107.5},
        {"open": 107.5, "high": 109.0, "low": 106.5, "close": 108.5},
        {"open": 108.5, "high": 110.0, "low": 107.5, "close": 109.5},
        {"open": 109.5, "high": 111.0, "low": 108.5, "close": 110.5},
        {"open": 110.5, "high": 112.0, "low": 109.5, "close": 111.5},
        {"open": 111.5, "high": 113.0, "low": 110.5, "close": 112.5},
        {"open": 112.5, "high": 114.0, "low": 111.5, "close": 113.5},
        {"open": 113.5, "high": 115.0, "low": 112.5, "close": 114.5},
    ]
    mocked_seeds = [
        {
            "seed_kind": "bos_anchor",
            "zone_kind": "support",
            "anchor_index": 4,
            "anchor_price": 102.5,
            "break_index": 7,
            "break_price": 107.5,
            "transition_direction": "bullish",
            "source_event": "bos_confirmed",
            "source_reason": "bullish_continuation",
            "lock_event": "swing_low_locked",
        }
    ]
    with patch("liquidsniper.core.zone_engine_v3.extract_structure_anchor_seeds") as mock_extract:
        from liquidsniper.core.zone_engine_v3 import StructureAnchorSeed

        mock_extract.return_value = [StructureAnchorSeed(**row) for row in mocked_seeds]
        zones = zone_candidates_from_structure("BTCUSDT", "1D", candles)
    assert zones
    best = zones[0]
    assert best["candidate_family"] == "structure"
    assert best["source_family"] == "structure_anchor_v3a"
    assert best["engine_contract"] == V3A_CONTRACT
    assert best["source_version"] == STRUCTURE_SEED_POLICY_VERSION
    assert best["candidate_provenance"]["family"] == "structure"
    assert best["candidate_provenance"]["seed_kind"] == "bos_anchor"
    assert best["candidate_provenance"]["anchor_index"] == 4
    assert best["shadow_diagnostics"]["generator_contract"] == V3A_CONTRACT
    assert best["shadow_diagnostics"]["seed_policy_version"] == STRUCTURE_SEED_POLICY_VERSION
    assert best["shadow_diagnostics"]["break_distance_atr"] > 0.0
