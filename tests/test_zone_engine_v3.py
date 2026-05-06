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
    zone_candidates_from_reaction,
    zone_candidates_from_structure,
)
from liquidsniper.core.zone_primitives import ROLE_SEMANTICS_CONTRACT, derive_role_semantics, local_atr, side_aware_interaction
from liquidsniper.core.zone_selectors import _apply_daily_current_regime_coverage


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
        "candidate_family": "reaction",
        "source_family": "reaction_family",
    }


def test_local_atr_matches_simple_average_true_range_window():
    candles = [
        {"high": 10.0, "low": 8.0, "close": 9.0},
        {"high": 11.0, "low": 9.0, "close": 10.0},
        {"high": 13.0, "low": 10.0, "close": 12.0},
        {"high": 14.0, "low": 11.0, "close": 13.0},
    ]
    assert round(local_atr(candles, period=3), 6) == round((2.0 + 3.0 + 3.0) / 3.0, 6)


def test_derive_role_semantics_separates_origin_from_price_relative_role():
    resistance = _zone("r1", 110.0, kind="resistance")
    support = _zone("s1", 100.0, kind="support")

    flipped = derive_role_semantics(zone=resistance, price=112.0)
    containing = derive_role_semantics(zone=support, price=100.0)

    assert flipped["origin_kind"] == "resistance"
    assert flipped["relative_position"] == "above"
    assert flipped["current_role"] == "support"
    assert containing["current_role"] == "containing"
    assert flipped["role_semantics_contract"] == ROLE_SEMANTICS_CONTRACT


def test_side_aware_interaction_flags_alignment_by_side_and_position():
    support = _zone("s1", 100.0, kind="support")
    resistance = _zone("r1", 110.0, kind="resistance")

    buy_hit = side_aware_interaction(zone=support, price=103.0, side="buy", atr=4.0)
    sell_hit = side_aware_interaction(zone=resistance, price=107.0, side="sell", atr=4.0)
    wrong_way = side_aware_interaction(zone=support, price=103.0, side="sell", atr=4.0)

    assert buy_hit["is_aligned"] is True
    assert buy_hit["current_role"] == "support"
    assert buy_hit["relative_position"] == "above"
    assert buy_hit["lifecycle_state"] == "virgin"
    assert sell_hit["is_aligned"] is True
    assert sell_hit["current_role"] == "resistance"
    assert sell_hit["relative_position"] == "below"
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
        [{**_zone("z1", 100.0), "candidate_family": "reaction", "candidate_provenance": {"family": "reaction", "evidence": "reaction-fixture"}, "source_version": "reaction_v1", "engine_contract": "reaction_contract"}],
        [{**_zone("z2", 100.2, strength=88.0), "candidate_family": "structure", "source_family": "structure_anchor_v3a", "candidate_provenance": {"family": "structure", "evidence": "structure-fixture"}, "structure_provenance": {"family": "structure", "evidence": "structure-fixture"}, "source_version": "structure_v1", "engine_contract": "structure_contract"}],
        [{**_zone("z3", 99.9, strength=84.0), "candidate_family": "base", "source_family": "base_shelf_v3b", "candidate_provenance": {"family": "base", "evidence": "base-fixture"}, "source_version": "base_v1", "engine_contract": "base_contract"}],
    )
    assert len(merged) == 1
    assert merged[0]["strength_score"] == 88.0
    assert merged[0]["candidate_sources"] == ["base", "reaction", "structure"]
    assert merged[0]["candidate_families"] == ["base", "reaction", "structure"]
    assert merged[0]["family_stamp_contract"] == "zone_engine_v3_family_stamp_v1"
    assert merged[0]["family_provenance"]["reaction"]["evidence"] == "reaction-fixture"
    assert merged[0]["family_provenance"]["structure"]["evidence"] == "structure-fixture"
    assert merged[0]["family_provenance"]["base"]["evidence"] == "base-fixture"
    assert merged[0]["source_versions"] == {"base": "base_v1", "reaction": "reaction_v1", "structure": "structure_v1"}
    assert merged[0]["generator_contracts"] == {"base": "base_contract", "reaction": "reaction_contract", "structure": "structure_contract"}
    assert merged[0]["provenance_summary"]["merge_family_count"] == 3
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


def test_select_daily_majors_adds_overlap_density_core_when_family_bounds_overlap():
    overlapped = {
        **_zone("doverlap", 100.0, tf="1D", strength=85.0, retest="reject"),
        "zone_low": 94.0,
        "zone_high": 106.0,
        "zone_mid": 100.0,
        "arbitration_diagnostics": {
            "candidates": [
                {"zone_id": "c1", "low": 96.0, "high": 104.0, "base_score": 88.0},
                {"zone_id": "c2", "low": 98.0, "high": 102.0, "base_score": 84.0},
            ]
        },
    }
    selected = select_daily_majors(
        [overlapped],
        min_strength=70.0,
        min_zone_separation_bps=120.0,
        max_zones=1,
        strict_retest_quality=True,
    )
    assert selected[0]["core_low"] == 98.0
    assert selected[0]["core_high"] == 102.0
    assert selected[0]["core_mid"] == 100.0
    assert selected[0]["core_definition"] == "overlap_density_core"



def test_select_daily_majors_expands_too_tight_overlap_core_to_daily_width_floor():
    seam = {
        **_zone("dseam", 85721.475, tf="1D", strength=90.0, selection=95.0, retest="reject"),
        "zone_low": 83063.9,
        "zone_high": 88651.2,
        "zone_mid": 85721.475,
        "zone_width_atr": 2.063077,
        "arbitration_diagnostics": {
            "candidates": [
                {"zone_id": "base", "low": 83063.9, "high": 85600.0, "base_score": 100.0},
                {"zone_id": "reaction", "low": 85570.8, "high": 88651.2, "base_score": 66.4993},
            ]
        },
    }
    selected = select_daily_majors(
        [seam],
        min_strength=70.0,
        min_zone_separation_bps=120.0,
        max_zones=1,
        strict_retest_quality=True,
    )
    core_width = selected[0]["core_high"] - selected[0]["core_low"]
    # Raw overlap is only 29.2 wide; Daily actionable cores should not collapse
    # into a one-tick seam. The floor uses max(0.20% price, 0.20*ATR).
    assert core_width >= 541.642
    assert selected[0]["core_low"] < 85570.8
    assert selected[0]["core_high"] > 85600.0
    assert selected[0]["core_definition"] == "overlap_density_core_width_floored"


def test_select_daily_majors_falls_back_to_midpoint_narrowed_core_when_no_overlap_exists():
    broad = {
        **_zone("dbroad", 100.0, tf="1D", strength=85.0, retest="reject"),
        "zone_low": 90.0,
        "zone_high": 110.0,
        "zone_mid": 100.0,
        "arbitration_diagnostics": {
            "candidates": [
                {"zone_id": "c1", "low": 90.0, "high": 110.0, "base_score": 88.0},
            ]
        },
    }
    selected = select_daily_majors(
        [broad],
        min_strength=70.0,
        min_zone_separation_bps=120.0,
        max_zones=1,
        strict_retest_quality=True,
    )
    assert selected[0]["core_low"] == 94.5
    assert selected[0]["core_high"] == 105.5
    assert selected[0]["core_mid"] == 100.0
    assert selected[0]["core_definition"] == "midpoint_narrowed_core"


def test_select_daily_majors_consolidates_nested_macro_pocket_representatives():
    lower = {
        **_zone("d-low", 210.0, tf="1D", strength=84.0, selection=84.0, retest="reject"),
        "zone_low": 170.0,
        "zone_high": 230.0,
        "zone_mid": 210.0,
        "zone_width_bps": 900.0,
        "candidate_sources": ["base", "structure"],
        "merge_family_count": 2,
        "structure_provenance": {"family": "structure"},
    }
    upper = {
        **_zone("d-upper", 270.0, tf="1D", strength=91.0, selection=91.0, retest="reject"),
        "zone_low": 236.0,
        "zone_high": 304.0,
        "zone_mid": 270.0,
        "zone_width_bps": 1100.0,
        "candidate_sources": ["base", "reaction", "structure"],
        "merge_family_count": 3,
        "structure_provenance": {"family": "structure"},
    }
    selected = select_daily_majors(
        [lower, upper],
        min_strength=70.0,
        min_zone_separation_bps=120.0,
        max_zones=4,
        strict_retest_quality=True,
        reference_price=700.0,
    )
    assert [z["zone_id"] for z in selected] == ["d-upper"]
    assert selected[0]["daily_pocket_member_ids"] == ["d-low", "d-upper"]
    assert selected[0]["daily_pocket_demoted_ids"] == ["d-low"]


def test_select_daily_majors_rejects_low_touch_daily_major_even_with_strong_structure_confluence():
    one_touch_structure = {
        **_zone("d-one-touch", 650.0, tf="1D", strength=100.0, selection=140.0, retest="reject"),
        "zone_low": 630.0,
        "zone_high": 690.0,
        "zone_mid": 650.0,
        "meaningful_touch_count": 1,
        "candidate_sources": ["structure", "reaction"],
        "merge_family_count": 2,
        "structure_provenance": {"family": "structure", "seed_kind": "flip_anchor"},
    }
    three_touch_base = {
        **_zone("d-three-touch", 850.0, tf="1D", strength=84.0, selection=84.0, retest="reject"),
        "zone_low": 830.0,
        "zone_high": 880.0,
        "zone_mid": 855.0,
        "meaningful_touch_count": 3,
        "candidate_sources": ["base", "reaction"],
        "merge_family_count": 2,
    }
    selected = select_daily_majors(
        [one_touch_structure, three_touch_base],
        min_strength=70.0,
        min_zone_separation_bps=120.0,
        max_zones=4,
        strict_retest_quality=True,
        reference_price=680.0,
    )
    ids = [z["zone_id"] for z in selected]
    assert "d-one-touch" not in ids
    assert "d-three-touch" in ids
    assert all(int(z.get("meaningful_touch_count") or 0) >= 3 for z in selected)


def test_select_daily_majors_adds_current_regime_coverage_anchor_when_large_gap_exists():
    distant_lower = {
        **_zone("d-lower", 210.0, tf="1D", strength=88.0, selection=88.0, retest="reject"),
        "zone_low": 180.0,
        "zone_high": 240.0,
        "zone_mid": 210.0,
        "zone_width_bps": 850.0,
        "candidate_sources": ["structure", "reaction"],
        "merge_family_count": 2,
        "structure_provenance": {"family": "structure"},
    }
    lower_active = {
        **_zone("d-active-low", 520.0, tf="1D", strength=92.0, selection=92.0, retest="reject"),
        "zone_low": 500.0,
        "zone_high": 540.0,
        "zone_mid": 520.0,
        "zone_width_bps": 700.0,
        "candidate_sources": ["base", "reaction"],
        "merge_family_count": 2,
    }
    containing = {
        **_zone("d-current", 700.0, tf="1D", strength=86.0, selection=86.0, retest="reject"),
        "zone_low": 660.0,
        "zone_high": 730.0,
        "zone_mid": 700.0,
        "zone_width_bps": 950.0,
        "candidate_sources": ["structure", "reaction"],
        "merge_family_count": 2,
        "structure_provenance": {"family": "structure"},
    }
    upper_active = {
        **_zone("d-upper", 860.0, tf="1D", strength=89.0, selection=89.0, retest="reject"),
        "zone_low": 840.0,
        "zone_high": 890.0,
        "zone_mid": 860.0,
        "zone_width_bps": 720.0,
        "candidate_sources": ["base", "reaction"],
        "merge_family_count": 2,
    }
    far_upper = {
        **_zone("d-far-upper", 1100.0, tf="1D", strength=79.0, selection=79.0, retest="accept"),
        "zone_low": 1080.0,
        "zone_high": 1120.0,
        "zone_mid": 1100.0,
        "zone_width_bps": 680.0,
        "candidate_sources": ["base"],
        "merge_family_count": 1,
    }
    selected = select_daily_majors(
        [distant_lower, lower_active, containing, upper_active, far_upper],
        min_strength=70.0,
        min_zone_separation_bps=120.0,
        max_zones=4,
        strict_retest_quality=True,
        reference_price=700.0,
    )
    ids = [z["zone_id"] for z in selected]
    assert "d-current" in ids
    assert "d-far-upper" not in ids


def test_apply_daily_current_regime_coverage_adds_intermediate_upside_anchor_when_containing_gap_is_too_large():
    selected = [
        {
            **_zone("below", 100.0, tf="1D", strength=88.0, selection=88.0, retest="reject"),
            "zone_low": 90.0,
            "zone_high": 110.0,
            "zone_mid": 100.0,
            "selector_rank": 3,
        },
        {
            **_zone("containing", 180.0, tf="1D", strength=90.0, selection=90.0, retest="reject"),
            "zone_low": 170.0,
            "zone_high": 210.0,
            "zone_mid": 190.0,
            "selector_rank": 1,
        },
        {
            **_zone("far-above-1", 400.0, tf="1D", strength=86.0, selection=86.0, retest="reject"),
            "zone_low": 390.0,
            "zone_high": 410.0,
            "zone_mid": 400.0,
            "selector_rank": 2,
        },
        {
            **_zone("far-above-2", 500.0, tf="1D", strength=82.0, selection=82.0, retest="reject"),
            "zone_low": 490.0,
            "zone_high": 510.0,
            "zone_mid": 500.0,
            "selector_rank": 4,
        },
    ]
    candidates = [
        *selected,
        {
            **_zone("mid-upside", 288.0, tf="1D", strength=78.0, selection=78.0, retest="reject"),
            "zone_low": 271.0,
            "zone_high": 299.0,
            "zone_mid": 288.0,
            "daily_major_provenance_weight": 1.04,
            "daily_major_diagnostics": {"has_structure": True},
            "structure_provenance": {"family": "structure"},
        },
        {
            **_zone("higher-mid-upside", 311.0, tf="1D", strength=84.0, selection=84.0, retest="reject"),
            "zone_low": 303.0,
            "zone_high": 319.0,
            "zone_mid": 311.0,
            "daily_major_provenance_weight": 1.0,
            "daily_major_diagnostics": {"has_structure": False},
        },
    ]

    out = _apply_daily_current_regime_coverage(
        selected,
        candidates=candidates,
        reference_price=200.0,
        max_zones=5,
    )

    ids = [z["zone_id"] for z in out]
    assert "mid-upside" in ids
    chosen = next(z for z in out if z["zone_id"] == "mid-upside")
    assert chosen["selector_reason"] == "kept: daily intermediate upside coverage anchor"



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
    assert selected[0]["local_cluster_member_ids"] == ["o1", "o2"]
    assert selected[0]["local_cluster_member_count"] == 2
    assert selected[0]["local_cluster_role"] == "support"
    assert selected[0]["local_cluster_demoted_ids"] == ["o2"]
    assert selected[0]["selector_surface"] == "operational_4h"
    assert selected[0]["selector_status"] == "kept"
    assert selected[0]["selector_rank"] == 1



def test_select_operational_zones_keeps_opposite_side_levels_separate_inside_local_neighborhood():
    support = _zone("sup", 100.0, tf="4H", kind="support", strength=82.0)
    resistance = {
        **_zone("res", 100.4, tf="4H", kind="resistance", strength=88.0),
        "current_role": "resistance",
        "origin_kind": "resistance",
    }
    selected = select_operational_zones(
        [support, resistance],
        min_strength=70.0,
        min_zone_separation_bps=80.0,
        max_zones=4,
    )
    assert [z["zone_id"] for z in selected] == ["sup", "res"]
    assert [z["local_cluster_role"] for z in selected] == ["support", "resistance"]



def test_select_operational_zones_prefers_best_evidence_within_local_same_side_cluster():
    zones = [
        _zone("nearer", 100.0, tf="4H", kind="support", strength=80.0, selection=80.0),
        _zone("better", 100.9, tf="4H", kind="support", strength=92.0, selection=92.0),
    ]
    selected = select_operational_zones(
        zones,
        min_strength=70.0,
        min_zone_separation_bps=80.0,
        max_zones=4,
    )
    assert [z["zone_id"] for z in selected] == ["better"]
    assert selected[0]["local_cluster_member_ids"] == ["nearer", "better"]


def test_select_operational_zones_collapses_overlapping_same_side_intervals_even_when_mid_gap_is_wide():
    left = {
        **_zone("wide-left", 101.0, tf="4H", kind="resistance", strength=87.0, selection=87.0),
        "zone_low": 99.0,
        "zone_high": 103.0,
        "zone_mid": 101.0,
        "zone_width_bps": 400.0,
        "current_role": "resistance",
        "origin_kind": "resistance",
    }
    right = {
        **_zone("wide-right", 104.5, tf="4H", kind="resistance", strength=84.0, selection=84.0),
        "zone_low": 102.5,
        "zone_high": 106.5,
        "zone_mid": 104.5,
        "zone_width_bps": 382.0,
        "current_role": "resistance",
        "origin_kind": "resistance",
    }
    selected = select_operational_zones(
        [left, right],
        min_strength=70.0,
        min_zone_separation_bps=80.0,
        max_zones=4,
    )
    assert [z["zone_id"] for z in selected] == ["wide-left"]
    assert selected[0]["local_cluster_member_ids"] == ["wide-left", "wide-right"]
    assert selected[0]["local_cluster_demoted_ids"] == ["wide-right"]
    assert selected[0]["local_cluster_competition_basis"] == "interval_overlap_or_edge_gap_with_provenance_bias"


def test_select_operational_zones_prefers_corroborated_provenance_within_local_same_side_cluster():
    base_only = {
        **_zone("base-only", 100.0, tf="4H", kind="support", strength=91.0, selection=91.0),
        "candidate_family": "base",
        "candidate_sources": ["base"],
        "candidate_families": ["base"],
        "source_family": "base",
        "merge_family_count": 1,
    }
    corroborated = {
        **_zone("corroborated", 100.9, tf="4H", kind="support", strength=89.0, selection=89.0),
        "candidate_family": "structure",
        "candidate_sources": ["structure", "reaction"],
        "candidate_families": ["structure", "reaction"],
        "source_family": "structure",
        "merge_family_count": 2,
        "structure_provenance": {"family": "structure"},
    }
    selected = select_operational_zones(
        [base_only, corroborated],
        min_strength=70.0,
        min_zone_separation_bps=80.0,
        max_zones=4,
    )
    assert [z["zone_id"] for z in selected] == ["corroborated"]
    assert selected[0]["local_cluster_demoted_ids"] == ["base-only"]
    assert selected[0]["local_cluster_representative_diagnostics"]["has_structure"] is True
    assert selected[0]["local_cluster_representative_diagnostics"]["merge_family_count"] == 2


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
    assert payload["nearest_support"]["candidate_families"] == ["reaction"]
    assert payload["nearest_support"]["provenance_summary"]["primary_family"] == "reaction"
    assert payload["nearest_support"]["origin_kind"] == "support"
    assert payload["nearest_support"]["current_role"] == "support"
    assert payload["nearest_support"]["relative_position"] == "above"
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
        {"open": 99.6, "high": 100.4, "low": 99.2, "close": 99.9},
        {"open": 99.9, "high": 100.6, "low": 99.4, "close": 100.1},
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
    assert best["candidate_provenance"]["family"] == "base"
    assert best["candidate_provenance"]["compression"]["qualifies"] is True
    assert best["candidate_provenance"]["overlap"]["qualifies"] is True
    assert best["candidate_provenance"]["edge_touches"]["qualifies"] is True
    assert best["candidate_provenance"]["breakout"]["direction"] == "up"
    assert best["family_provenance"]["base"]["breakout"]["qualifies"] is True


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
    assert best["candidate_families"] == ["structure"]
    assert best["family_provenance"]["structure"]["seed_kind"] == "bos_anchor"
    assert best["provenance_summary"]["primary_family"] == "structure"
    assert best["candidate_provenance"]["seed_kind"] == "bos_anchor"
    assert best["candidate_provenance"]["anchor_index"] == 4
    assert best["shadow_diagnostics"]["generator_contract"] == V3A_CONTRACT
    assert best["shadow_diagnostics"]["seed_policy_version"] == STRUCTURE_SEED_POLICY_VERSION
    assert best["shadow_diagnostics"]["break_distance_atr"] > 0.0


def test_zone_candidates_from_reaction_emits_touch_and_retest_provenance():
    mocked_zone = {
        **_zone("rx1", 100.0, tf="4H", kind="support"),
        "pivot_count": 4,
        "touch_count": 5,
        "meaningful_touch_count": 3,
        "body_overlap_rate": 0.67,
        "wick_only_rate": 0.33,
        "directional_close_rate": 0.67,
        "deviation_retest": 0,
        "first_retest_pending": 0,
        "first_retest_ts": "2026-03-14T00:00:00Z",
        "first_retest_result": "reject",
    }
    mocked_touches = [
        {
            "zone_id": "rx1",
            "candle_ts": "2026-03-13T00:00:00Z",
            "reaction_type": "reject_up",
            "reaction_magnitude_atr": 0.9,
            "carry_magnitude_atr": 0.6,
            "adverse_magnitude_atr": 0.1,
            "is_meaningful": 1,
        },
        {
            "zone_id": "rx1",
            "candle_ts": "2026-03-13T04:00:00Z",
            "reaction_type": "reject_up",
            "reaction_magnitude_atr": 0.7,
            "carry_magnitude_atr": 0.5,
            "adverse_magnitude_atr": 0.2,
            "is_meaningful": 1,
        },
        {
            "zone_id": "rx1",
            "candle_ts": "2026-03-13T08:00:00Z",
            "reaction_type": "reject_down",
            "reaction_magnitude_atr": 0.4,
            "carry_magnitude_atr": 0.3,
            "adverse_magnitude_atr": 0.2,
            "is_meaningful": 0,
        },
    ]
    with patch("liquidsniper.core.zone_engine_v3.build_zones_for_tf", return_value=([mocked_zone], mocked_touches)):
        zones = zone_candidates_from_reaction("BTCUSDT", "4H", [{"high": 101.0, "low": 99.0, "close": 100.0}] * 20)
    assert zones
    best = zones[0]
    assert best["candidate_family"] == "reaction"
    assert best["family_provenance"]["reaction"]["family"] == "reaction"
    assert best["family_provenance"]["reaction"]["cluster"]["meaningful_touch_count"] == 3
    assert best["family_provenance"]["reaction"]["touch_behavior"]["reaction_type"] == "reject_up"
    assert best["family_provenance"]["reaction"]["reaction"]["max_reaction_atr"] == 0.9
    assert best["family_provenance"]["reaction"]["retest"]["first_retest_result"] == "reject"
    assert best["family_provenance"]["reaction"]["timestamps"]["touches"] == [
        "2026-03-13T00:00:00Z",
        "2026-03-13T04:00:00Z",
    ]



def test_score_zone_adds_core_bounds_for_daily_operator_view():
    from liquidsniper.core.zone_engine_v3 import score_zone
    zone = {
        "zone_id": "BTCUSDT:1D:test",
        "symbol": "BTCUSDT",
        "tf": "1D",
        "status": "confirmed",
        "zone_low": 100.0,
        "zone_high": 140.0,
        "zone_mid": 120.0,
        "strength_score": 80.0,
        "reaction_score": 70.0,
        "reaction_efficiency_score": 65.0,
        "carry_score": 60.0,
        "candidate_sources": ["base", "reaction", "structure"],
        "atr_local": 5.0,
    }
    scored = score_zone(zone, last_price=130.0)
    assert scored["core_low"] >= scored["zone_low"]
    assert scored["core_high"] <= scored["zone_high"]
    assert scored["core_high"] - scored["core_low"] < scored["zone_high"] - scored["zone_low"]
    assert scored["display_bounds_kind"] == "core"


def test_score_zone_keeps_macro_bounds_for_4h_operator_view():
    from liquidsniper.core.zone_engine_v3 import score_zone
    zone = {
        "zone_id": "BTCUSDT:4H:test",
        "symbol": "BTCUSDT",
        "tf": "4H",
        "status": "confirmed",
        "zone_low": 100.0,
        "zone_high": 110.0,
        "zone_mid": 105.0,
        "strength_score": 80.0,
        "reaction_score": 70.0,
        "reaction_efficiency_score": 65.0,
        "carry_score": 60.0,
        "candidate_sources": ["reaction"],
        "atr_local": 3.0,
    }
    scored = score_zone(zone, last_price=106.0)
    assert scored["core_low"] == scored["zone_low"]
    assert scored["core_high"] == scored["zone_high"]
    assert scored["display_bounds_kind"] == "macro"
