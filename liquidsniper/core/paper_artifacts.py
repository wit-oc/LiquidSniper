"""Paper MVP artifact persistence helpers."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os


REQUIRED_RUN_FIELDS = (
    "entry",
    "stop_loss_initial",
    "tp_levels",
    "tp_plan",
    "tp_events",
    "exit_reason",
    "pnl_r",
    "pnl_pct",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _f(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _tp_levels(payload: dict[str, Any]) -> list[float]:
    raw = payload.get("tp_levels")
    if isinstance(raw, list):
        out = [_f(v) for v in raw]
        return [v for v in out if v is not None]

    legacy = [_f(payload.get("tp1")), _f(payload.get("tp2")), _f(payload.get("tp3"))]
    return [v for v in legacy if v is not None]


def _tp_plan(payload: dict[str, Any], tp_levels: list[float]) -> list[dict[str, float]]:
    raw = payload.get("tp_plan")
    if isinstance(raw, list):
        plan: list[dict[str, float]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            level = _f(item.get("level"))
            size_pct = _f(item.get("size_pct"))
            if level is None or size_pct is None:
                continue
            plan.append({"level": level, "size_pct": size_pct})
        if plan:
            return plan

    if not tp_levels:
        return []

    if len(tp_levels) == 1:
        splits = [1.0]
    elif len(tp_levels) == 2:
        splits = [0.5, 0.5]
    elif len(tp_levels) == 3:
        splits = [0.4, 0.35, 0.25]
    else:
        per = round(1.0 / len(tp_levels), 4)
        splits = [per] * len(tp_levels)

    return [{"level": lvl, "size_pct": splits[i]} for i, lvl in enumerate(tp_levels)]


def build_run_artifact(proposal: dict[str, Any], execution_result: dict[str, Any]) -> dict[str, Any]:
    trade_intent = proposal.get("trade_intent") if isinstance(proposal.get("trade_intent"), dict) else {}
    adapter = execution_result.get("adapter_result") if isinstance(execution_result.get("adapter_result"), dict) else {}

    merged: dict[str, Any] = {}
    merged.update(trade_intent)
    merged.update(adapter)
    merged.update(proposal)

    run_id = str(proposal.get("trace_id") or proposal.get("run_id") or "")
    timestamp = (
        merged.get("timestamp")
        or merged.get("ts")
        or trade_intent.get("ts")
        or _utc_now()
    )
    entry = _f(merged.get("entry") or merged.get("limit_price"))
    stop = _f(merged.get("stop_loss_initial") or merged.get("stop_loss") or merged.get("stop"))
    tp_levels = _tp_levels(merged)
    tp_plan = _tp_plan(merged, tp_levels)

    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "symbol": merged.get("symbol"),
        "direction": merged.get("side"),
        "anchor_profile_id": merged.get("anchor_profile_id"),
        "htf_anchor_tf": merged.get("htf_anchor_tf"),
        "score_total": _f(merged.get("score_total") or merged.get("final_score")),
        "score_gate_passed": bool(merged.get("score_gate_passed", False)),
        "decision_tier": merged.get("decision_tier") or merged.get("decision"),
        "decision_reason_codes": list(merged.get("decision_reason_codes") or execution_result.get("reason_codes") or []),
        "feed_state": merged.get("feed_state"),
        "feed_reason_codes": list(merged.get("feed_reason_codes") or []),
        "canonical_trace_id": merged.get("canonical_trace_id") or run_id,
        "trigger_trace_id": merged.get("trigger_trace_id"),
        "trigger_influence": _f(merged.get("trigger_influence")),
        "entry": entry,
        "stop_loss_initial": stop,
        "tp_levels": tp_levels,
        "tp_plan": tp_plan,
        "stop_policy": {
            "move_to_break_even_on_tp1": True,
            "break_even_price": entry,
            "post_tp1_trailing": "disabled_by_default",
        },
        "risk_pct_requested": _f(merged.get("risk_pct_requested") or merged.get("risk_pct")),
        "risk_pct_allowed": _f(merged.get("risk_pct_allowed") or merged.get("risk_pct")),
        "proposal_decision": "accepted" if execution_result.get("decision") in {"executed", "noop"} else "rejected",
        "execution_decision": execution_result.get("decision") or "noop",
        "tp_events": list(merged.get("tp_events") or []),
        "pnl_r": _f(merged.get("pnl_r")),
        "pnl_pct": _f(merged.get("pnl_pct")),
        "max_adverse_excursion_r": _f(merged.get("max_adverse_excursion_r")),
        "max_favorable_excursion_r": _f(merged.get("max_favorable_excursion_r")),
        "exit_reason": merged.get("exit_reason"),
        "policy_version": proposal.get("policy_version"),
        "rulebook_ref": proposal.get("rulebook_ref"),
    }


def persist_run_artifact(proposal: dict[str, Any], execution_result: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    payload = build_run_artifact(proposal, execution_result)
    run_id = str(payload.get("run_id") or "").strip()
    if not run_id:
        raise ValueError("run_id is required to persist paper run artifact")

    artifact_root = Path(os.getenv("LS_ARTIFACT_ROOT", "artifacts"))
    path = artifact_root / "paper_mvp" / "runs" / f"{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return payload, path


def _parse_day(timestamp: Any) -> str | None:
    if not isinstance(timestamp, str) or not timestamp.strip():
        return None
    token = timestamp.strip()
    if len(token) >= 10:
        return token[:10]
    return None


def _load_run_payloads_for_day(*, trading_day: str, artifact_root: Path) -> list[dict[str, Any]]:
    runs_dir = artifact_root / "paper_mvp" / "runs"
    if not runs_dir.exists():
        return []

    out: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if _parse_day(payload.get("timestamp")) != trading_day:
            continue
        out.append(payload)
    return out


def build_daily_scorecard(*, trading_day: str, runs: list[dict[str, Any]]) -> dict[str, Any]:
    total_runs = len(runs)
    accepted = sum(1 for row in runs if row.get("proposal_decision") == "accepted")
    executed = sum(1 for row in runs if row.get("execution_decision") == "executed")
    rejected = sum(1 for row in runs if row.get("proposal_decision") == "rejected")

    realized = [
        _f(row.get("pnl_r"))
        for row in runs
        if row.get("execution_decision") == "executed" and _f(row.get("pnl_r")) is not None
    ]
    realized_values = [v for v in realized if v is not None]

    expectancy_r = round(sum(realized_values) / len(realized_values), 4) if realized_values else None
    wins = [v for v in realized_values if v > 0]
    losses = [v for v in realized_values if v < 0]
    win_rate = round(len(wins) / len(realized_values), 4) if realized_values else None
    if losses:
        profit_factor = round(sum(wins) / abs(sum(losses)), 4)
    elif wins:
        profit_factor = None
    else:
        profit_factor = None

    reject_counter: Counter[str] = Counter()
    feed_reason_counter: Counter[str] = Counter()
    feed_state_counter: Counter[str] = Counter()
    for row in runs:
        if row.get("proposal_decision") != "accepted":
            for code in row.get("decision_reason_codes") or []:
                if isinstance(code, str) and code:
                    reject_counter[code] += 1

        feed_state = row.get("feed_state")
        if isinstance(feed_state, str) and feed_state:
            feed_state_counter[feed_state] += 1

        for code in row.get("feed_reason_codes") or []:
            if isinstance(code, str) and code:
                feed_reason_counter[code] += 1

    ok_feeds = feed_state_counter.get("ok", 0)
    freshness_pct = round(ok_feeds / total_runs, 4) if total_runs else None

    gap_hits = sum(v for k, v in feed_reason_counter.items() if "GAP" in k)
    rate_limit_hits = sum(v for k, v in feed_reason_counter.items() if "RATE_LIMIT" in k)
    gap_rate = round(gap_hits / total_runs, 4) if total_runs else None
    rate_limit_rate = round(rate_limit_hits / total_runs, 4) if total_runs else None

    top_reject_reasons = [
        {"code": code, "count": count}
        for code, count in sorted(reject_counter.items(), key=lambda item: (-item[1], item[0]))[:3]
    ]

    return {
        "date": trading_day,
        "runs_total": total_runs,
        "accepted": accepted,
        "executed": executed,
        "rejected": rejected,
        "expectancy_r": expectancy_r,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "reject_reason_distribution": dict(sorted(reject_counter.items())),
        "top_reject_reasons": top_reject_reasons,
        "feed_health": {
            "freshness_pct": freshness_pct,
            "gap_rate": gap_rate,
            "rate_limit_rate": rate_limit_rate,
            "feed_state_distribution": dict(sorted(feed_state_counter.items())),
            "feed_reason_distribution": dict(sorted(feed_reason_counter.items())),
        },
    }


def persist_daily_scorecard(*, trading_day: str, artifact_root: Path | None = None) -> tuple[dict[str, Any], Path]:
    root = artifact_root or Path(os.getenv("LS_ARTIFACT_ROOT", "artifacts"))
    runs = _load_run_payloads_for_day(trading_day=trading_day, artifact_root=root)
    payload = build_daily_scorecard(trading_day=trading_day, runs=runs)

    path = root / "paper_mvp" / "daily" / f"{trading_day}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return payload, path


def _iso_week(date_token: str) -> str | None:
    try:
        dt = datetime.fromisoformat(date_token)
    except ValueError:
        return None
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def _load_run_payloads_for_week(*, trading_week: str, artifact_root: Path) -> list[dict[str, Any]]:
    runs_dir = artifact_root / "paper_mvp" / "runs"
    if not runs_dir.exists():
        return []

    out: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        trading_day = _parse_day(payload.get("timestamp"))
        if not trading_day:
            continue
        if _iso_week(trading_day) != trading_week:
            continue
        out.append(payload)
    return out


def _weekly_posture(*, total_runs: int, executed: int, expectancy_r: float | None, freshness_pct: float | None, reason_codes: Counter[str]) -> dict[str, Any]:
    hard_failures = {"NON_BYPASS_FAILED", "POLICY_VERSION_UNPINNED", "REPLAY_PARITY_FAILED"}
    tripped_hard = sorted(code for code in hard_failures if reason_codes.get(code, 0) > 0)

    blockers: list[dict[str, Any]] = []
    if tripped_hard:
        for code in tripped_hard:
            blockers.append({"code": code, "count": reason_codes[code]})

    if freshness_pct is not None and freshness_pct < 0.8:
        blockers.append({"code": "FEED_INSTABILITY", "count": 1, "detail": f"freshness_pct={freshness_pct}"})

    if expectancy_r is None or expectancy_r <= 0:
        blockers.append({"code": "NON_POSITIVE_EXPECTANCY", "count": 1})

    if total_runs < 10 or executed < 5:
        blockers.append({"code": "SAMPLE_TOO_SMALL", "count": 1, "detail": f"runs={total_runs},executed={executed}"})

    opportunities: list[dict[str, Any]] = []
    if expectancy_r is not None and expectancy_r > 0:
        opportunities.append({"code": "POSITIVE_EXPECTANCY", "detail": expectancy_r})
    if freshness_pct is not None and freshness_pct >= 0.8:
        opportunities.append({"code": "FEED_STABLE", "detail": freshness_pct})
    if total_runs >= 10 and executed >= 5:
        opportunities.append({"code": "SAMPLE_SUFFICIENT", "detail": f"runs={total_runs},executed={executed}"})

    if tripped_hard:
        recommendation = "NO_GO"
        rationale = "Hard-failure reason code(s) detected in weekly window."
    elif blockers:
        recommendation = "HOLD"
        rationale = "Readiness constraints remain; continue paper operations."
    else:
        recommendation = "GO"
        rationale = "Paper metrics stable with sufficient sample and no hard failures."

    return {
        "recommendation": recommendation,
        "rationale": rationale,
        "top_blockers": blockers[:3],
        "top_opportunities": opportunities[:3],
    }


def build_weekly_rollup(*, trading_week: str, runs: list[dict[str, Any]]) -> dict[str, Any]:
    total_runs = len(runs)
    accepted = sum(1 for row in runs if row.get("proposal_decision") == "accepted")
    executed = sum(1 for row in runs if row.get("execution_decision") == "executed")
    rejected = sum(1 for row in runs if row.get("proposal_decision") == "rejected")

    realized = [
        _f(row.get("pnl_r"))
        for row in runs
        if row.get("execution_decision") == "executed" and _f(row.get("pnl_r")) is not None
    ]
    realized_values = [v for v in realized if v is not None]

    expectancy_r = round(sum(realized_values) / len(realized_values), 4) if realized_values else None
    wins = [v for v in realized_values if v > 0]
    losses = [v for v in realized_values if v < 0]
    win_rate = round(len(wins) / len(realized_values), 4) if realized_values else None
    if losses:
        profit_factor = round(sum(wins) / abs(sum(losses)), 4)
    elif wins:
        profit_factor = None
    else:
        profit_factor = None

    reject_counter: Counter[str] = Counter()
    feed_reason_counter: Counter[str] = Counter()
    feed_state_counter: Counter[str] = Counter()
    reason_codes: Counter[str] = Counter()
    for row in runs:
        for code in row.get("decision_reason_codes") or []:
            if isinstance(code, str) and code:
                reason_codes[code] += 1

        if row.get("proposal_decision") != "accepted":
            for code in row.get("decision_reason_codes") or []:
                if isinstance(code, str) and code:
                    reject_counter[code] += 1

        feed_state = row.get("feed_state")
        if isinstance(feed_state, str) and feed_state:
            feed_state_counter[feed_state] += 1

        for code in row.get("feed_reason_codes") or []:
            if isinstance(code, str) and code:
                feed_reason_counter[code] += 1
                reason_codes[code] += 1

    ok_feeds = feed_state_counter.get("ok", 0)
    freshness_pct = round(ok_feeds / total_runs, 4) if total_runs else None

    gap_hits = sum(v for k, v in feed_reason_counter.items() if "GAP" in k)
    rate_limit_hits = sum(v for k, v in feed_reason_counter.items() if "RATE_LIMIT" in k)
    gap_rate = round(gap_hits / total_runs, 4) if total_runs else None
    rate_limit_rate = round(rate_limit_hits / total_runs, 4) if total_runs else None

    posture = _weekly_posture(
        total_runs=total_runs,
        executed=executed,
        expectancy_r=expectancy_r,
        freshness_pct=freshness_pct,
        reason_codes=reason_codes,
    )

    return {
        "week": trading_week,
        "runs_total": total_runs,
        "accepted": accepted,
        "executed": executed,
        "rejected": rejected,
        "expectancy_r": expectancy_r,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "reject_reason_distribution": dict(sorted(reject_counter.items())),
        "feed_health": {
            "freshness_pct": freshness_pct,
            "gap_rate": gap_rate,
            "rate_limit_rate": rate_limit_rate,
            "feed_state_distribution": dict(sorted(feed_state_counter.items())),
            "feed_reason_distribution": dict(sorted(feed_reason_counter.items())),
        },
        "posture": posture,
    }


def persist_weekly_rollup(*, trading_week: str, artifact_root: Path | None = None) -> tuple[dict[str, Any], Path]:
    root = artifact_root or Path(os.getenv("LS_ARTIFACT_ROOT", "artifacts"))
    runs = _load_run_payloads_for_week(trading_week=trading_week, artifact_root=root)
    payload = build_weekly_rollup(trading_week=trading_week, runs=runs)

    path = root / "paper_mvp" / "weekly" / f"{trading_week}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return payload, path
