from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision
from liquidsniper.core.paper_artifacts import persist_run_artifact
from liquidsniper.core.mode_guard import enforce_startup_mode
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


class MarketDataUnavailable(RuntimeError):
    pass


def _interval_for(tf: str) -> str:
    token = tf.strip().lower()
    mapping = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
    }
    if token not in mapping:
        raise ValueError(f"unsupported timeframe: {tf}")
    return mapping[token]


def _ema(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    if period <= 1:
        return values[-1]
    alpha = 2.0 / (period + 1.0)
    ema_val = values[0]
    for v in values[1:]:
        ema_val = alpha * v + (1.0 - alpha) * ema_val
    return float(ema_val)


def _fetch_klines(symbol: str, interval: str, *, limit: int = 120) -> list[dict[str, object]]:
    qs = urllib.parse.urlencode({"symbol": symbol.upper(), "interval": interval, "limit": int(limit)})
    base = os.getenv("LIQUIDSNIPER_MARKETDATA_BASE", "https://data-api.binance.vision").rstrip("/")
    url = f"{base}/api/v3/klines?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "LiquidSniper/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            if int(getattr(resp, "status", 200)) != 200:
                raise MarketDataUnavailable(f"BINANCE_HTTP_{getattr(resp, 'status', 'ERR')}")
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise MarketDataUnavailable(f"BINANCE_FETCH_FAILED:{symbol}:{interval}") from exc

    if not isinstance(payload, list) or len(payload) < 60:
        raise MarketDataUnavailable(f"BINANCE_INSUFFICIENT_CANDLES:{symbol}:{interval}")

    out: list[dict[str, object]] = []
    for row in payload:
        if not isinstance(row, list) or len(row) < 7:
            continue
        out.append(
            {
                "open_time": datetime.fromtimestamp(int(row[0]) / 1000, tz=timezone.utc),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "close_time": datetime.fromtimestamp(int(row[6]) / 1000, tz=timezone.utc),
            }
        )

    if len(out) < 60:
        raise MarketDataUnavailable(f"BINANCE_PARSED_CANDLES_INSUFFICIENT:{symbol}:{interval}")
    return out


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
    data_source = os.getenv("LIQUIDSNIPER_DATA_SOURCE", "binance").strip().lower()
    if data_source == "mock":
        seed = _score_seed(f"snapshot:{symbol}:{now.isoformat()}:{cycle_count}:{policy.profile_id}")
        tf_minutes = 5 if policy.profile_id in {"I", "C"} else 15
        candle_ts = _floor_candle_ts(now, tf_minutes)
        side = "buy" if (seed[5] % 2 == 0) else "sell"
        return {
            "side": side,
            "entry": round(100 + (seed[3] / 255.0) * 200, 4),
            "candle_ts": candle_ts,
            "candle_closed": (seed[0] % 10) < 8,
            "htf_chop": round(35 + (seed[1] / 255.0) * 35, 2),
            "sr_first_retest": (seed[2] % 10) < 8,
            "bos_choch": (seed[3] % 10) < 8,
            "secondary_hits": int(seed[4] % 5),
            "data_source": "mock",
        }

    i15 = _interval_for("15m")
    i1h = _interval_for("1h")
    i4h = _interval_for("4h")

    c15 = _fetch_klines(symbol, i15, limit=120)
    c1h = _fetch_klines(symbol, i1h, limit=120)
    c4h = _fetch_klines(symbol, i4h, limit=120)

    last15 = c15[-1]
    close15 = float(last15["close"])
    candle_ts = str(last15["close_time"].isoformat())
    candle_closed = now >= last15["close_time"]

    closes15 = [float(c["close"]) for c in c15]
    closes1h = [float(c["close"]) for c in c1h]
    closes4h = [float(c["close"]) for c in c4h]

    ema20_1h = _ema(closes1h[-60:], 20)
    ema50_1h = _ema(closes1h[-60:], 50)
    ema20_4h = _ema(closes4h[-60:], 20)
    ema50_4h = _ema(closes4h[-60:], 50)

    if ema20_1h > ema50_1h and ema20_4h > ema50_4h:
        side = "buy"
    elif ema20_1h < ema50_1h and ema20_4h < ema50_4h:
        side = "sell"
    else:
        side = "buy"

    # Chop proxy: path inefficiency on 1H closes (higher => choppier).
    path = sum(abs(closes1h[i] - closes1h[i - 1]) for i in range(1, len(closes1h[-32:])))
    net = abs(closes1h[-1] - closes1h[-32]) if len(closes1h) >= 32 else abs(closes1h[-1] - closes1h[0])
    htf_chop = 100.0 if net <= 1e-9 else min(100.0, (path / net) * 25.0)

    highs1h = [float(c["high"]) for c in c1h]
    lows1h = [float(c["low"]) for c in c1h]
    if side == "buy":
        level = max(highs1h[-30:-3])
        sr_first_retest = abs(close15 - level) / max(level, 1e-9) <= 0.0045
        bos_choch = close15 > max(float(c["high"]) for c in c15[-16:-1])
    else:
        level = min(lows1h[-30:-3])
        sr_first_retest = abs(close15 - level) / max(level, 1e-9) <= 0.0045
        bos_choch = close15 < min(float(c["low"]) for c in c15[-16:-1])

    ema20_15 = _ema(closes15[-60:], 20)
    ema50_15 = _ema(closes15[-60:], 50)
    secondary_hits = 0
    if side == "buy":
        secondary_hits += int(close15 > ema20_15)
        secondary_hits += int(close15 > ema50_15)
        secondary_hits += int(closes1h[-1] > ema20_1h)
        secondary_hits += int(closes4h[-1] > ema20_4h)
    else:
        secondary_hits += int(close15 < ema20_15)
        secondary_hits += int(close15 < ema50_15)
        secondary_hits += int(closes1h[-1] < ema20_1h)
        secondary_hits += int(closes4h[-1] < ema20_4h)

    return {
        "side": side,
        "entry": round(close15, 6),
        "candle_ts": candle_ts,
        "candle_closed": candle_closed,
        "htf_chop": round(float(htf_chop), 4),
        "sr_first_retest": bool(sr_first_retest),
        "bos_choch": bool(bos_choch),
        "secondary_hits": int(secondary_hits),
        "data_source": "binance",
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
    side = str(market_snapshot.get("side") or "buy")
    entry = _as_float(market_snapshot.get("entry"), 0.0)
    if entry <= 0:
        raise MarketDataUnavailable(f"INVALID_ENTRY_PRICE:{symbol}")

    # Score is market-feature-derived with a small deterministic tie-breaker.
    secondary_hits = int(market_snapshot.get("secondary_hits") or 0)
    htf_chop = float(market_snapshot.get("htf_chop") or 100.0)
    score = round(max(0.0, min(10.0, 6.0 + (secondary_hits * 0.7) - max(0.0, (htf_chop - 35.0) / 25.0) + (seed[0] / 2550.0))), 2)

    risk_usd = float(os.getenv("LIQUIDSNIPER_RISK_USD_PER_TRADE", "25"))
    pnl_usd = round(((seed[2] - 128) / 128.0) * risk_usd * 0.20, 2)

    trace_id = f"paper-{now_iso.replace(':', '').replace('-', '')}-{symbol.lower()}"
    idempotency_key = f"paper-{profile_policy.profile_id}-{symbol}-{market_snapshot['candle_ts']}"
    intent_id = str(uuid5(NAMESPACE_URL, idempotency_key))

    strategy_id = {"I": "intraday", "C": "scalp", "S": "swing"}.get(profile_policy.profile_id, "intraday")

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
            "strategy_id": strategy_id,
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

        try:
            snapshot = _build_market_snapshot(symbol, now=now, cycle_count=cycle_count, policy=profile_policy)
        except MarketDataUnavailable as exc:
            blocked += 1
            trace_id = f"paper-{now.isoformat().replace(':', '').replace('-', '')}-{symbol.lower()}"
            reject_proposal = {
                "trace_id": trace_id,
                "policy_version": profile_policy.policy_version,
                "rulebook_ref": "TRADING_STRATEGY_PLAYBOOK_V1",
                "mode": "paper",
                "symbol": symbol,
                "direction": "buy",
                "entry": None,
                "stop_loss_initial": None,
                "tp_levels": [],
                "tp_plan": [],
                "candle_timestamp": None,
                "gate_checks": {"data": {"ok": False, "reason": str(exc)}},
                "policy_snapshot": profile_policy.snapshot(),
                "decision_reason_codes": ["DATA_UNAVAILABLE"],
            }
            persist_run_artifact(reject_proposal, {"decision": "blocked", "reason_codes": ["DATA_UNAVAILABLE"]})
            continue

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
            persist_run_artifact(proposal, {"decision": "blocked", "reason_codes": list(out.get("reason_codes") or gate.reason_codes)})
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
            persist_run_artifact(proposal, result)

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
    parallel_enabled = os.getenv("LIQUIDSNIPER_PAPER_PARALLEL", "false").strip().lower() in {"1", "true", "yes"}
    enforce_startup_mode(parallel_enabled=parallel_enabled, mode=mode)
    if mode != "paper":
        raise RuntimeError("MODE_GUARD_PAPER_DAEMON_REQUIRES_PAPER")

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
