from __future__ import annotations

from liquidsniper.core.pair_analytics import (
    PAIR_ANALYTICS_CONTRACT,
    STRUCTURE_DIAGNOSTIC_CONTRACT,
    build_market_structure_diagnostic,
    build_pair_analytics_snapshot,
)


def _zone(zone_id: str, mid: float, *, tf: str, kind: str = "support", family: str = "reaction") -> dict:
    return {
        "zone_id": zone_id,
        "symbol": "BTCUSDT",
        "tf": tf,
        "status": "confirmed",
        "zone_low": mid - 1.0,
        "zone_high": mid + 1.0,
        "zone_mid": mid,
        "zone_kind": kind,
        "strength_score": 82.0,
        "selection_score": 85.0,
        "reaction_score": 70.0,
        "reaction_efficiency_score": 75.0,
        "carry_score": 66.0,
        "body_respect_score": 68.0,
        "touch_count": 6,
        "meaningful_touch_count": 5,
        "first_retest_result": "reject",
        "candidate_sources": [family],
        "candidate_families": [family],
        "source_family": family,
        "family_stamp_contract": "zone_engine_v3_family_stamp_v1",
        "family_provenance": {family: {"family": family, "evidence": "fixture"}},
        "provenance_summary": {"primary_family": family, "candidate_families": [family], "has_structure": family == "structure", "merge_family_count": 1, "zone_kind": kind, "source_versions": [family], "generator_contracts": [family]},
        "source_versions": {family: f"{family}_v1"},
        "generator_contracts": {family: f"{family}_contract"},
        "price_anchor": {"kind": "merged_zone_mid", "zone_mid": mid},
        "arbitration_diagnostics": {
            "kept_zone_id": zone_id,
            "cluster_size": 1,
            "families": [family],
            "score_components": {
                "winner_base_score": 85.0,
                "family_confluence_bonus": 0.0,
                "final_selection_score": 85.0,
            },
        },
    }


def test_build_market_structure_diagnostic_adapts_phase1_engine():
    candles = [
        {"open": 10.0, "high": 11.0, "low": 9.0, "close": 10.4},
        {"open": 10.4, "high": 12.0, "low": 10.0, "close": 11.5},
        {"open": 11.5, "high": 13.0, "low": 11.0, "close": 12.6},
        {"open": 12.6, "high": 14.0, "low": 12.0, "close": 13.7},
        {"open": 13.7, "high": 14.5, "low": 13.0, "close": 13.3},
        {"open": 13.3, "high": 13.8, "low": 12.2, "close": 12.5},
        {"open": 12.5, "high": 12.9, "low": 11.5, "close": 11.8},
        {"open": 11.8, "high": 12.0, "low": 10.8, "close": 11.0},
        {"open": 11.0, "high": 11.2, "low": 10.2, "close": 10.4},
        {"open": 10.4, "high": 10.8, "low": 9.7, "close": 9.9},
    ]
    payload = build_market_structure_diagnostic(candles=candles, tf="1D")
    assert payload["contract"] == STRUCTURE_DIAGNOSTIC_CONTRACT
    assert payload["status"] == "ok"
    assert payload["trend"] in {"bullish", "bearish"}
    assert isinstance(payload["event_counts"], dict)
    assert "diagnostics" in payload


def test_build_pair_analytics_snapshot_combines_sr_and_structure_contracts():
    zones = [
        _zone("d1", 98.0, tf="1D", kind="support", family="reaction"),
        _zone("d2", 105.0, tf="1D", kind="resistance", family="structure"),
        _zone("h1", 99.0, tf="4H", kind="support", family="base"),
        _zone("h2", 104.0, tf="4H", kind="resistance", family="reaction"),
    ]
    candles_by_tf = {
        "1D": [
            {"open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5},
            {"open": 10.5, "high": 12.0, "low": 10.0, "close": 11.5},
            {"open": 11.5, "high": 13.0, "low": 11.0, "close": 12.5},
            {"open": 12.5, "high": 14.0, "low": 12.0, "close": 13.5},
            {"open": 13.5, "high": 14.2, "low": 13.0, "close": 13.2},
            {"open": 13.2, "high": 13.4, "low": 12.2, "close": 12.5},
            {"open": 12.5, "high": 12.8, "low": 11.5, "close": 11.8},
            {"open": 11.8, "high": 12.0, "low": 10.9, "close": 11.1},
        ],
        "4H": [
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.4},
            {"open": 100.4, "high": 101.3, "low": 99.8, "close": 100.8},
            {"open": 100.8, "high": 102.0, "low": 100.2, "close": 101.8},
            {"open": 101.8, "high": 103.0, "low": 101.1, "close": 102.6},
            {"open": 102.6, "high": 103.2, "low": 101.8, "close": 102.0},
            {"open": 102.0, "high": 102.2, "low": 100.9, "close": 101.1},
            {"open": 101.1, "high": 101.5, "low": 100.2, "close": 100.5},
            {"open": 100.5, "high": 100.9, "low": 99.7, "close": 99.9},
        ],
    }
    payload = build_pair_analytics_snapshot(
        symbol="BTCUSDT",
        profile_id="I",
        entry=100.0,
        zones=zones,
        candles_by_tf=candles_by_tf,
        timeframe_availability={
            "1H": {"timeframe": "1H", "status": "missing_source", "reason": "no matching candle csv found"},
        },
    )
    assert payload["contract"] == PAIR_ANALYTICS_CONTRACT
    nearest_support = payload["sr"]["nearest_levels"]["nearest_support"]
    nearest_resistance = payload["sr"]["nearest_levels"]["nearest_resistance"]
    majors = payload["sr"]["majors"]
    assert nearest_support["zone_id"] == "h1"
    assert nearest_support["kind"] == "containing"
    assert nearest_support["bounds"]["mid"] == 99.0
    assert nearest_support["selection_score"] == 85.0
    assert nearest_support["first_retest_status"] == "reject"
    assert nearest_support["price_anchor"]["zone_mid"] == 99.0
    assert nearest_support["family_stamp_contract"] == "zone_engine_v3_family_stamp_v1"
    assert nearest_support["role_semantics"]["review_label"] == "containing"
    assert nearest_support["role_semantics"]["relative_position"] == "inside"
    assert nearest_support["role_semantics"]["origin_kind"] == "support"
    assert nearest_support["provenance"]["family_provenance"]["base"]["evidence"] == "fixture"
    assert nearest_support["family_provenance"]["base"]["evidence"] == "fixture"
    assert nearest_support["provenance_summary"]["primary_family"] == "base"
    assert nearest_support["provenance"]["source_versions"]["base"] == "base_v1"
    assert nearest_support["source_versions"]["base"] == "base_v1"
    assert nearest_support["generator_contracts"]["base"] == "base_contract"
    assert "base" in nearest_support["family_badges"]
    assert nearest_support["arbitration"]["kept_zone_id"] == "h1"
    assert nearest_resistance["zone_id"] == "h2"
    assert majors[0]["kind"] == "support"
    assert majors[0]["origin_kind"] == "support"
    assert majors[1]["kind"] == "resistance"
    assert majors[1]["origin_kind"] == "resistance"
    assert payload["market_structure"]["contract"] == STRUCTURE_DIAGNOSTIC_CONTRACT
    assert set(payload["market_structure"]["available_timeframes"]) == {"1D", "4H"}
    availability = {row["timeframe"]: row for row in payload["market_structure"]["availability"]}
    assert availability["1D"]["status"] == "ready"
    assert availability["4H"]["status"] == "ready"
    assert availability["1H"]["status"] == "missing_source"
