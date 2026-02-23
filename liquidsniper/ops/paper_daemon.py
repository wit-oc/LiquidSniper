from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision
from liquidsniper.core.paper_artifacts import persist_run_artifact
from liquidsniper.core.mode_guard import enforce_startup_mode
from liquidsniper.core.db import init_db
from liquidsniper.core.sr_engine_v2 import build_zones_for_tf, nearest_sr_query, persist_sr_state
from liquidsniper.core.paper_policy import (
    ProfilePolicy,
    ThrottleState,
    compute_bias,
    count_active_risk_positions,
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


def _symbols_for_strategy(strategy: str) -> list[str]:
    key = f"LIQUIDSNIPER_SYMBOLS_{strategy.upper()}"
    raw = os.getenv(key)
    if raw:
        out = [x.strip().upper() for x in raw.split(",") if x.strip()]
        if out:
            return out
    return _symbols()


def _strategy_profile_id(strategy: str) -> str:
    mapping = {"scalp": "C", "intraday": "I", "swing": "S"}
    return mapping.get(strategy, "I")


def _parallel_enabled() -> bool:
    feature = os.getenv("LIQUIDSNIPER_FEATURE_PAPER_PARALLEL", "false").strip().lower() in {"1", "true", "yes", "on"}
    runtime = os.getenv("LIQUIDSNIPER_PAPER_PARALLEL", "false").strip().lower() in {"1", "true", "yes", "on"}
    return feature and runtime


def _parallel_strategies() -> list[str]:
    raw = os.getenv("LIQUIDSNIPER_PAPER_PARALLEL_STRATEGIES", "scalp,intraday,swing")
    allowed = {"scalp", "intraday", "swing"}
    items = [x.strip().lower() for x in raw.split(",") if x.strip()]
    uniq = []
    seen = set()
    for s in items:
        if s in allowed and s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq or ["intraday"]


BASE_TICK_SECONDS = 5 * 60
LANE_TICK_DIVISOR = {"scalp": 1, "intraday": 3, "swing": 12}


def _lane_bankroll(strategy: str) -> float:
    key = f"LIQUIDSNIPER_PAPER_BANKROLL_USD_{strategy.upper()}"
    raw = os.getenv(key)
    if raw and raw.strip():
        try:
            return float(raw)
        except ValueError:
            pass
    return float(os.getenv("LIQUIDSNIPER_PAPER_BANKROLL_USD", "2000"))


def _base_tick_index(now: datetime) -> int:
    return int(now.timestamp()) // BASE_TICK_SECONDS


def _lane_should_run(*, strategy: str, tick_index: int) -> bool:
    return (tick_index % LANE_TICK_DIVISOR.get(strategy, 1)) == 0


def _seconds_until_next_base_tick(now: datetime) -> int:
    elapsed = int(now.timestamp()) % BASE_TICK_SECONDS
    if elapsed == 0:
        return BASE_TICK_SECONDS
    return BASE_TICK_SECONDS - elapsed


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
        "1w": "1w",
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


def _nearest_level(price: float, levels: list[float]) -> float | None:
    if not levels:
        return None
    return min(levels, key=lambda lvl: abs(price - lvl))


def _promote_positions_to_be(state: ThrottleState, *, now: datetime, cycle_count: int) -> tuple[int, list[str]]:
    promoted = 0
    ids: list[str] = []
    for pos in state.open_positions:
        if pos.get("status") != "open" or pos.get("stop_state") != "initial":
            continue
        if int(pos.get("opened_cycle") or 0) < cycle_count:
            pos["stop_state"] = "be"
            pos["tp1_ts"] = now.isoformat()
            promoted += 1
            ids.append(str(pos.get("position_id") or ""))
    state.trades_open = sum(1 for p in state.open_positions if p.get("status") == "open")
    return promoted, ids


def _fetch_klines(symbol: str, interval: str, *, limit: int = 120) -> list[dict[str, object]]:
    qs = urllib.parse.urlencode({"symbol": symbol.upper(), "interval": interval, "limit": int(limit)})
    base = os.getenv("LIQUIDSNIPER_MARKETDATA_BASE", "https://data-api.binance.vision").rstrip("/")

    parsed = urllib.parse.urlparse(base)
    allowed_hosts_raw = os.getenv("LIQUIDSNIPER_MARKETDATA_ALLOWED_HOSTS", "data-api.binance.vision,api.binance.com")
    allowed_hosts = {h.strip().lower() for h in allowed_hosts_raw.split(",") if h.strip()}
    if parsed.scheme != "https" or not parsed.netloc or parsed.hostname is None or parsed.hostname.lower() not in allowed_hosts:
        raise MarketDataUnavailable("BINANCE_BASE_URL_INVALID")

    url = f"{base}/api/v3/klines?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "LiquidSniper/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:  # nosec B310
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


def _fetch_klines_with_retry(
    symbol: str,
    interval: str,
    *,
    limit: int = 120,
    sleep_fn=time.sleep,
) -> tuple[list[dict[str, object]], int]:
    attempts_max = max(1, int(os.getenv("LIQUIDSNIPER_DATA_FETCH_RETRY_ATTEMPTS", "3")))
    base_delay = max(1, int(os.getenv("LIQUIDSNIPER_DATA_FETCH_RETRY_BASE_MS", "250")))
    max_delay = max(base_delay, int(os.getenv("LIQUIDSNIPER_DATA_FETCH_RETRY_MAX_MS", "1000")))
    endpoint = os.getenv("LIQUIDSNIPER_MARKETDATA_BASE", "https://data-api.binance.vision").rstrip("/")

    last_exc: Exception | None = None
    for attempt in range(1, attempts_max + 1):
        try:
            candles = _fetch_klines(symbol, interval, limit=limit)
            return candles, attempt
        except MarketDataUnavailable as exc:
            last_exc = exc
            if attempt >= attempts_max:
                break
            backoff_ms = min(max_delay, base_delay * (2 ** (attempt - 1)))
            sleep_fn(backoff_ms / 1000.0)

    raise MarketDataUnavailable(
        f"DATA_FETCH_RETRY_EXHAUSTED:{symbol}:{interval}:attempts={attempts_max}:endpoint={endpoint}:last={last_exc}"
    )


def _classify_breakout_regime(
    *,
    side: str,
    closes_entry: list[float],
    highs_entry: list[float],
    lows_entry: list[float],
    ema20_itf: float,
    ema50_itf: float,
    ema20_htf: float,
    ema50_htf: float,
) -> tuple[bool, dict[str, object]]:
    if len(closes_entry) < 18 or len(highs_entry) < 18 or len(lows_entry) < 18:
        return False, {"range_break": False, "displacement_ok": False, "bias_aligned": False}

    close_now = float(closes_entry[-1])
    close_prev = float(closes_entry[-2])
    recent_high = max(float(v) for v in highs_entry[-17:-1])
    recent_low = min(float(v) for v in lows_entry[-17:-1])

    range_break = close_now > recent_high if side == "buy" else close_now < recent_low
    displacement_bps = abs(close_now - close_prev) / max(abs(close_prev), 1e-9) * 10_000.0
    displacement_min_bps = float(os.getenv("LIQUIDSNIPER_BREAKOUT_DISPLACEMENT_MIN_BPS", "12"))
    displacement_ok = displacement_bps >= displacement_min_bps
    bias_aligned = (ema20_itf > ema50_itf and ema20_htf > ema50_htf) if side == "buy" else (ema20_itf < ema50_itf and ema20_htf < ema50_htf)

    breakout = bool(range_break and displacement_ok and bias_aligned)
    return breakout, {
        "range_break": bool(range_break),
        "displacement_bps": round(displacement_bps, 4),
        "displacement_min_bps": round(displacement_min_bps, 4),
        "displacement_ok": bool(displacement_ok),
        "bias_aligned": bool(bias_aligned),
    }


def _confirm_candle_close_with_backoff(
    *,
    snapshot: dict[str, object],
    snapshot_builder,
    symbol: str,
    cycle_count: int,
    policy: ProfilePolicy,
    now: datetime,
    sleep_fn=time.sleep,
) -> tuple[dict[str, object], dict[str, object]]:
    schedule_sec = (5, 10, 15)
    attempts = 0
    elapsed = 0
    current = snapshot
    if bool(current.get("candle_closed")):
        return current, {"close_confirm_attempts": 0, "close_confirm_elapsed_sec": 0, "close_confirm_timeout": False}

    for step in schedule_sec:
        sleep_fn(step)
        elapsed += step
        attempts += 1
        probe_now = now + timedelta(seconds=elapsed)
        current = snapshot_builder(symbol, now=probe_now, cycle_count=cycle_count, policy=policy)
        if bool(current.get("candle_closed")):
            break

    timed_out = not bool(current.get("candle_closed"))
    return current, {
        "close_confirm_attempts": attempts,
        "close_confirm_elapsed_sec": elapsed,
        "close_confirm_timeout": timed_out,
    }


def _write_health(
    path: Path,
    *,
    status: str,
    loop_seconds: int,
    cycle_count: int,
    cycle_stats: dict[str, int],
    profile_policy: ProfilePolicy | None = None,
    lanes: list[dict[str, object]] | None = None,
) -> None:
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
    if profile_policy is not None:
        payload["profile_id"] = profile_policy.profile_id
    if lanes is not None:
        payload["lanes"] = lanes
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
        bos_choch = (seed[3] % 10) < 8
        bias = compute_bias(profile_id=policy.profile_id, side=side, bos_choch=bos_choch)
        entry = round(100 + (seed[3] / 255.0) * 200, 4)
        nearest = round(entry * (0.998 if side == "buy" else 1.002), 4)
        return {
            "side": side,
            "entry": entry,
            "candle_ts": candle_ts,
            "candle_closed": (seed[0] % 10) < 8,
            "htf_chop": round(35 + (seed[1] / 255.0) * 35, 2),
            "sr_first_retest": (seed[2] % 10) < 8,
            "sr_distance_bps": 20.0,
            "bos_choch": bos_choch,
            "secondary_hits": int(seed[4] % 5),
            "bias_snapshot": {"direction": bias.direction, "mechanism": bias.mechanism, "profile_id": policy.profile_id},
            "sr_context": {
                "nearest_htf_level": nearest,
                "nearest_itf_level": nearest,
                "distance_bps": 20.0,
                "first_retest_eligible": (seed[2] % 10) < 8,
            },
            "breakout_regime": bool(bos_choch),
            "breakout_diagnostics": {"range_break": bool(bos_choch), "displacement_ok": True, "bias_aligned": True},
            "data_fetch_attempts": 0,
            "close_confirm_attempts": 0,
            "close_confirm_elapsed_sec": 0,
            "data_source": "mock",
        }

    entry_tf = policy.ltf_trigger_tfs[0]
    i_entry = _interval_for(entry_tf)
    i_itf = _interval_for(policy.itf_tf)
    i_htf = _interval_for(policy.htf_anchor_tf)

    data_fetch_attempts = 0

    c_entry, attempts = _fetch_klines_with_retry(symbol, i_entry, limit=180)
    data_fetch_attempts += attempts
    c_itf, attempts = _fetch_klines_with_retry(symbol, i_itf, limit=180)
    data_fetch_attempts += attempts
    c_htf, attempts = _fetch_klines_with_retry(symbol, i_htf, limit=180)
    data_fetch_attempts += attempts

    last_entry = c_entry[-1]
    close_entry = float(last_entry["close"])
    candle_ts = str(last_entry["close_time"].isoformat())
    candle_closed = now >= last_entry["close_time"]

    closes_entry = [float(c["close"]) for c in c_entry]
    closes_itf = [float(c["close"]) for c in c_itf]
    closes_htf = [float(c["close"]) for c in c_htf]

    ema20_itf = _ema(closes_itf[-80:], 20)
    ema50_itf = _ema(closes_itf[-80:], 50)
    ema20_htf = _ema(closes_htf[-80:], 20)
    ema50_htf = _ema(closes_htf[-80:], 50)

    if ema20_itf > ema50_itf and ema20_htf > ema50_htf:
        side = "buy"
    elif ema20_itf < ema50_itf and ema20_htf < ema50_htf:
        side = "sell"
    else:
        side = "buy"

    # Chop proxy: path inefficiency on ITF closes (higher => choppier).
    segment = closes_itf[-32:] if len(closes_itf) >= 32 else closes_itf
    path = sum(abs(segment[i] - segment[i - 1]) for i in range(1, len(segment)))
    net = abs(segment[-1] - segment[0]) if len(segment) >= 2 else 0.0
    htf_chop = 100.0 if net <= 1e-9 else min(100.0, (path / net) * 25.0)

    sr_1h, a = _fetch_klines_with_retry(symbol, "1h", limit=220)
    data_fetch_attempts += a
    sr_4h, a = _fetch_klines_with_retry(symbol, "4h", limit=220)
    data_fetch_attempts += a
    sr_1d, a = _fetch_klines_with_retry(symbol, "1d", limit=220)
    data_fetch_attempts += a
    sr_1w, a = _fetch_klines_with_retry(symbol, "1w", limit=220)
    data_fetch_attempts += a

    sr_candles = {
        "1H": sr_1h,
        "4H": sr_4h,
        "1D": sr_1d,
        "1W": sr_1w,
    }
    sr_zones: list[dict[str, object]] = []
    sr_touches: list[dict[str, object]] = []
    for tf, tf_candles in sr_candles.items():
        z, t = build_zones_for_tf(symbol, tf, tf_candles)
        sr_zones.extend(z)
        sr_touches.extend(t)

    db_path = os.getenv("LIQUIDSNIPER_DB_PATH", "data/liquidsniper.sqlite")
    conn = init_db(db_path)
    try:
        persist_sr_state(conn, sr_zones, sr_touches)
    finally:
        conn.close()

    sr_query = nearest_sr_query(profile_id=policy.profile_id, side=side, entry=close_entry, zones=sr_zones)
    nearest_support_obj = sr_query.get("nearest_support") if isinstance(sr_query.get("nearest_support"), dict) else None
    nearest_resistance_obj = sr_query.get("nearest_resistance") if isinstance(sr_query.get("nearest_resistance"), dict) else None

    nearest_support = (nearest_support_obj or {}).get("bounds", {}).get("mid") if nearest_support_obj else None
    nearest_resistance = (nearest_resistance_obj or {}).get("bounds", {}).get("mid") if nearest_resistance_obj else None
    sr_distance_bps = float(sr_query.get("distance_bps") or 999999.0)
    sr_first_retest = bool(sr_query.get("first_retest_eligible")) and sr_distance_bps <= float(policy.sr_retest_bps_max)
    highs_entry = [float(c["high"]) for c in c_entry]
    lows_entry = [float(c["low"]) for c in c_entry]
    bos_choch = close_entry > max(highs_entry[-16:-1]) if side == "buy" else close_entry < min(lows_entry[-16:-1])

    breakout_regime, breakout_diag = _classify_breakout_regime(
        side=side,
        closes_entry=closes_entry,
        highs_entry=highs_entry,
        lows_entry=lows_entry,
        ema20_itf=ema20_itf,
        ema50_itf=ema50_itf,
        ema20_htf=ema20_htf,
        ema50_htf=ema50_htf,
    )

    bias = compute_bias(profile_id=policy.profile_id, side=side, bos_choch=bos_choch)

    ema20_entry = _ema(closes_entry[-80:], 20)
    ema50_entry = _ema(closes_entry[-80:], 50)
    secondary_hits = 0
    if side == "buy":
        secondary_hits += int(close_entry > ema20_entry)
        secondary_hits += int(close_entry > ema50_entry)
        secondary_hits += int(closes_itf[-1] > ema20_itf)
        secondary_hits += int(closes_htf[-1] > ema20_htf)
    else:
        secondary_hits += int(close_entry < ema20_entry)
        secondary_hits += int(close_entry < ema50_entry)
        secondary_hits += int(closes_itf[-1] < ema20_itf)
        secondary_hits += int(closes_htf[-1] < ema20_htf)

    return {
        "side": side,
        "entry": round(close_entry, 6),
        "candle_ts": candle_ts,
        "candle_closed": candle_closed,
        "htf_chop": round(float(htf_chop), 4),
        "sr_first_retest": bool(sr_first_retest),
        "sr_distance_bps": round(float(sr_distance_bps), 4),
        "bos_choch": bool(bos_choch),
        "secondary_hits": int(secondary_hits),
        "bias_snapshot": {"direction": bias.direction, "mechanism": bias.mechanism, "profile_id": policy.profile_id},
        "sr_context": {
            "entry_tf": entry_tf,
            "itf_tf": policy.itf_tf,
            "htf_tf": policy.htf_anchor_tf,
            "sr_anchor_tf": sr_query.get("sr_anchor_tf"),
            "sr_eligible_tfs": sr_query.get("sr_eligible_tfs"),
            "nearest_support": nearest_support_obj,
            "nearest_resistance": nearest_resistance_obj,
            "nearest_htf_level": nearest_support if side == "buy" else nearest_resistance,
            "nearest_itf_level": nearest_support if side == "buy" else nearest_resistance,
            "distance_bps": round(float(sr_distance_bps), 4),
            "first_retest_eligible": bool(sr_first_retest),
            "retest_bps_max": float(policy.sr_retest_bps_max),
            "gate_eligible": bool(sr_query.get("gate_eligible")),
            "reason_codes": list(sr_query.get("reason_codes") or []),
        },
        "breakout_regime": bool(breakout_regime),
        "breakout_diagnostics": breakout_diag,
        "data_fetch_attempts": int(data_fetch_attempts),
        "close_confirm_attempts": 0,
        "close_confirm_elapsed_sec": 0,
        "data_source": "binance",
    }


def _build_proposal(
    symbol: str,
    *,
    strategy: str,
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

    trace_id = f"paper-{now_iso.replace(':', '').replace('-', '')}-{strategy}-{symbol.lower()}"
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
        "bias_snapshot": market_snapshot.get("bias_snapshot") if isinstance(market_snapshot.get("bias_snapshot"), dict) else {},
        "sr_context": market_snapshot.get("sr_context") if isinstance(market_snapshot.get("sr_context"), dict) else {},
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


def _state_path(strategy: str | None = None) -> Path:
    root = Path(_artifact_root()) / "paper_mvp" / "state"
    if strategy:
        return root / "lanes" / f"{strategy}_execution_throttle_state.json"
    return root / "execution_throttle_state.json"


def _load_profile_policy_for(profile_id: str) -> ProfilePolicy:
    prev = os.getenv("LIQUIDSNIPER_PROFILE_ID")
    os.environ["LIQUIDSNIPER_PROFILE_ID"] = profile_id
    try:
        return load_profile_policy()
    finally:
        if prev is None:
            os.environ.pop("LIQUIDSNIPER_PROFILE_ID", None)
        else:
            os.environ["LIQUIDSNIPER_PROFILE_ID"] = prev


def _run_lane_cycle(
    *,
    strategy: str,
    symbols: list[str],
    cycle_count: int,
    now: datetime,
    boundary: ExecutionBoundary,
    profile_policy: ProfilePolicy,
    state_path: Path,
) -> dict[str, int]:
    state = load_throttle_state(state_path, now)

    attempted = 0
    executed = 0
    blocked = 0

    promoted_count, promoted_ids = _promote_positions_to_be(state, now=now, cycle_count=cycle_count)

    for symbol in symbols:
        attempted += 1

        try:
            snapshot = _build_market_snapshot(symbol, now=now, cycle_count=cycle_count, policy=profile_policy)
        except MarketDataUnavailable as exc:
            blocked += 1
            trace_id = f"paper-{now.isoformat().replace(':', '').replace('-', '')}-{strategy}-{symbol.lower()}"
            reject_proposal = {
                "trace_id": trace_id,
                "policy_version": profile_policy.policy_version,
                "rulebook_ref": "TRADING_STRATEGY_PLAYBOOK_V1",
                "mode": "paper",
                "strategy": strategy,
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

        close_confirm = {"close_confirm_attempts": 0, "close_confirm_elapsed_sec": 0, "close_confirm_timeout": False}
        if profile_policy.require_candle_close and str(snapshot.get("data_source") or "").lower() == "binance" and not bool(snapshot.get("candle_closed")):
            snapshot, close_confirm = _confirm_candle_close_with_backoff(
                snapshot=snapshot,
                snapshot_builder=_build_market_snapshot,
                symbol=symbol,
                cycle_count=cycle_count,
                policy=profile_policy,
                now=now,
                sleep_fn=time.sleep,
            )
            snapshot["close_confirm_attempts"] = int(close_confirm["close_confirm_attempts"])
            snapshot["close_confirm_elapsed_sec"] = int(close_confirm["close_confirm_elapsed_sec"])

        breakout_regime = bool(snapshot.get("breakout_regime"))
        htf_chop_mode = "breakout_softened" if breakout_regime else "strict"
        soften_points = float(os.getenv("LIQUIDSNIPER_HTF_CHOP_SOFTEN_POINTS", "8"))
        htf_chop_threshold_effective = min(100.0, float(profile_policy.htf_chop_max) + (soften_points if breakout_regime else 0.0))

        idempotency_key = f"paper-{profile_policy.profile_id}-{symbol}-{snapshot['candle_ts']}"

        gate = evaluate_gates(
            policy=profile_policy,
            state=state,
            now=now,
            idempotency_key=idempotency_key,
            side=str(snapshot.get("side") or "buy"),
            candle_closed=bool(snapshot["candle_closed"]),
            candle_ts=str(snapshot["candle_ts"]),
            htf_chop=float(snapshot["htf_chop"]),
            htf_chop_max_effective=float(htf_chop_threshold_effective),
            htf_chop_mode=htf_chop_mode,
            sr_first_retest=bool(snapshot["sr_first_retest"]),
            sr_distance_bps=float(snapshot.get("sr_distance_bps") or 0.0),
            bos_choch=bool(snapshot["bos_choch"]),
            secondary_hits=int(snapshot["secondary_hits"]),
        )

        proposal, policy = _build_proposal(
            symbol,
            strategy=strategy,
            now=now,
            cycle_count=cycle_count,
            profile_policy=profile_policy,
            market_snapshot=snapshot,
            gate_reason_codes=gate.reason_codes,
            gate_checks=gate.gate_checks,
        )
        proposal["strategy"] = strategy
        proposal["close_confirm_attempts"] = int(snapshot.get("close_confirm_attempts") or close_confirm["close_confirm_attempts"])
        proposal["close_confirm_elapsed_sec"] = int(snapshot.get("close_confirm_elapsed_sec") or close_confirm["close_confirm_elapsed_sec"])
        proposal["data_fetch_attempts"] = int(snapshot.get("data_fetch_attempts") or 0)
        proposal["breakout_regime"] = bool(breakout_regime)
        proposal["htf_chop_mode"] = htf_chop_mode
        proposal["htf_chop_threshold_effective"] = round(float(htf_chop_threshold_effective), 4)
        proposal["position_state_before"] = {
            "open_positions": state.trades_open,
            "active_risk_positions": count_active_risk_positions(state),
            "tp1_promotions_this_cycle": promoted_count,
            "promoted_position_ids": promoted_ids,
        }

        if bool(close_confirm.get("close_confirm_timeout")) and not bool(snapshot.get("candle_closed")):
            blocked += 1
            proposal["decision_reason_codes"] = ["CANDLE_CLOSE_TIMEOUT"]
            proposal["position_state_after"] = {
                "open_positions": state.trades_open,
                "active_risk_positions": count_active_risk_positions(state),
            }
            persist_run_artifact(proposal, {"decision": "blocked", "reason_codes": ["CANDLE_CLOSE_TIMEOUT"]})
            continue

        out = boundary.propose_trade(proposal, policy)
        decision = out.get("decision")
        if decision != "accepted":
            blocked += 1
            proposal["position_state_after"] = {
                "open_positions": state.trades_open,
                "active_risk_positions": count_active_risk_positions(state),
            }
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
            state.seen_idempotency_keys = (state.seen_idempotency_keys + [idempotency_key])[-2000:]
            state.open_positions.append(
                {
                    "position_id": out["proposal_id"],
                    "symbol": symbol,
                    "strategy": strategy,
                    "status": "open",
                    "stop_state": "initial",
                    "opened_cycle": cycle_count,
                    "tp1_ts": None,
                }
            )
            state.trades_open = sum(1 for p in state.open_positions if p.get("status") == "open")

            adapter_result = result.get("adapter_result") if isinstance(result.get("adapter_result"), dict) else {}
            realized_trade_pnl = _as_float(adapter_result.get("pnl_usd"), _as_float(proposal.get("pnl_usd"), 0.0))
            state.realized_pnl_today_usd = round(state.realized_pnl_today_usd + realized_trade_pnl, 8)
            proposal["position_state_after"] = {
                "open_positions": state.trades_open,
                "active_risk_positions": count_active_risk_positions(state),
            }
            persist_run_artifact(proposal, result)
        else:
            blocked += 1
            proposal["position_state_after"] = {
                "open_positions": state.trades_open,
                "active_risk_positions": count_active_risk_positions(state),
            }
            persist_run_artifact(proposal, result)

    persist_throttle_state(state_path, state)
    return {"attempted": attempted, "executed": executed, "blocked": blocked}


def run_cycle(*, loop_seconds: int, health_path: Path, cycle_count: int, boundary: ExecutionBoundary) -> None:
    now = datetime.now(timezone.utc)
    os.environ.setdefault("LS_ARTIFACT_ROOT", _artifact_root())
    profile_policy = load_profile_policy()
    stats = _run_lane_cycle(
        strategy={"I": "intraday", "C": "scalp", "S": "swing"}.get(profile_policy.profile_id, "intraday"),
        symbols=_symbols(),
        cycle_count=cycle_count,
        now=now,
        boundary=boundary,
        profile_policy=profile_policy,
        state_path=_state_path(),
    )

    _write_health(
        health_path,
        status="ok",
        loop_seconds=loop_seconds,
        cycle_count=cycle_count,
        cycle_stats=stats,
        profile_policy=profile_policy,
    )


def run_cycle_parallel(
    *,
    loop_seconds: int,
    health_path: Path,
    cycle_count: int,
    lane_boundaries: dict[str, ExecutionBoundary],
    lane_run_flags: dict[str, bool] | None = None,
) -> None:
    now = datetime.now(timezone.utc)
    os.environ.setdefault("LS_ARTIFACT_ROOT", _artifact_root())

    lanes_info: list[dict[str, object]] = []
    total = {"attempted": 0, "executed": 0, "blocked": 0, "skipped_preclose": 0}
    lane_run_flags = lane_run_flags or {}
    for strategy in _parallel_strategies():
        profile_id = _strategy_profile_id(strategy)
        policy = _load_profile_policy_for(profile_id)
        should_run = lane_run_flags.get(strategy, True)
        symbols = _symbols_for_strategy(strategy)
        if should_run:
            lane_stats = _run_lane_cycle(
                strategy=strategy,
                symbols=symbols,
                cycle_count=cycle_count,
                now=now,
                boundary=lane_boundaries[strategy],
                profile_policy=policy,
                state_path=_state_path(strategy),
            )
            skipped_preclose = 0
        else:
            lane_stats = {"attempted": 0, "executed": 0, "blocked": 0}
            skipped_preclose = len(symbols)

        lanes_info.append({
            "strategy": strategy,
            "profile_id": profile_id,
            "symbols": symbols,
            **lane_stats,
            "skipped_preclose": skipped_preclose,
        })
        total["attempted"] += lane_stats["attempted"]
        total["executed"] += lane_stats["executed"]
        total["blocked"] += lane_stats["blocked"]
        total["skipped_preclose"] += skipped_preclose

    _write_health(
        health_path,
        status="ok",
        loop_seconds=loop_seconds,
        cycle_count=cycle_count,
        cycle_stats=total,
        lanes=lanes_info,
    )


def main() -> None:
    mode = os.getenv("LIQUIDSNIPER_MODE", "paper").strip().lower()
    parallel_enabled = _parallel_enabled()
    enforce_startup_mode(parallel_enabled=parallel_enabled, mode=mode)
    if mode != "paper":
        raise RuntimeError("MODE_GUARD_PAPER_DAEMON_REQUIRES_PAPER")

    loop_seconds = int(os.getenv("LIQUIDSNIPER_LOOP_SECONDS", "60"))
    run_once = os.getenv("LIQUIDSNIPER_RUN_ONCE", "false").strip().lower() in {"1", "true", "yes"}
    health_path = Path(os.getenv("LIQUIDSNIPER_HEALTH_PATH", "/var/lib/liquidsniper/logs/paper_runner.health.json"))

    boundary = ExecutionBoundary()
    lane_boundaries: dict[str, ExecutionBoundary] = {
        strategy: ExecutionBoundary(starting_bankroll_usd=_lane_bankroll(strategy)) for strategy in _parallel_strategies()
    }

    cycle_count = 0
    last_tick_index: int | None = None
    while True:
        now = datetime.now(timezone.utc)
        tick_index = _base_tick_index(now)
        if last_tick_index is not None and tick_index == last_tick_index:
            if run_once:
                break
            time.sleep(max(1, _seconds_until_next_base_tick(now)))
            continue

        cycle_count += 1
        last_tick_index = tick_index

        if parallel_enabled:
            lane_flags = {strategy: _lane_should_run(strategy=strategy, tick_index=tick_index) for strategy in _parallel_strategies()}
            run_cycle_parallel(
                loop_seconds=BASE_TICK_SECONDS,
                health_path=health_path,
                cycle_count=cycle_count,
                lane_boundaries=lane_boundaries,
                lane_run_flags=lane_flags,
            )
        else:
            profile_policy = load_profile_policy()
            strategy = {"I": "intraday", "C": "scalp", "S": "swing"}.get(profile_policy.profile_id, "intraday")
            should_run = _lane_should_run(strategy=strategy, tick_index=tick_index)
            if should_run:
                run_cycle(loop_seconds=BASE_TICK_SECONDS, health_path=health_path, cycle_count=cycle_count, boundary=boundary)
            else:
                _write_health(
                    health_path,
                    status="ok",
                    loop_seconds=BASE_TICK_SECONDS,
                    cycle_count=cycle_count,
                    cycle_stats={"attempted": 0, "executed": 0, "blocked": 0, "skipped_preclose": len(_symbols())},
                    profile_policy=profile_policy,
                    lanes=[
                        {
                            "strategy": strategy,
                            "profile_id": profile_policy.profile_id,
                            "symbols": _symbols(),
                            "attempted": 0,
                            "executed": 0,
                            "blocked": 0,
                            "skipped_preclose": len(_symbols()),
                        }
                    ],
                )

        if run_once:
            break
        time.sleep(max(1, _seconds_until_next_base_tick(datetime.now(timezone.utc))))


if __name__ == "__main__":
    main()
