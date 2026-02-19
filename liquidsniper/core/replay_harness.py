"""Deterministic replay harness for LiquidSniper MVP scoring.

This module replays fixture packs and verifies score/decision outputs against
optional golden expectations.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Thresholds:
    zone_to_context: float = 45.0
    pre_to_agent: float = 60.0
    publish_candidate: float = 70.0
    high_priority: float = 80.0


REQUIRED_CANDLE_WINDOWS = ("1m", "5m", "15m", "1h", "4h", "1d", "1w")
ANCHOR_PROFILE_MAP: dict[str, dict[str, Any]] = {
    "S": {"htf_anchor_tf": "1D", "itf_tf": "4H", "ltf_trigger_tfs": ["1H", "15m"]},
    "I": {"htf_anchor_tf": "4H", "itf_tf": "1H", "ltf_trigger_tfs": ["15m", "5m"]},
    "C": {"htf_anchor_tf": "1H", "itf_tf": "15m", "ltf_trigger_tfs": ["5m", "1m"]},
}

TF_RANK = {"1m": 1, "5m": 2, "15m": 3, "1h": 4, "4h": 5, "1d": 6, "1w": 7}

DECISION_TIER_RANK = {"reject": 0, "watch_only": 1, "publish_candidate": 2, "high_priority": 3}


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _round2(v: float) -> float:
    return round(float(v), 2)


def _size_score(liquidity_size_usd: float) -> float:
    # Log-scaled 10k -> 1m maps roughly to 20 -> 100.
    x = max(10_000.0, float(liquidity_size_usd or 0.0))
    lo = math.log10(10_000.0)
    hi = math.log10(1_000_000.0)
    n = (math.log10(x) - lo) / (hi - lo)
    return _clamp(20.0 + n * 80.0)


def _distance_score(distance_pct: float) -> float:
    # Closer levels score higher.
    d = max(0.0, float(distance_pct or 0.0))
    return _clamp(100.0 - d * 20.0)


def _freshness_score(age_seconds_min: int) -> float:
    age = max(0, int(age_seconds_min or 0))
    if age <= 3600:
        return 100.0
    if age <= 4 * 3600:
        return 80.0
    if age <= 12 * 3600:
        return 60.0
    if age <= 24 * 3600:
        return 40.0
    return 20.0


def score_zone_priority(event: dict[str, Any]) -> float:
    size = _size_score(float(event.get("liquidity_size_usd") or 0.0))
    dist = _distance_score(float(event.get("distance_pct") or 0.0))
    fresh = _freshness_score(int(event.get("age_seconds_min") or 0))
    cross = _clamp(float(event.get("cross_venue_agreement") or 50.0))

    return _round2(0.35 * size + 0.30 * dist + 0.20 * fresh + 0.15 * cross)


def score_context(context: dict[str, Any] | None) -> float:
    c = context or {}
    htf = _clamp(float(c.get("htf_regime") or 50.0))
    sr = _clamp(float(c.get("sr_retest") or 50.0))
    ltf = _clamp(float(c.get("ltf_structure_shift") or 50.0))
    vol = _clamp(float(c.get("volatility_regime") or 50.0))
    return _round2(0.35 * htf + 0.30 * sr + 0.20 * ltf + 0.15 * vol)


def _normalize_tf(tf: str) -> str:
    return str(tf or "").strip().lower()


def evaluate_canonical_candle_windows(canonical_candles: dict[str, Any] | None) -> tuple[bool, list[str]]:
    """Return availability gate for canonical candle windows.

    Missing/stale windows are fail-closed for strategy promotion.
    If canonical metadata is omitted (legacy fixtures), this gate is bypassed.
    """
    if canonical_candles is None:
        return True, []

    c = canonical_candles

    raw_available = c.get("available_timeframes") or []
    available = {_normalize_tf(tf) for tf in raw_available}

    raw_stale = c.get("stale_timeframes") or []
    stale = {_normalize_tf(tf) for tf in raw_stale}

    required = {_normalize_tf(tf) for tf in (c.get("required_timeframes") or REQUIRED_CANDLE_WINDOWS)}

    missing = sorted(tf for tf in required if tf not in available)
    stale_hit = sorted(tf for tf in required if tf in stale)

    reasons: list[str] = []
    if missing:
        reasons.append(f"missing canonical windows: {','.join(missing)}")
    if stale_hit:
        reasons.append(f"stale canonical windows: {','.join(stale_hit)}")

    return len(reasons) == 0, reasons


def _agent_confidence(agent: dict[str, Any] | None) -> float:
    a = agent or {}
    base = _clamp(float(a.get("agent_confidence") or 50.0))
    tv_status = str(a.get("tv_status") or "ok")
    if tv_status in {"unavailable", "auth_required", "failed"}:
        base = max(0.0, base - 15.0)
    return _round2(base)


def _normalize_tfs(raw: list[str] | tuple[str, ...] | None) -> list[str]:
    return [_normalize_tf(tf) for tf in (raw or [])]


def _apply_task14_15_contract(case: dict[str, Any], decision: str) -> tuple[str, list[str], str]:
    reason_codes: list[str] = []

    profile = str(case.get("anchor_profile_id") or "").strip()
    profile_spec = ANCHOR_PROFILE_MAP.get(profile)
    if profile_spec is None:
        reason_codes.append("invalid_profile_id")

    htf = str(case.get("htf_anchor_tf") or "").strip()
    itf = str(case.get("itf_tf") or "").strip()
    ltf = case.get("ltf_trigger_tfs") or []

    if profile_spec is not None:
        if (
            htf != profile_spec["htf_anchor_tf"]
            or itf != profile_spec["itf_tf"]
            or list(ltf) != list(profile_spec["ltf_trigger_tfs"])
        ):
            reason_codes.append("profile_tf_mismatch")

    htf_rank = TF_RANK.get(_normalize_tf(htf), 0)
    itf_rank = TF_RANK.get(_normalize_tf(itf), 0)
    ltf_ranks = [TF_RANK.get(_normalize_tf(tf), 0) for tf in ltf]
    if htf_rank == 0 or itf_rank == 0 or any(r == 0 for r in ltf_ranks) or not (htf_rank > itf_rank > max(ltf_ranks, default=0)):
        reason_codes.append("invalid_tf_hierarchy")

    regime_permission = str(case.get("regime_permission") or "").strip().lower()
    regime_reason_codes = case.get("regime_reason_codes") or []
    if regime_permission not in {"allow", "degrade", "deny"} or not regime_reason_codes:
        reason_codes.append("missing_regime_gate")

    if reason_codes:
        return "reject", reason_codes, regime_permission

    if regime_permission == "deny":
        decision = "watch_only"
        reason_codes.append("regime_deny_watch_only")
    elif regime_permission == "degrade" and DECISION_TIER_RANK.get(decision, 0) > DECISION_TIER_RANK["publish_candidate"]:
        decision = "publish_candidate"
        reason_codes.append("regime_degrade_cap")

    reason_codes.append("task14_15_contract_ok")
    return decision, reason_codes, regime_permission


def _runbook_decision(confluence: dict[str, Any]) -> tuple[str, int, bool]:
    """Apply runbook v1 confluence policy.

    Primary required:
    - support/resistance first retest
    - BoS/CHoCH alignment

    Secondary ranking (count-based tiering):
    - fib
    - trendline
    - liquidity_alert
    - vwap
    - ema200

    Low-confidence items (order blocks / supply zones) are intentionally ignored.
    """
    primary = confluence.get("primary") or {}
    secondary = confluence.get("secondary") or {}

    has_primary = bool(primary.get("sr_first_retest")) and bool(primary.get("bos_choch"))

    secondary_order = ["fib", "trendline", "liquidity_alert", "vwap", "ema200"]
    secondary_hits = sum(1 for k in secondary_order if bool(secondary.get(k)))

    if not has_primary:
        return "reject", secondary_hits, has_primary
    if secondary_hits >= 4:
        return "high_priority", secondary_hits, has_primary
    if secondary_hits >= 2:
        return "publish_candidate", secondary_hits, has_primary
    return "watch_only", secondary_hits, has_primary


def score_case(case: dict[str, Any], thresholds: Thresholds | None = None) -> dict[str, Any]:
    t = thresholds or Thresholds()
    feed_health = dict(case.get("feed_health") or {})

    # Canonical candles are the decision baseline (Task 22).
    canonical_ready, canonical_reasons = evaluate_canonical_candle_windows(case.get("canonical_candles"))
    feed_state = str(feed_health.get("state") or "ok").strip().lower()
    feed_reason_codes = [str(x) for x in (feed_health.get("reason_codes") or [])]
    feed_promotion_blocked = feed_state in {"degraded", "tripped", "resync_required"}

    event = dict(case.get("event") or {})
    zone_priority = score_zone_priority(event)

    # Canonical structural context is primary; trigger context is overlay-only.
    canonical_context_score = score_context(case.get("canonical_context") or case.get("context"))
    trigger_overlay = _clamp(float((case.get("trigger_context") or {}).get("overlay_boost") or 0.0), -10.0, 10.0)

    if canonical_ready and zone_priority >= t.zone_to_context:
        context_score = _round2(_clamp(canonical_context_score + trigger_overlay))
    else:
        context_score = 0.0

    pre_score = _round2(0.55 * zone_priority + 0.45 * context_score)

    if pre_score >= t.pre_to_agent:
        agent_confidence = _agent_confidence(case.get("agent"))
    else:
        agent_confidence = 0.0

    final_score = _round2(0.70 * pre_score + 0.30 * agent_confidence)

    if "confluence" in case:
        decision, secondary_hits, has_primary = _runbook_decision(dict(case.get("confluence") or {}))
    else:
        has_primary = True
        secondary_hits = 0
        if final_score >= t.high_priority:
            decision = "high_priority"
        elif final_score >= t.publish_candidate:
            decision = "publish_candidate"
        elif pre_score >= t.zone_to_context:
            decision = "watch_only"
        else:
            decision = "reject"

    if not canonical_ready:
        decision = "reject"

    if feed_promotion_blocked and decision in {"publish_candidate", "high_priority"}:
        decision = "watch_only"

    decision_reason_codes: list[str] = []
    regime_permission = "allow"
    if "anchor_profile_id" in case:
        decision, decision_reason_codes, regime_permission = _apply_task14_15_contract(case, decision)

    score_total = _round2(final_score / 10.0)
    score_gate_passed = score_total >= 6.0
    if "anchor_profile_id" in case and not score_gate_passed and decision != "reject":
        decision = "watch_only"
        decision_reason_codes.append("score_gate_below_6_0")

    if feed_promotion_blocked:
        decision_reason_codes.append("feed_health_degraded")
    decision_reason_codes.extend(f"feed_health:{code}" for code in feed_reason_codes)

    trigger_context = dict(case.get("trigger_context") or {})

    return {
        "id": case.get("id"),
        "zone_priority": zone_priority,
        "context_score": context_score,
        "pre_score": pre_score,
        "agent_confidence": agent_confidence,
        "final_score": final_score,
        "score_total": score_total,
        "score_gate_passed": score_gate_passed,
        "decision": decision,
        "decision_tier": decision,
        "decision_reason_codes": decision_reason_codes,
        "regime_permission": regime_permission,
        "runbook_primary_ok": has_primary,
        "runbook_secondary_hits": secondary_hits,
        "canonical_ready": canonical_ready,
        "canonical_gate_reasons": canonical_reasons,
        "anchor_profile_id": case.get("anchor_profile_id"),
        "htf_anchor_tf": case.get("htf_anchor_tf"),
        "rulebook_ref": case.get("rulebook_ref"),
        "policy_version": case.get("policy_version"),
        "feed_state": feed_state,
        "feed_reason_codes": feed_reason_codes,
        "canonical_trace_id": (case.get("canonical_candles") or {}).get("trace_id"),
        "trigger_trace_id": trigger_context.get("trace_id"),
        "trigger_influence": _round2(trigger_overlay),
    }


def run_fixture_pack(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    cases = list(payload.get("cases") or [])

    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for case in cases:
        out = score_case(case)
        results.append(out)

        expected = case.get("expected")
        if not expected:
            continue

        mismatch: dict[str, Any] = {}
        for k in (
            "zone_priority",
            "context_score",
            "pre_score",
            "agent_confidence",
            "final_score",
            "decision",
            "runbook_primary_ok",
            "runbook_secondary_hits",
            "canonical_ready",
            "canonical_gate_reasons",
        ):
            if k not in expected:
                continue
            if out.get(k) != expected.get(k):
                mismatch[k] = {"expected": expected.get(k), "actual": out.get(k)}

        if mismatch:
            failures.append({"id": case.get("id"), "mismatch": mismatch})

    return {
        "fixture": str(p),
        "total": len(cases),
        "passed": len(cases) - len(failures),
        "failed": len(failures),
        "failures": failures,
        "results": results,
    }
