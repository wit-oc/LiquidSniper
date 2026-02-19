from __future__ import annotations

from liquidsniper.core.replay_harness import score_case


def test_task22_decision_runs_without_trigger_when_canonical_ready() -> None:
    case = {
        "event": {
            "liquidity_size_usd": 600000,
            "distance_pct": 0.8,
            "age_seconds_min": 900,
            "cross_venue_agreement": 80,
        },
        "canonical_context": {
            "htf_regime": 82,
            "sr_retest": 78,
            "ltf_structure_shift": 75,
            "volatility_regime": 70,
        },
        "canonical_candles": {
            "available_timeframes": ["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
            "stale_timeframes": [],
        },
        # No trigger feed context present.
        "trigger_context": None,
    }

    out = score_case(case)

    assert out["canonical_ready"] is True
    assert out["canonical_gate_reasons"] == []
    assert out["decision"] in {"watch_only", "publish_candidate", "high_priority"}


def test_task22_missing_canonical_windows_fails_closed_even_with_trigger() -> None:
    case = {
        "event": {
            "liquidity_size_usd": 900000,
            "distance_pct": 0.2,
            "age_seconds_min": 300,
            "cross_venue_agreement": 95,
        },
        "canonical_context": {
            "htf_regime": 90,
            "sr_retest": 90,
            "ltf_structure_shift": 90,
            "volatility_regime": 90,
        },
        "canonical_candles": {
            "available_timeframes": ["1m", "5m", "15m", "1h"],
            "stale_timeframes": [],
        },
        "trigger_context": {"overlay_boost": 10},
    }

    out = score_case(case)

    assert out["canonical_ready"] is False
    assert "missing canonical windows:" in out["canonical_gate_reasons"][0]
    assert out["decision"] == "reject"


def test_task24_feed_degraded_blocks_promotion_and_adds_traceability() -> None:
    case = {
        "event": {
            "liquidity_size_usd": 900000,
            "distance_pct": 0.2,
            "age_seconds_min": 300,
            "cross_venue_agreement": 95,
        },
        "canonical_context": {
            "htf_regime": 90,
            "sr_retest": 90,
            "ltf_structure_shift": 90,
            "volatility_regime": 90,
        },
        "canonical_candles": {
            "available_timeframes": ["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
            "stale_timeframes": [],
            "trace_id": "canon-1",
        },
        "trigger_context": {"overlay_boost": 8, "trace_id": "trigger-1"},
        "feed_health": {"state": "degraded", "reason_codes": ["PROVIDER_RATE_LIMITED"]},
    }

    out = score_case(case)

    assert out["decision"] == "watch_only"
    assert "feed_health_degraded" in out["decision_reason_codes"]
    assert out["canonical_trace_id"] == "canon-1"
    assert out["trigger_trace_id"] == "trigger-1"


def test_task22_trigger_feed_is_overlay_only() -> None:
    base_case = {
        "event": {
            "liquidity_size_usd": 700000,
            "distance_pct": 0.6,
            "age_seconds_min": 1000,
            "cross_venue_agreement": 80,
        },
        "canonical_context": {
            "htf_regime": 70,
            "sr_retest": 70,
            "ltf_structure_shift": 70,
            "volatility_regime": 70,
        },
        "canonical_candles": {
            "available_timeframes": ["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
            "stale_timeframes": [],
        },
    }

    no_overlay = score_case(base_case)
    with_overlay = score_case({**base_case, "trigger_context": {"overlay_boost": 50}})

    assert with_overlay["decision"] != "reject"
    assert with_overlay["context_score"] - no_overlay["context_score"] <= 10.0
