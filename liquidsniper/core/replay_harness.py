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


def _agent_confidence(agent: dict[str, Any] | None) -> float:
    a = agent or {}
    base = _clamp(float(a.get("agent_confidence") or 50.0))
    tv_status = str(a.get("tv_status") or "ok")
    if tv_status in {"unavailable", "auth_required", "failed"}:
        base = max(0.0, base - 15.0)
    return _round2(base)


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
    event = dict(case.get("event") or {})

    zone_priority = score_zone_priority(event)
    context_score = score_context(case.get("context")) if zone_priority >= t.zone_to_context else 0.0
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

    return {
        "id": case.get("id"),
        "zone_priority": zone_priority,
        "context_score": context_score,
        "pre_score": pre_score,
        "agent_confidence": agent_confidence,
        "final_score": final_score,
        "decision": decision,
        "runbook_primary_ok": has_primary,
        "runbook_secondary_hits": secondary_hits,
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
