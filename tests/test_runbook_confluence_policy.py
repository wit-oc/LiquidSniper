from __future__ import annotations

from liquidsniper.core.replay_harness import score_case


def test_publish_requires_both_primary_confluences() -> None:
    case = {
        "event": {"liquidity_size_usd": 500000, "distance_pct": 1.0, "age_seconds_min": 1000},
        "context": {"htf_regime": 80, "sr_retest": 80, "ltf_structure_shift": 80, "volatility_regime": 60},
        "agent": {"agent_confidence": 90, "tv_status": "ok"},
        "confluence": {
            "primary": {"sr_first_retest": True, "bos_choch": False},
            "secondary": {"fib": True, "trendline": True, "liquidity_alert": True, "vwap": True, "ema200": True},
        },
    }
    out = score_case(case)
    assert out["runbook_primary_ok"] is False
    assert out["decision"] == "reject"


def test_low_confidence_flags_do_not_promote_decision() -> None:
    case = {
        "event": {"liquidity_size_usd": 500000, "distance_pct": 1.0, "age_seconds_min": 1000},
        "context": {"htf_regime": 80, "sr_retest": 80, "ltf_structure_shift": 80, "volatility_regime": 60},
        "agent": {"agent_confidence": 90, "tv_status": "ok"},
        "confluence": {
            "primary": {"sr_first_retest": True, "bos_choch": True},
            "secondary": {"fib": True, "trendline": False, "liquidity_alert": False, "vwap": False, "ema200": False},
            "low_confidence": {"order_blocks": True, "supply_zones": True},
        },
    }
    out = score_case(case)
    assert out["runbook_secondary_hits"] == 1
    assert out["decision"] == "watch_only"
