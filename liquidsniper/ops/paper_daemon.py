from __future__ import annotations

import hashlib
import json
import math
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


def _exchange_time_offset_ms() -> int:
    raw = os.getenv("LIQUIDSNIPER_EXCHANGE_TIME_OFFSET_MS", "0").strip()
    try:
        return int(raw)
    except ValueError:
        return 0


def _lane_bankroll(strategy: str) -> float:
    key = f"LIQUIDSNIPER_PAPER_BANKROLL_USD_{strategy.upper()}"
    raw = os.getenv(key)
    if raw and raw.strip():
        try:
            return float(raw)
        except ValueError:
            pass
    return float(os.getenv("LIQUIDSNIPER_PAPER_BANKROLL_USD", "2000"))


def _base_tick_index(now: datetime, *, offset_ms: int = 0) -> int:
    adjusted = now + timedelta(milliseconds=offset_ms)
    return int(adjusted.timestamp()) // BASE_TICK_SECONDS


def _lane_should_run(*, strategy: str, tick_index: int) -> bool:
    return (tick_index % LANE_TICK_DIVISOR.get(strategy, 1)) == 0


def _seconds_until_next_base_tick(now: datetime, *, offset_ms: int = 0) -> int:
    adjusted = now + timedelta(milliseconds=offset_ms)
    elapsed = int(adjusted.timestamp()) % BASE_TICK_SECONDS
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


def _interval_minutes(tf: str) -> int:
    token = _interval_for(tf)
    amount = int(token[:-1])
    unit = token[-1]
    if unit == "m":
        return amount
    if unit == "h":
        return amount * 60
    if unit == "d":
        return amount * 60 * 24
    if unit == "w":
        return amount * 60 * 24 * 7
    raise ValueError(f"unsupported timeframe: {tf}")


def _target_candle_window(*, now: datetime, tf_minutes: int, offset_ms: int = 0) -> tuple[datetime, datetime]:
    tf_seconds = max(60, int(tf_minutes) * 60)
    adjusted_epoch = int((now + timedelta(milliseconds=offset_ms)).timestamp())
    target_close_epoch = adjusted_epoch - (adjusted_epoch % tf_seconds)
    target_open_epoch = target_close_epoch - tf_seconds
    return (
        datetime.fromtimestamp(target_open_epoch, tz=timezone.utc),
        datetime.fromtimestamp(target_close_epoch, tz=timezone.utc),
    )


def _select_candle_by_open_time(candles: list[dict[str, object]], *, target_open: datetime) -> dict[str, object] | None:
    for candle in candles:
        if candle.get("open_time") == target_open:
            return candle
    return None


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


def _sign(value: float, *, eps: float = 1e-12) -> float:
    if value > eps:
        return 1.0
    if value < -eps:
        return -1.0
    return 0.0


def _compute_htf_chop_components(closes: list[float], highs: list[float], lows: list[float], *, lookback: int = 14) -> dict[str, float]:
    n = max(2, int(lookback))
    if len(closes) < (n + 1) or len(highs) < n or len(lows) < n:
        return {"ci": 100.0, "er": 100.0, "norm": 100.0}

    c = [float(x) for x in closes[-(n + 1):]]
    h = [float(x) for x in highs[-n:]]
    l = [float(x) for x in lows[-n:]]
    eps = 1e-9

    tr_sum = 0.0
    for i in range(1, len(c)):
        prev_close = c[i - 1]
        high_i = h[i - 1]
        low_i = l[i - 1]
        tr_sum += max(high_i - low_i, abs(high_i - prev_close), abs(low_i - prev_close))

    span = max(max(h) - min(l), eps)
    ci = 100.0 * (0.0 if tr_sum <= eps else (max(0.0, math.log10(tr_sum / span)) / max(math.log10(float(n)), eps)))

    path = sum(abs(c[i] - c[i - 1]) for i in range(1, len(c)))
    er = abs(c[-1] - c[0]) / max(path, eps)
    er_chop = 100.0 * (1.0 - er)

    w_ci = float(os.getenv("LIQUIDSNIPER_HTF_CHOP_W_CI", "0.7"))
    w_er = float(os.getenv("LIQUIDSNIPER_HTF_CHOP_W_ER", "0.3"))
    norm = max(0.0, min(100.0, (w_ci * ci) + (w_er * er_chop)))
    return {
        "ci": round(max(0.0, min(100.0, ci)), 4),
        "er": round(max(0.0, min(100.0, er_chop)), 4),
        "norm": round(norm, 4),
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
        target_close_ts = str(snapshot.get("target_close_ts") or "")
        try:
            current = snapshot_builder(
                symbol,
                now=probe_now,
                cycle_count=cycle_count,
                policy=policy,
                target_close_ts=target_close_ts,
            )
        except TypeError:
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


def _build_market_snapshot(
    symbol: str,
    *,
    now: datetime,
    cycle_count: int,
    policy: ProfilePolicy,
    target_close_ts: str | None = None,
) -> dict[str, object]:
    data_source = os.getenv("LIQUIDSNIPER_DATA_SOURCE", "binance").strip().lower()
    if data_source == "mock":
        seed = _score_seed(f"snapshot:{symbol}:{now.isoformat()}:{cycle_count}:{policy.profile_id}")
        tf_minutes = 5 if policy.profile_id in {"I", "C"} else 15
        offset_ms = _exchange_time_offset_ms()
        target_open_dt, target_close_dt = _target_candle_window(now=now, tf_minutes=tf_minutes, offset_ms=offset_ms)
        candle_ts = target_close_dt.isoformat()
        side = "buy" if (seed[5] % 2 == 0) else "sell"
        bos_choch = (seed[3] % 10) < 8
        bias = compute_bias(profile_id=policy.profile_id, side=side, bos_choch=bos_choch)
        entry = round(100 + (seed[3] / 255.0) * 200, 4)
        nearest = round(entry * (0.998 if side == "buy" else 1.002), 4)
        htf_chop_norm = round(35 + (seed[1] / 255.0) * 35, 2)
        strict_retest = (seed[2] % 10) < 8
        return {
            "side": side,
            "entry": entry,
            "candle_ts": candle_ts,
            "candle_closed": (seed[0] % 10) < 8,
            "target_open_ts": target_open_dt.isoformat(),
            "target_close_ts": target_close_dt.isoformat(),
            "matched_candle_open_ts": target_open_dt.isoformat(),
            "exchange_offset_ms": int(offset_ms),
            "htf_chop": htf_chop_norm,
            "htf_chop_ci": htf_chop_norm,
            "htf_chop_er": htf_chop_norm,
            "htf_chop_norm": htf_chop_norm,
            "htf_chop_penalty": 0.0,
            "sr_first_retest": strict_retest,
            "sr_retest_mode": "strict" if strict_retest else "none",
            "sr_near_retest_used": False,
            "sr_penalty": 0.0,
            "breakout_window_ok": bool(bos_choch),
            "sr_distance_bps": 20.0,
            "bos_choch": bos_choch,
            "secondary_hits": int(seed[4] % 5),
            "bias_snapshot": {"direction": bias.direction, "mechanism": bias.mechanism, "profile_id": policy.profile_id, "votes": {}},
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

    tf_minutes = _interval_minutes(entry_tf)
    offset_ms = _exchange_time_offset_ms()
    if target_close_ts:
        target_close_dt = datetime.fromisoformat(target_close_ts)
        target_open_dt = target_close_dt - timedelta(minutes=tf_minutes)
    else:
        target_open_dt, target_close_dt = _target_candle_window(now=now, tf_minutes=tf_minutes, offset_ms=offset_ms)

    target_candle = _select_candle_by_open_time(c_entry, target_open=target_open_dt)

    last_entry = c_entry[-1]
    close_entry = float(target_candle["close"] if target_candle is not None else last_entry["close"])
    candle_ts = target_close_dt.isoformat()
    candle_closed = bool(target_candle is not None and now >= target_close_dt)

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

    chop_components = _compute_htf_chop_components(
        closes_htf,
        [float(c["high"]) for c in c_htf],
        [float(c["low"]) for c in c_htf],
        lookback=int(os.getenv("LIQUIDSNIPER_HTF_CHOP_LOOKBACK", "14")),
    )
    htf_chop = float(chop_components["norm"])

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
    sr_first_retest_eligible = bool(sr_query.get("first_retest_eligible"))
    sr_strict_ok = sr_first_retest_eligible and sr_distance_bps <= float(policy.sr_retest_bps_max)
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

    breakout_window_ok = bool(bos_choch)
    near_lane_allowed = policy.profile_id in {"I", "C"}
    near_band_ok = float(policy.sr_retest_bps_max) < sr_distance_bps <= float(policy.sr_retest_near_bps_max)
    sr_near_retest_used = bool((not sr_strict_ok) and near_lane_allowed and breakout_regime and breakout_window_ok and near_band_ok and sr_first_retest_eligible)
    sr_first_retest = bool(sr_strict_ok or sr_near_retest_used)
    sr_retest_mode = "strict" if sr_strict_ok else ("near_breakout" if sr_near_retest_used else "none")
    sr_penalty = 0.0
    if sr_near_retest_used:
        denom = max(float(policy.sr_retest_near_bps_max) - float(policy.sr_retest_bps_max), 1e-9)
        ratio = max(0.0, min(1.0, (sr_distance_bps - float(policy.sr_retest_bps_max)) / denom))
        sr_penalty = ratio * float(policy.sr_near_penalty_max)

    htf_chop_penalty = 0.0
    if htf_chop > float(policy.htf_chop_soft_max):
        denom = max(float(policy.htf_chop_hard_max) - float(policy.htf_chop_soft_max), 1e-9)
        ratio = max(0.0, min(1.0, (htf_chop - float(policy.htf_chop_soft_max)) / denom))
        htf_chop_penalty = ratio * float(policy.htf_chop_penalty_max)

    nearest_zone = nearest_support_obj if side == "buy" else nearest_resistance_obj
    nearest_zone_mid = float((nearest_zone or {}).get("bounds", {}).get("mid") or close_entry)
    v_htf = _sign(ema20_htf - ema50_htf)
    v_itf = _sign(ema20_itf - ema50_itf)
    v_structure = _sign((1.0 if bos_choch else -1.0) if side == "buy" else (-1.0 if bos_choch else 1.0))
    v_sr_context = _sign((close_entry - nearest_zone_mid) if side == "buy" else (nearest_zone_mid - close_entry))
    swing_votes = {"v_htf": v_htf, "v_itf": v_itf, "v_structure": v_structure, "v_sr_context": v_sr_context}

    bias = compute_bias(
        profile_id=policy.profile_id,
        side=side,
        bos_choch=bos_choch,
        swing_votes=swing_votes,
        swing_bias_neutral_band=policy.swing_bias_neutral_band,
    )

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
        "target_open_ts": target_open_dt.isoformat(),
        "target_close_ts": target_close_dt.isoformat(),
        "matched_candle_open_ts": target_candle["open_time"].isoformat() if target_candle is not None else None,
        "exchange_offset_ms": int(offset_ms),
        "htf_chop": round(float(htf_chop), 4),
        "htf_chop_ci": float(chop_components["ci"]),
        "htf_chop_er": float(chop_components["er"]),
        "htf_chop_norm": round(float(htf_chop), 4),
        "htf_chop_penalty": round(float(htf_chop_penalty), 4),
        "sr_first_retest": bool(sr_first_retest),
        "sr_retest_mode": sr_retest_mode,
        "sr_near_retest_used": bool(sr_near_retest_used),
        "sr_penalty": round(float(sr_penalty), 4),
        "breakout_window_ok": bool(breakout_window_ok),
        "sr_distance_bps": round(float(sr_distance_bps), 4),
        "bos_choch": bool(bos_choch),
        "secondary_hits": int(secondary_hits),
        "bias_snapshot": {"direction": bias.direction, "mechanism": bias.mechanism, "profile_id": policy.profile_id, "votes": swing_votes},
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
            "first_retest_eligible": bool(sr_first_retest_eligible),
            "gate_retest_pass": bool(sr_first_retest),
            "retest_mode": sr_retest_mode,
            "near_retest_used": bool(sr_near_retest_used),
            "retest_bps_max": float(policy.sr_retest_bps_max),
            "retest_near_bps_max": float(policy.sr_retest_near_bps_max),
            "sr_penalty": round(float(sr_penalty), 4),
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
    score_total_raw = max(0.0, min(10.0, 6.0 + (secondary_hits * 0.7) - max(0.0, (htf_chop - 35.0) / 25.0) + (seed[0] / 2550.0)))
    score_penalty = float(market_snapshot.get("htf_chop_penalty") or 0.0) + float(market_snapshot.get("sr_penalty") or 0.0)
    score = round(max(0.0, min(10.0, score_total_raw - score_penalty)), 2)

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
        "score_total_raw": round(score_total_raw, 4),
        "score_total_adj": score,
        "htf_chop_penalty": round(float(market_snapshot.get("htf_chop_penalty") or 0.0), 4),
        "sr_penalty": round(float(market_snapshot.get("sr_penalty") or 0.0), 4),
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
        htf_chop_mode = "soft_hard"
        htf_chop_soft_effective = float(profile_policy.htf_chop_soft_max)
        htf_chop_hard_effective = float(profile_policy.htf_chop_hard_max)

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
            htf_chop_ci=float(snapshot.get("htf_chop_ci") or 100.0),
            htf_chop_er=float(snapshot.get("htf_chop_er") or 100.0),
            htf_chop_soft_max_effective=float(htf_chop_soft_effective),
            htf_chop_hard_max_effective=float(htf_chop_hard_effective),
            htf_chop_mode=htf_chop_mode,
            htf_chop_penalty=float(snapshot.get("htf_chop_penalty") or 0.0),
            sr_first_retest=bool(snapshot["sr_first_retest"]),
            sr_distance_bps=float(snapshot.get("sr_distance_bps") or 0.0),
            sr_retest_mode=str(snapshot.get("sr_retest_mode") or "strict"),
            sr_near_retest_used=bool(snapshot.get("sr_near_retest_used")),
            sr_penalty=float(snapshot.get("sr_penalty") or 0.0),
            breakout_regime=bool(snapshot.get("breakout_regime")),
            breakout_window_ok=bool(snapshot.get("breakout_window_ok")),
            bos_choch=bool(snapshot["bos_choch"]),
            secondary_hits=int(snapshot["secondary_hits"]),
            swing_votes=(snapshot.get("bias_snapshot") or {}).get("votes") if isinstance(snapshot.get("bias_snapshot"), dict) else None,
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
        proposal["target_open_ts"] = snapshot.get("target_open_ts")
        proposal["target_close_ts"] = snapshot.get("target_close_ts")
        proposal["matched_candle_open_ts"] = snapshot.get("matched_candle_open_ts")
        proposal["exchange_offset_ms"] = int(snapshot.get("exchange_offset_ms") or 0)
        proposal["data_fetch_attempts"] = int(snapshot.get("data_fetch_attempts") or 0)
        proposal["breakout_regime"] = bool(breakout_regime)
        proposal["htf_chop_mode"] = htf_chop_mode
        proposal["htf_chop_threshold_effective"] = round(float(htf_chop_hard_effective), 4)
        proposal["htf_chop_soft_max"] = round(float(htf_chop_soft_effective), 4)
        proposal["htf_chop_hard_max"] = round(float(htf_chop_hard_effective), 4)
        proposal["htf_chop_ci"] = round(float(snapshot.get("htf_chop_ci") or 100.0), 4)
        proposal["htf_chop_er"] = round(float(snapshot.get("htf_chop_er") or 100.0), 4)
        proposal["htf_chop_norm"] = round(float(snapshot.get("htf_chop_norm") or snapshot.get("htf_chop") or 100.0), 4)
        proposal["sr_retest_mode"] = str(snapshot.get("sr_retest_mode") or "strict")
        proposal["sr_near_retest_used"] = bool(snapshot.get("sr_near_retest_used"))
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
    exchange_offset_ms = _exchange_time_offset_ms()
    while True:
        now = datetime.now(timezone.utc)
        tick_index = _base_tick_index(now, offset_ms=exchange_offset_ms)
        if last_tick_index is not None and tick_index == last_tick_index:
            if run_once:
                break
            time.sleep(max(1, _seconds_until_next_base_tick(now, offset_ms=exchange_offset_ms)))
            continue

        cycle_count += 1
        last_tick_index = tick_index

        if parallel_enabled:
            lane_flags = (
                {strategy: True for strategy in _parallel_strategies()}
                if run_once
                else {strategy: _lane_should_run(strategy=strategy, tick_index=tick_index) for strategy in _parallel_strategies()}
            )
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
            should_run = run_once or _lane_should_run(strategy=strategy, tick_index=tick_index)
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
        time.sleep(max(1, _seconds_until_next_base_tick(datetime.now(timezone.utc), offset_ms=exchange_offset_ms)))


if __name__ == "__main__":
    main()
