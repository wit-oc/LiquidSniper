from __future__ import annotations

from liquidsniper.ops.sr_bootstrap import _build_authoritative_surface


def _zone(
    zone_id: str,
    *,
    low: float,
    high: float,
    tf: str = "1D",
    current_role: str | None = None,
    origin_kind: str = "support",
    core_low: float | None = None,
    core_high: float | None = None,
    core_definition: str | None = None,
) -> dict:
    payload = {
        "zone_id": zone_id,
        "tf": tf,
        "zone_low": low,
        "zone_mid": (low + high) / 2.0,
        "zone_high": high,
        "origin_kind": origin_kind,
        "current_role": current_role,
        "selection_score": 80.0,
        "candidate_families": ["base"],
    }
    if core_low is not None and core_high is not None:
        payload["core_low"] = core_low
        payload["core_high"] = core_high
        payload["core_mid"] = (core_low + core_high) / 2.0
        payload["core_definition"] = core_definition or "narrowed_operator_core"
    return payload


def test_build_authoritative_surface_groups_shadow_selected_levels_for_review() -> None:
    zones = [
        _zone("support-high", low=97.0, high=98.0, current_role="support"),
        _zone("support-low", low=95.0, high=96.0, current_role="support"),
        _zone("active-band", low=99.0, high=101.0, current_role="containing", origin_kind="resistance", core_low=99.4, core_high=100.2, core_definition="overlap_density_core"),
        _zone("resistance-high", low=105.0, high=106.0, current_role="resistance", origin_kind="resistance"),
        _zone("resistance-low", low=103.0, high=104.0, current_role="resistance", origin_kind="resistance"),
    ]

    surface = _build_authoritative_surface(zones, entry=100.0, tf="1D", selector_surface="daily_major")

    assert surface["contract"] == "authoritative_levels_view_v1"
    assert surface["selector_surface"] == "daily_major"
    assert surface["group_perspective"] == "zone_relative_to_price"
    assert [z["zone_id"] for z in surface["groups"]["below_price"]] == ["support-low", "support-high"]
    assert [z["zone_id"] for z in surface["groups"]["contains_price"]] == ["active-band"]
    assert [z["zone_id"] for z in surface["groups"]["above_price"]] == ["resistance-low", "resistance-high"]
    assert surface["groups"]["contains_price"][0]["current_role"] == "containing"
    assert surface["groups"]["contains_price"][0]["origin_kind"] == "resistance"
    core_bounds = surface["groups"]["contains_price"][0]["core_bounds"]
    assert core_bounds["low"] == 99.4
    assert round(float(core_bounds["mid"]), 4) == 99.8
    assert core_bounds["high"] == 100.2
    assert surface["groups"]["contains_price"][0]["core_definition"] == "overlap_density_core"
