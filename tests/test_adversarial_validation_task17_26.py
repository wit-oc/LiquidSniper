from __future__ import annotations

from liquidsniper.core.adversarial_validation import (
    build_feed_benchmark_report,
    build_gate_evidence_pack,
    run_two_pass_adversarial_validation,
)


def test_task17_two_pass_validation_blocks_on_failed_gates() -> None:
    pass1_cases = [
        {
            "id": "p1-a",
            "baseline_decision": "high_priority",
            "stressed_decision": "watch_only",
            "expected_cost_bps": 8,
            "realized_cost_bps": 26,
            "trigger_influence": 14,
        }
    ]
    pass2_cases = [
        {
            "id": "p2-a",
            "expected_policy_version": "v1",
            "observed_policy_version": "v2",
            "non_bypass_ok": False,
            "replay_parity_ok": True,
            "reason_code_audit_ok": True,
        }
    ]

    out = run_two_pass_adversarial_validation(pass1_cases, pass2_cases)

    assert out["promotion_blocked"] is True
    assert out["pass1"]["ok"] is False
    assert out["pass2"]["ok"] is False
    assert "ANCHOR_PROFILE_DRIFT_EXCESS" in out["reason_codes"]
    assert "COST_TAIL_ERROR_EXCESS" in out["reason_codes"]
    assert "TRIGGER_INFLATION_EXCESS" in out["reason_codes"]
    assert "POLICY_VERSION_UNPINNED" in out["reason_codes"]
    assert "NON_BYPASS_FAILED" in out["reason_codes"]


def test_task26_feed_benchmark_requires_1d_and_1h_parity() -> None:
    feed_cycles = [
        {"state": "ok", "inserted": 5, "lag_ms": 60_000, "reason_codes": [], "retry_count": 0},
        {"state": "ok", "inserted": 4, "lag_ms": 50_000, "reason_codes": [], "retry_count": 1},
        {"state": "ok", "inserted": 6, "lag_ms": 70_000, "reason_codes": [], "retry_count": 0},
    ]
    replay_parity_cases = [
        {"anchor": "1D", "parity_ok": True},
        {"anchor": "1H", "parity_ok": False},
    ]

    out = build_feed_benchmark_report(feed_cycles, replay_parity_cases)

    assert out["benchmark_ok"] is False
    assert out["replay_parity"]["1D"] is True
    assert out["replay_parity"]["1H"] is False
    assert "REPLAY_PARITY_1H_FAILED" in out["reason_codes"]


def test_task17_26_evidence_pack_yields_go_when_gates_are_clean() -> None:
    pass1_cases = [
        {
            "id": "p1-clean",
            "baseline_decision": "publish_candidate",
            "stressed_decision": "watch_only",
            "expected_cost_bps": 10,
            "realized_cost_bps": 15,
            "trigger_influence": 8,
        }
    ]
    pass2_cases = [
        {
            "id": "p2-clean",
            "expected_policy_version": "v1",
            "observed_policy_version": "v1",
            "non_bypass_ok": True,
            "replay_parity_ok": True,
            "reason_code_audit_ok": True,
        }
    ]
    feed_cycles = [
        {"state": "ok", "inserted": 5, "lag_ms": 30_000, "reason_codes": [], "retry_count": 0},
        {"state": "ok", "inserted": 4, "lag_ms": 40_000, "reason_codes": [], "retry_count": 1},
        {"state": "ok", "inserted": 6, "lag_ms": 60_000, "reason_codes": [], "retry_count": 0},
        {"state": "ok", "inserted": 7, "lag_ms": 80_000, "reason_codes": [], "retry_count": 0},
        {"state": "ok", "inserted": 5, "lag_ms": 50_000, "reason_codes": [], "retry_count": 0},
    ]
    replay_parity_cases = [{"anchor": "1D", "parity_ok": True}, {"anchor": "1H", "parity_ok": True}]

    out = build_gate_evidence_pack(pass1_cases, pass2_cases, feed_cycles, replay_parity_cases)

    assert out["adversarial"]["promotion_blocked"] is False
    assert out["feed_benchmark"]["benchmark_ok"] is True
    assert out["recommendation"] == "GO"
    assert out["promotion_blocked"] is False
