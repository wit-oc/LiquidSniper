from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision


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


def _write_health(path: Path, *, status: str, loop_seconds: int, cycle_count: int, cycle_stats: dict[str, int]) -> None:
    payload = {
        "service": "paper-runner",
        "mode": "paper",
        "status": status,
        "loop_seconds": loop_seconds,
        "cycle_count": cycle_count,
        "profile_mode": os.getenv("LIQUIDSNIPER_PROFILE_MODE", "intraday_only"),
        "symbols": _symbols(),
        "cycle_stats": cycle_stats,
        "updated_at": _utc_now(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _build_proposal(symbol: str, *, now_iso: str, cycle_count: int) -> tuple[dict[str, object], PolicyDecision]:
    profile_mode = os.getenv("LIQUIDSNIPER_PROFILE_MODE", "intraday_only").strip().lower()
    if profile_mode != "intraday_only":
        raise RuntimeError("paper daemon currently supports LIQUIDSNIPER_PROFILE_MODE=intraday_only")

    seed = _score_seed(f"{symbol}:{now_iso}:{cycle_count}")
    score = round(6.0 + (seed[0] / 255.0) * 4.0, 2)
    side = "buy" if (seed[1] % 2 == 0) else "sell"
    risk_usd = float(os.getenv("LIQUIDSNIPER_RISK_USD_PER_TRADE", "25"))
    pnl_usd = round(((seed[2] - 128) / 128.0) * risk_usd * 0.20, 2)

    trace_id = f"paper-{now_iso.replace(':', '').replace('-', '')}-{symbol.lower()}"
    intent_id = str(uuid4())
    entry = round(100 + (seed[3] / 255.0) * 200, 4)

    proposal: dict[str, object] = {
        "trace_id": trace_id,
        "policy_version": "v1",
        "rulebook_ref": "TRADING_STRATEGY_PLAYBOOK_V1",
        "mode": "paper",
        "symbol": symbol,
        "direction": side,
        "entry": entry,
        "stop_loss_initial": round(entry * (0.985 if side == "buy" else 1.015), 4),
        "tp_levels": [round(entry * 1.01, 4), round(entry * 1.02, 4)],
        "risk_usd": risk_usd,
        "pnl_usd": pnl_usd,
        "anchor_profile_id": "I",
        "htf_anchor_tf": "4H",
        "score_total": score,
        "score_gate_passed": score >= 6.0,
        "decision_tier": "high_priority" if score >= 8.5 else "publish_candidate",
        "feed_state": "ok",
        "feed_reason_codes": [],
        "trade_intent": {
            "intent_id": intent_id,
            "ts": now_iso,
            "strategy_id": "paper-mvp-intraday-v1",
            "mode": "paper",
            "venue": "blofin",
            "symbol": symbol,
            "side": side,
            "order_type": "limit",
            "limit_price": str(entry),
            "size_notional_usd": str(round(risk_usd * 8, 2)),
            "time_in_force": "GTC",
            "max_slippage_bps": 25,
            "thesis": "intraday autonomous paper cycle",
            "idempotency_key": f"paper-{intent_id}",
        },
    }

    policy = PolicyDecision(True, (), trace_id, "v1")
    return proposal, policy


def run_cycle(*, loop_seconds: int, health_path: Path, cycle_count: int, boundary: ExecutionBoundary) -> None:
    now_iso = _utc_now()
    os.environ.setdefault("LS_ARTIFACT_ROOT", _artifact_root())

    attempted = 0
    executed = 0
    blocked = 0
    for symbol in _symbols():
        attempted += 1
        proposal, policy = _build_proposal(symbol, now_iso=now_iso, cycle_count=cycle_count)
        out = boundary.propose_trade(proposal, policy)
        decision = out.get("decision")
        if decision != "accepted":
            blocked += 1
            continue
        result = boundary.execute_with_adapter(out["proposal_id"], lambda _: {"status": "paper_fill", "pnl_usd": proposal.get("pnl_usd", 0.0)})
        if result.get("decision") == "executed":
            executed += 1
        else:
            blocked += 1

    _write_health(
        health_path,
        status="ok",
        loop_seconds=loop_seconds,
        cycle_count=cycle_count,
        cycle_stats={"attempted": attempted, "executed": executed, "blocked": blocked},
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
