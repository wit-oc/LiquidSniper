from __future__ import annotations

from liquidsniper.web.app import (
    _authoritative_group_title,
    _authoritative_view_scope_caption,
    _debug_payload_scope_caption,
    _format_authoritative_zone_line,
    _review_surface_scope_caption,
)


def test_authoritative_group_title_matches_review_contract() -> None:
    assert _authoritative_group_title("below_price") == "Below current price / support"
    assert _authoritative_group_title("contains_price") == "Contains current price / active band"
    assert _authoritative_group_title("above_price") == "Above current price / resistance"


def test_format_authoritative_zone_line_keeps_current_role_primary_and_origin_secondary() -> None:
    zone = {
        "tf": "1D",
        "bounds": {"low": 95.0, "mid": 96.0, "high": 97.0},
        "core_bounds": {"low": 95.5, "mid": 96.0, "high": 96.5},
        "core_definition": "overlap_density_core",
        "current_role": "support",
        "origin_kind": "resistance",
        "candidate_families": ["base", "reaction"],
        "selection_score": 81.25,
    }

    line = _format_authoritative_zone_line(zone)

    assert "band 95.0000 -> 97.0000" in line
    assert "mid 96.0000" in line
    assert "core 95.5000 -> 96.5000" in line
    assert "core mid 96.0000" in line
    assert "core rule overlap_density_core" in line
    assert "role support" in line
    assert "tf 1D" in line
    assert "families base, reaction" in line
    assert "sel 81.2" in line
    assert "origin resistance" in line
    assert line.index("role support") < line.index("origin resistance")



def test_scope_captions_make_semantic_boundaries_explicit() -> None:
    authoritative = _authoritative_view_scope_caption()
    review = _review_surface_scope_caption()
    debug = _debug_payload_scope_caption()

    assert "shadow-selected levels only" in authoritative
    assert "baseline vs shadow" in review
    assert "selected surfaces" in review
    assert "raw payload inspection" in debug
    assert "not the primary operator review surface" in debug
