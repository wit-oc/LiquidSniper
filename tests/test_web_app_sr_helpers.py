from __future__ import annotations

from liquidsniper.web.app import (
    _format_anchor_summary,
    _format_arbitration_summary,
    _format_zone_badges,
    _format_zone_summary,
)


def test_format_zone_helpers_make_operator_readable_strings() -> None:
    zone = {
        "zone_id": "z1",
        "tf": "4H",
        "kind": "support",
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
    assert "dist 42.5bps" in summary
    assert "sel 87.5" in summary
    assert "retest reject" in summary
    assert "anchor merged_zone_mid @ 99.0000" in summary
    assert "cluster=2" in arbitration
    assert "base=83.5 + bonus=4.0 => final=87.5" in arbitration
