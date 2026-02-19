from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DECISION_TIER_RANK = {"reject": 0, "watch_only": 1, "publish_candidate": 2, "high_priority": 3}


@dataclass(frozen=True)
class AdversarialGateConfig:
    max_profile_drift_tier_delta: int = 1
    max_cost_tail_error_bps: float = 12.0
    max_trigger_influence: float = 10.0


@dataclass(frozen=True)
class FeedBenchmarkConfig:
    max_gap_rate: float = 0.02
    max_rate_limit_rate: float = 0.05
    min_freshness_rate: float = 0.95
    stale_lag_ms: int = 120_000


def _tier(decision: str) -> int:
    return DECISION_TIER_RANK.get(str(decision or "reject"), 0)


def run_two_pass_adversarial_validation(
    pass1_cases: list[dict[str, Any]],
    pass2_cases: list[dict[str, Any]],
    config: AdversarialGateConfig | None = None,
) -> dict[str, Any]:
    cfg = config or AdversarialGateConfig()

    pass1_failures: list[dict[str, Any]] = []
    for case in pass1_cases:
        cid = str(case.get("id") or "unknown")

        baseline = _tier(str(case.get("baseline_decision") or "reject"))
        stressed = _tier(str(case.get("stressed_decision") or "reject"))
        drift = abs(baseline - stressed)
        if drift > cfg.max_profile_drift_tier_delta:
            pass1_failures.append({"id": cid, "gate": "anchor_profile_drift", "reason_code": "ANCHOR_PROFILE_DRIFT_EXCESS", "drift": drift})

        expected_cost = float(case.get("expected_cost_bps") or 0.0)
        realized_cost = float(case.get("realized_cost_bps") or 0.0)
        tail_error = abs(realized_cost - expected_cost)
        if tail_error > cfg.max_cost_tail_error_bps:
            pass1_failures.append({"id": cid, "gate": "cost_tail_error", "reason_code": "COST_TAIL_ERROR_EXCESS", "tail_error_bps": round(tail_error, 2)})

        trigger_influence = abs(float(case.get("trigger_influence") or 0.0))
        if trigger_influence > cfg.max_trigger_influence:
            pass1_failures.append({"id": cid, "gate": "trigger_inflation", "reason_code": "TRIGGER_INFLATION_EXCESS", "trigger_influence": round(trigger_influence, 2)})

    pass2_failures: list[dict[str, Any]] = []
    for case in pass2_cases:
        cid = str(case.get("id") or "unknown")
        expected_policy_version = str(case.get("expected_policy_version") or "")
        observed_policy_version = str(case.get("observed_policy_version") or "")
        if not expected_policy_version or observed_policy_version != expected_policy_version:
            pass2_failures.append({"id": cid, "gate": "policy_version_pinning", "reason_code": "POLICY_VERSION_UNPINNED"})

        if not bool(case.get("non_bypass_ok")):
            pass2_failures.append({"id": cid, "gate": "non_bypass_contract", "reason_code": "NON_BYPASS_FAILED"})

        if not bool(case.get("replay_parity_ok")):
            pass2_failures.append({"id": cid, "gate": "replay_parity", "reason_code": "REPLAY_PARITY_FAILED"})

        if not bool(case.get("reason_code_audit_ok")):
            pass2_failures.append({"id": cid, "gate": "reason_code_audit", "reason_code": "REASON_CODE_AUDIT_FAILED"})

    pass1_ok = len(pass1_failures) == 0
    pass2_ok = len(pass2_failures) == 0
    reason_codes = [f["reason_code"] for f in (pass1_failures + pass2_failures)]

    return {
        "pass1": {"ok": pass1_ok, "total": len(pass1_cases), "failures": pass1_failures},
        "pass2": {"ok": pass2_ok, "total": len(pass2_cases), "failures": pass2_failures},
        "promotion_blocked": not (pass1_ok and pass2_ok),
        "reason_codes": sorted(set(reason_codes)),
    }


def build_feed_benchmark_report(
    feed_cycles: list[dict[str, Any]],
    replay_parity_cases: list[dict[str, Any]],
    config: FeedBenchmarkConfig | None = None,
) -> dict[str, Any]:
    cfg = config or FeedBenchmarkConfig()

    total = len(feed_cycles)
    if total == 0:
        coverage_rate = 0.0
        freshness_rate = 0.0
        gap_rate = 1.0
        rate_limit_rate = 1.0
        tripped_rate = 0.0
        retries_total = 0
        retries_recovered = 0
    else:
        inserted_ok = sum(1 for c in feed_cycles if int(c.get("inserted") or 0) > 0)
        fresh_ok = sum(1 for c in feed_cycles if int(c.get("lag_ms") or 0) <= cfg.stale_lag_ms)
        gap_events = sum(1 for c in feed_cycles if "CANDLE_GAP_DETECTED" in (c.get("reason_codes") or []))
        rate_limited = sum(1 for c in feed_cycles if "PROVIDER_RATE_LIMITED" in (c.get("reason_codes") or []))
        tripped_events = sum(1 for c in feed_cycles if str(c.get("state") or "") == "tripped")
        retry_cases = [c for c in feed_cycles if int(c.get("retry_count") or 0) > 0]
        retries_total = len(retry_cases)
        retries_recovered = sum(1 for c in retry_cases if str(c.get("state") or "") == "ok")

        coverage_rate = round(inserted_ok / total, 4)
        freshness_rate = round(fresh_ok / total, 4)
        gap_rate = round(gap_events / total, 4)
        rate_limit_rate = round(rate_limited / total, 4)
        tripped_rate = round(tripped_events / total, 4)

    parity_by_anchor = {
        str(c.get("anchor") or "").upper(): bool(c.get("parity_ok")) for c in replay_parity_cases
    }
    anchor_1d_ok = parity_by_anchor.get("1D", False)
    anchor_1h_ok = parity_by_anchor.get("1H", False)
    parity_ok = anchor_1d_ok and anchor_1h_ok

    benchmark_ok = (
        coverage_rate > 0.0
        and freshness_rate >= cfg.min_freshness_rate
        and gap_rate <= cfg.max_gap_rate
        and rate_limit_rate <= cfg.max_rate_limit_rate
        and parity_ok
    )

    reason_codes: list[str] = []
    if freshness_rate < cfg.min_freshness_rate:
        reason_codes.append("FEED_FRESHNESS_BELOW_THRESHOLD")
    if gap_rate > cfg.max_gap_rate:
        reason_codes.append("FEED_GAP_RATE_HIGH")
    if rate_limit_rate > cfg.max_rate_limit_rate:
        reason_codes.append("FEED_RATE_LIMIT_RATE_HIGH")
    if not anchor_1d_ok:
        reason_codes.append("REPLAY_PARITY_1D_FAILED")
    if not anchor_1h_ok:
        reason_codes.append("REPLAY_PARITY_1H_FAILED")

    return {
        "benchmark_ok": benchmark_ok,
        "metrics": {
            "cycles_total": total,
            "coverage_rate": coverage_rate,
            "freshness_rate": freshness_rate,
            "gap_rate": gap_rate,
            "rate_limit_rate": rate_limit_rate,
            "tripped_rate": tripped_rate,
            "retry_outcomes": {"total": retries_total, "recovered_ok": retries_recovered},
        },
        "replay_parity": {"1D": anchor_1d_ok, "1H": anchor_1h_ok, "ok": parity_ok},
        "reason_codes": reason_codes,
    }


def build_gate_evidence_pack(
    pass1_cases: list[dict[str, Any]],
    pass2_cases: list[dict[str, Any]],
    feed_cycles: list[dict[str, Any]],
    replay_parity_cases: list[dict[str, Any]],
) -> dict[str, Any]:
    adversarial = run_two_pass_adversarial_validation(pass1_cases, pass2_cases)
    benchmark = build_feed_benchmark_report(feed_cycles, replay_parity_cases)

    critical_no_go = {"POLICY_VERSION_UNPINNED", "NON_BYPASS_FAILED", "REPLAY_PARITY_FAILED"}
    has_critical = any(code in critical_no_go for code in adversarial["reason_codes"])

    if has_critical:
        recommendation = "NO_GO"
    elif adversarial["promotion_blocked"] or not benchmark["benchmark_ok"]:
        recommendation = "HOLD"
    else:
        recommendation = "GO"

    return {
        "adversarial": adversarial,
        "feed_benchmark": benchmark,
        "recommendation": recommendation,
        "promotion_blocked": adversarial["promotion_blocked"] or not benchmark["benchmark_ok"],
    }
