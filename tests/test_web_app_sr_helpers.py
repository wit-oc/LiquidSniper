from __future__ import annotations

from liquidsniper.web.app import (
    _format_anchor_summary,
    _format_arbitration_summary,
    _format_zone_badges,
    _format_zone_summary,
    _group_zones_by_relative_position,
    _surface_group_label,
)


def test_format_zone_helpers_make_operator_readable_strings() -> None:
    zone = {
        "zone_id": "z1",
        "tf": "4H",
        "kind": "support",
        "origin_kind": "resistance",
        "current_role": "support",
        "relative_position": "above",
        "distance_bps": 42.5,
        "selection_score": 87.5,
        "meaningful_touch_count": 3,
        "first_retest_status": "reject",
        "source_family": "base_shelf_v3b",
        "candidate_families": ["base", "reaction"],
        "bounds": {"low": 98.0, "mid": 99.0, "high": 100.0},
        "price_anchor": {"kind": "merged_zone_mid", "zone_mid": 99.0},
        "arbitration": {
            "kept_zone_id": "z1",
            "cluster_size": 2,
            "families": ["base", "reaction"],
            "score_components": {
                "winner_base_score": 83.5,
                "family_confluence_bonus": 4.0,
                "final_selection_score": 87.5,
            },
        },
    }

    badges = _format_zone_badges(zone)
    summary = _format_zone_summary(zone)
    arbitration = _format_arbitration_summary(zone)

    assert "[SUPPORT]" in badges
    assert "[4H]" in badges
    assert "[SRC:base_shelf_v3b]" in badges
    assert "[FAM:base]" in badges
    assert "merged_zone_mid @ 99.0000" == _format_anchor_summary(zone)
    assert "role support / pos above / origin resistance" in summary
    assert "dist 42.5bps" in summary
    assert "sel 87.5" in summary
    assert "retest reject" in summary
    assert "anchor merged_zone_mid @ 99.0000" in summary
    assert "cluster=2" in arbitration
    assert "base=83.5 + bonus=4.0 => final=87.5" in arbitration


def test_group_zones_by_relative_position_orders_review_surface() -> None:
    zones = [
        {"zone_id": "res", "relative_position": "below"},
        {"zone_id": "cont", "relative_position": "inside"},
        {"zone_id": "sup1", "relative_position": "above"},
        {"zone_id": "sup2", "relative_position": "above"},
    ]

    grouped = _group_zones_by_relative_position(zones)

    assert [key for key, _bucket in grouped] == ["above", "inside", "below"]
    assert [zone["zone_id"] for zone in grouped[0][1]] == ["sup1", "sup2"]
    assert _surface_group_label("above") == "Below price / support"
    assert _surface_group_label("inside") == "Contains price / active band"
    assert _surface_group_label("below") == "Above price / resistance"
