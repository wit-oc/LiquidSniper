from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision
from liquidsniper.core.paper_policy import (
    ProfilePolicy,
    ThrottleState,
    evaluate_gates,
    load_profile_policy,
    load_throttle_state,
    persist_throttle_state,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _symbols() -> list[str]:
    raw = os.getenv("LIQUIDSNIPER_SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,SUIUSDT")
    out = [x.strip().upper() for x in raw.split(",") if x.strip()]
    return out or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "SUIUSDT"]


def _artifact_root() -> str:
    return os.getenv("LS_ARTIFACT_ROOT") or os.getenv("LIQUIDSNIPER_ARTIFACT_ROOT") or "artifacts"


def _score_seed(text: str) -> bytes:
    return hashlib.sha256(text.encode("utf-8")).digest()


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _write_health(
    path: Path,
    *,
    status: str,
    loop_seconds: int,
    cycle_count: int,
    cycle_stats: dict[str, int],
    profile_policy: ProfilePolicy,
) -> None:
    payload = {
        "service": "paper-runner",
        "mode": "paper",
        "status": status,
        "loop_seconds": loop_seconds,
        "cycle_count": cycle_count,
        "profile_mode": os.getenv("LIQUIDSNIPER_PROFILE_MODE", "intraday_only"),
        "profile_id": profile_policy.profile_id,
        "symbols": _symbols(),
        "cycle_stats": cycle_stats,
        "updated_at": _utc_now(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _floor_candle_ts(now: datetime, tf_minutes: int) -> str:
    minute = (now.minute // tf_minutes) * tf_minutes
    floored = now.replace(minute=minute, second=0, microsecond=0)
    return floored.isoformat()


def _build_market_snapshot(symbol: str, *, now: datetime, cycle_count: int, policy: ProfilePolicy) -> dict[str, object]:
    seed = _score_seed(f"snapshot:{symbol}:{now.isoformat()}:{cycle_count}:{policy.profile_id}")
    tf_minutes = 5 if policy.profile_id in {"I", "C"} else 15
    candle_ts = _floor_candle_ts(now, tf_minutes)

    # Deterministic pseudo-market features. Candle-close is probabilistic but stable per input seed.
    candle_closed = (seed[0] % 10) < 8
    htf_chop = round(35 + (seed[1] / 255.0) * 35, 2)
    sr_first_retest = (seed[2] % 10) < 8
    bos_choch = (seed[3] % 10) < 8
    secondary_hits = int(seed[4] % 5)

    return {
        "candle_ts": candle_ts,
        "candle_closed": candle_closed,
        "htf_chop": htf_chop,
        "sr_first_retest": sr_first_retest,
        "bos_choch": bos_choch,
        "secondary_hits": secondary_hits,
    }


def _build_proposal(
    symbol: str,
    *,
    now: datetime,
    cycle_count: int,
    profile_policy: ProfilePolicy,
    market_snapshot: dict[str, object],
    gate_reason_codes: tuple[str, ...],
    gate_checks: dict[str, object],
) -> tuple[dict[str, object], PolicyDecision]:
    now_iso = now.isoformat()
    seed = _score_seed(f"{symbol}:{market_snapshot['candle_ts']}:{cycle_count}:{profile_policy.profile_id}")
    score = round(5.4 + (seed[0] / 255.0) * 4.2, 2)
    side = "buy" if (seed[1] % 2 == 0) else "sell"
    risk_usd = float(os.getenv("LIQUIDSNIPER_RISK_USD_PER_TRADE", "25"))
    pnl_usd = round(((seed[2] - 128) / 128.0) * risk_usd * 0.20, 2)

    trace_id = f"paper-{now_iso.replace(':', '').replace('-', '')}-{symbol.lower()}"
    entry = round(100 + (seed[3] / 255.0) * 200, 4)
    idempotency_key = f"paper-{profile_policy.profile_id}-{symbol}-{market_snapshot['candle_ts']}"
    intent_id = str(uuid5(NAMESPACE_URL, idempotency_key))

    proposal: dict[str, object] = {
        "trace_id": trace_id,
        "policy_version": profile_policy.policy_version,
        "rulebook_ref": "TRADING_STRATEGY_PLAYBOOK_V1",
        "mode": "paper",
        "symbol": symbol,
        "direction": side,
        "entry": entry,
        "stop_loss_initial": round(entry * (0.985 if side == "buy" else 1.015), 4),
        "tp_levels": [round(entry * 1.01, 4), round(entry * 1.02, 4)],
        "risk_usd": risk_usd,
        "pnl_usd": pnl_usd,
        "anchor_profile_id": profile_policy.profile_id,
        "htf_anchor_tf": profile_policy.htf_anchor_tf,
        "score_total": score,
        "score_gate_passed": score >= 6.0,
        "decision_tier": "high_priority" if score >= 8.5 else "publish_candidate",
        "feed_state": "ok",
        "feed_reason_codes": [],
        "candle_timestamp": market_snapshot["candle_ts"],
        "gate_checks": gate_checks,
        "policy_snapshot": profile_policy.snapshot(),
        "trade_intent": {
            "intent_id": intent_id,
            "ts": now_iso,
            "strategy_id": f"paper-mvp-{profile_policy.profile_id.lower()}-v1",
            "mode": "paper",
            "venue": "blofin",
            "symbol": symbol,
            "side": side,
            "order_type": "limit",
            "limit_price": str(entry),
            "size_notional_usd": str(round(risk_usd * 8, 2)),
            "time_in_force": "GTC",
            "max_slippage_bps": 25,
            "thesis": "profile-gated autonomous paper cycle",
            "idempotency_key": idempotency_key,
        },
    }

    if gate_reason_codes:
        proposal["decision_reason_codes"] = list(gate_reason_codes)

    policy = PolicyDecision(not gate_reason_codes, gate_reason_codes, trace_id, profile_policy.policy_version)
    return proposal, policy


def _state_path() -> Path:
    return Path(_artifact_root()) / "paper_mvp" / "state" / "execution_throttle_state.json"


def run_cycle(*, loop_seconds: int, health_path: Path, cycle_count: int, boundary: ExecutionBoundary) -> None:
    now = datetime.now(timezone.utc)
    os.environ.setdefault("LS_ARTIFACT_ROOT", _artifact_root())
    profile_policy = load_profile_policy()
    state_path = _state_path()
    state = load_throttle_state(state_path, now)

    attempted = 0
    executed = 0
    blocked = 0

    # A position is considered open for one cycle window to enforce one-open-position guard.
    state.trades_open = 0

    for symbol in _symbols():
        attempted += 1
        snapshot = _build_market_snapshot(symbol, now=now, cycle_count=cycle_count, policy=profile_policy)
        idempotency_key = f"paper-{profile_policy.profile_id}-{symbol}-{snapshot['candle_ts']}"

        gate = evaluate_gates(
            policy=profile_policy,
            state=state,
            now=now,
            idempotency_key=idempotency_key,
            candle_closed=bool(snapshot["candle_closed"]),
            candle_ts=str(snapshot["candle_ts"]),
            htf_chop=float(snapshot["htf_chop"]),
            sr_first_retest=bool(snapshot["sr_first_retest"]),
            bos_choch=bool(snapshot["bos_choch"]),
            secondary_hits=int(snapshot["secondary_hits"]),
        )

        proposal, policy = _build_proposal(
            symbol,
            now=now,
            cycle_count=cycle_count,
            profile_policy=profile_policy,
            market_snapshot=snapshot,
            gate_reason_codes=gate.reason_codes,
            gate_checks=gate.gate_checks,
        )

        out = boundary.propose_trade(proposal, policy)
        decision = out.get("decision")
        if decision != "accepted":
            blocked += 1
            continue

        result = boundary.execute_with_adapter(
            out["proposal_id"],
            lambda _: {"status": "paper_fill", "pnl_usd": proposal.get("pnl_usd", 0.0)},
        )
        if result.get("decision") == "executed":
            executed += 1
            state.executed_today += 1
            state.last_entry_ts = now.isoformat()
            state.trades_open = 1
            state.seen_idempotency_keys = (state.seen_idempotency_keys + [idempotency_key])[-2000:]

            adapter_result = result.get("adapter_result") if isinstance(result.get("adapter_result"), dict) else {}
            realized_trade_pnl = _as_float(adapter_result.get("pnl_usd"), _as_float(proposal.get("pnl_usd"), 0.0))
            state.realized_pnl_today_usd = round(state.realized_pnl_today_usd + realized_trade_pnl, 8)
        else:
            blocked += 1

    persist_throttle_state(state_path, state)

    _write_health(
        health_path,
        status="ok",
        loop_seconds=loop_seconds,
        cycle_count=cycle_count,
        cycle_stats={"attempted": attempted, "executed": executed, "blocked": blocked},
        profile_policy=profile_policy,
    )


def main() -> None:
    mode = os.getenv("LIQUIDSNIPER_MODE", "paper").strip().lower()
    if mode != "paper":
        raise RuntimeError("paper_daemon only supports LIQUIDSNIPER_MODE=paper")

    loop_seconds = int(os.getenv("LIQUIDSNIPER_LOOP_SECONDS", "60"))
    run_once = os.getenv("LIQUIDSNIPER_RUN_ONCE", "false").strip().lower() in {"1", "true", "yes"}
    health_path = Path(os.getenv("LIQUIDSNIPER_HEALTH_PATH", "/var/lib/liquidsniper/logs/paper_runner.health.json"))

    boundary = ExecutionBoundary()
    cycle_count = 0
    while True:
        cycle_count += 1
        run_cycle(loop_seconds=loop_seconds, health_path=health_path, cycle_count=cycle_count, boundary=boundary)
        if run_once:
            break
        time.sleep(max(1, loop_seconds))


if __name__ == "__main__":
    main()
