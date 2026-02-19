from __future__ import annotations

from liquidsniper.core.replay_harness import score_case


BASE_CASE = {
    "event": {
        "liquidity_size_usd": 820000,
        "distance_pct": 0.9,
        "age_seconds_min": 2400,
        "cross_venue_agreement": 85,
    },
    "canonical_context": {
        "htf_regime": 82,
        "sr_retest": 76,
        "ltf_structure_shift": 73,
        "volatility_regime": 66,
    },
    "canonical_candles": {
        "available_timeframes": ["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
        "stale_timeframes": [],
    },
    "agent": {"agent_confidence": 81, "tv_status": "ok"},
    "confluence": {
        "primary": {"sr_first_retest": True, "bos_choch": True},
        "secondary": {"fib": True, "trendline": True, "liquidity_alert": True, "vwap": True, "ema200": True},
    },
    "anchor_profile_id": "S",
    "htf_anchor_tf": "1D",
    "itf_tf": "4H",
    "ltf_trigger_tfs": ["1H", "15m"],
    "regime_permission": "allow",
    "regime_reason_codes": ["htf_aligned"],
    "rulebook_ref": "TRADING_STRATEGY_RUNBOOK_V1",
    "policy_version": "v1",
}


def test_task14_15_valid_payload_mapping_with_score_gate() -> None:
    out = score_case(BASE_CASE)
    assert out["decision_tier"] == "high_priority"
    assert out["score_total"] >= 6.0
    assert out["score_gate_passed"] is True
    assert out["decision_reason_codes"] == ["task14_15_contract_ok"]


def test_task14_15_profile_timeframe_mismatch_rejects() -> None:
    out = score_case({**BASE_CASE, "itf_tf": "15m"})
    assert out["decision_tier"] == "reject"
    assert "profile_tf_mismatch" in out["decision_reason_codes"]


def test_task14_15_degrade_caps_high_priority_to_publish_candidate() -> None:
    out = score_case({**BASE_CASE, "regime_permission": "degrade", "regime_reason_codes": ["reduced_confidence"]})
    assert out["decision_tier"] == "publish_candidate"
    assert "regime_degrade_cap" in out["decision_reason_codes"]


def test_task14_15_score_gate_below_6_forces_watch_only() -> None:
    low_case = {
        **BASE_CASE,
        "event": {
            "liquidity_size_usd": 50000,
            "distance_pct": 6.5,
            "age_seconds_min": 86000,
            "cross_venue_agreement": 30,
        },
        "canonical_context": {
            "htf_regime": 45,
            "sr_retest": 40,
            "ltf_structure_shift": 42,
            "volatility_regime": 35,
        },
        "confluence": {
            "primary": {"sr_first_retest": True, "bos_choch": True},
            "secondary": {"fib": True, "trendline": True, "liquidity_alert": True, "vwap": False, "ema200": False},
        },
    }
    out = score_case(low_case)
    assert out["score_total"] < 6.0
    assert out["score_gate_passed"] is False
    assert out["decision_tier"] == "watch_only"
    assert "score_gate_below_6_0" in out["decision_reason_codes"]
