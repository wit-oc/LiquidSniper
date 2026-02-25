from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os


_PROFILE_DEFAULTS = {
    "S": {
        "htf_anchor_tf": "1D",
        "itf_tf": "4H",
        "ltf_trigger_tfs": ["1H", "15m"],
        "gate": {
            "require_candle_close": True,
            "htf_chop_soft_max": 62.0,
            "htf_chop_hard_max": 76.0,
            "htf_chop_penalty_max": 0.8,
            "require_sr_first_retest": True,
            "sr_retest_bps_max": 35.0,
            "sr_retest_near_bps_max": 35.0,
            "sr_near_penalty_max": 0.0,
            "breakout_relax_window_candles": 1,
            "swing_bias_neutral_band": 0.55,
            "min_secondary_confluence_hits": 2,
        },
    },
    "I": {
        "htf_anchor_tf": "4H",
        "itf_tf": "1H",
        "ltf_trigger_tfs": ["15m", "5m"],
        "gate": {
            "require_candle_close": True,
            "htf_chop_soft_max": 68.0,
            "htf_chop_hard_max": 82.0,
            "htf_chop_penalty_max": 1.0,
            "require_sr_first_retest": True,
            "sr_retest_bps_max": 18.0,
            "sr_retest_near_bps_max": 30.0,
            "sr_near_penalty_max": 0.7,
            "breakout_relax_window_candles": 1,
            "swing_bias_neutral_band": 0.55,
            "min_secondary_confluence_hits": 2,
        },
    },
    "C": {
        "htf_anchor_tf": "1H",
        "itf_tf": "15m",
        "ltf_trigger_tfs": ["5m", "1m"],
        "gate": {
            "require_candle_close": True,
            "htf_chop_soft_max": 72.0,
            "htf_chop_hard_max": 86.0,
            "htf_chop_penalty_max": 1.2,
            "require_sr_first_retest": True,
            "sr_retest_bps_max": 20.0,
            "sr_retest_near_bps_max": 35.0,
            "sr_near_penalty_max": 0.8,
            "breakout_relax_window_candles": 1,
            "swing_bias_neutral_band": 0.55,
            "min_secondary_confluence_hits": 1,
        },
    },
}


@dataclass(frozen=True)
class ProfilePolicy:
    profile_id: str
    htf_anchor_tf: str
    itf_tf: str
    ltf_trigger_tfs: tuple[str, ...]
    require_candle_close: bool
    htf_chop_soft_max: float
    htf_chop_hard_max: float
    htf_chop_penalty_max: float
    require_sr_first_retest: bool
    sr_retest_bps_max: float
    sr_retest_near_bps_max: float
    sr_near_penalty_max: float
    breakout_relax_window_candles: int
    swing_bias_neutral_band: float
    min_secondary_confluence_hits: int
    cooldown_seconds: int
    daily_max_trades: int
    daily_max_loss_usd: float
    max_active_risk_positions: int
    policy_version: str

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThrottleState:
    trading_day: str
    last_entry_ts: str | None
    trades_open: int
    executed_today: int
    realized_pnl_today_usd: float
    seen_idempotency_keys: list[str]
    open_positions: list[dict[str, Any]]

    @classmethod
    def empty(cls, trading_day: str) -> "ThrottleState":
        return cls(
            trading_day=trading_day,
            last_entry_ts=None,
            trades_open=0,
            executed_today=0,
            realized_pnl_today_usd=0.0,
            seen_idempotency_keys=[],
            open_positions=[],
        )


@dataclass(frozen=True)
class GateDecision:
    accepted: bool
    reason_codes: tuple[str, ...]
    gate_checks: dict[str, Any]


@dataclass(frozen=True)
class BiasDecision:
    direction: str
    mechanism: str


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return float(raw)


def _utc_day(now: datetime) -> str:
    return now.astimezone(timezone.utc).date().isoformat()


def count_active_risk_positions(state: ThrottleState) -> int:
    return sum(1 for p in state.open_positions if str(p.get("status", "open")) == "open" and str(p.get("stop_state", "initial")) != "be")


def compute_bias(
    *,
    profile_id: str,
    side: str,
    bos_choch: bool,
    swing_votes: dict[str, float] | None = None,
    swing_bias_neutral_band: float = 0.55,
) -> BiasDecision:
    expected = "long" if side == "buy" else "short"
    if profile_id != "S":
        if bos_choch:
            return BiasDecision(direction=expected, mechanism="bos_choch_confirmed")
        return BiasDecision(direction=expected, mechanism="ema_structure_proxy")

    votes = swing_votes or {}
    if votes:
        bias_conf = (
            0.45 * float(votes.get("v_htf", 0.0))
            + 0.30 * float(votes.get("v_itf", 0.0))
            + 0.15 * float(votes.get("v_structure", 0.0))
            + 0.10 * float(votes.get("v_sr_context", 0.0))
        )
        if abs(bias_conf) < max(0.0, float(swing_bias_neutral_band)):
            return BiasDecision(direction="neutral", mechanism="swing_weighted_neutral")
        return BiasDecision(direction=("long" if bias_conf > 0 else "short"), mechanism="swing_weighted_vote")

    if bos_choch:
        return BiasDecision(direction=expected, mechanism="bos_choch_confirmed")
    return BiasDecision(direction="neutral", mechanism="structure_unconfirmed")


def load_profile_policy() -> ProfilePolicy:
    profile_id = os.getenv("LIQUIDSNIPER_PROFILE_ID", "I").strip().upper()
    spec = _PROFILE_DEFAULTS.get(profile_id)
    if spec is None:
        raise RuntimeError(f"invalid LIQUIDSNIPER_PROFILE_ID: {profile_id}")

    gate = spec["gate"]
    min_secondary = _int_env("LIQUIDSNIPER_MIN_SECONDARY_HITS", int(gate["min_secondary_confluence_hits"]))
    if min_secondary < 0:
        raise RuntimeError("LIQUIDSNIPER_MIN_SECONDARY_HITS must be >= 0")

    daily_max_trades = _int_env("LIQUIDSNIPER_DAILY_MAX_TRADES", 4)
    if daily_max_trades <= 0:
        raise RuntimeError("LIQUIDSNIPER_DAILY_MAX_TRADES must be > 0")

    cooldown_seconds = _int_env("LIQUIDSNIPER_COOLDOWN_SECONDS", 900)
    if cooldown_seconds < 0:
        raise RuntimeError("LIQUIDSNIPER_COOLDOWN_SECONDS must be >= 0")

    daily_max_loss_usd = _float_env("LIQUIDSNIPER_MAX_DAILY_LOSS_USD", 500.0)
    if daily_max_loss_usd <= 0:
        raise RuntimeError("LIQUIDSNIPER_MAX_DAILY_LOSS_USD must be > 0")

    max_active_risk_positions = _int_env("LIQUIDSNIPER_MAX_ACTIVE_RISK_POSITIONS", 2)
    if max_active_risk_positions <= 0:
        raise RuntimeError("LIQUIDSNIPER_MAX_ACTIVE_RISK_POSITIONS must be > 0")

    return ProfilePolicy(
        profile_id=profile_id,
        htf_anchor_tf=str(spec["htf_anchor_tf"]),
        itf_tf=str(spec["itf_tf"]),
        ltf_trigger_tfs=tuple(str(x) for x in spec["ltf_trigger_tfs"]),
        require_candle_close=_bool_env("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", bool(gate["require_candle_close"])),
        htf_chop_soft_max=_float_env("LIQUIDSNIPER_HTF_CHOP_SOFT_MAX", float(gate["htf_chop_soft_max"])),
        htf_chop_hard_max=_float_env("LIQUIDSNIPER_HTF_CHOP_HARD_MAX", float(gate["htf_chop_hard_max"])),
        htf_chop_penalty_max=_float_env("LIQUIDSNIPER_HTF_CHOP_PENALTY_MAX", float(gate["htf_chop_penalty_max"])),
        require_sr_first_retest=_bool_env("LIQUIDSNIPER_REQUIRE_SR_FIRST_RETEST", bool(gate["require_sr_first_retest"])),
        sr_retest_bps_max=_float_env("LIQUIDSNIPER_SR_RETEST_BPS_MAX", float(gate["sr_retest_bps_max"])),
        sr_retest_near_bps_max=_float_env("LIQUIDSNIPER_SR_RETEST_NEAR_BPS_MAX", float(gate["sr_retest_near_bps_max"])),
        sr_near_penalty_max=_float_env("LIQUIDSNIPER_SR_NEAR_PENALTY_MAX", float(gate["sr_near_penalty_max"])),
        breakout_relax_window_candles=max(0, _int_env("LIQUIDSNIPER_BREAKOUT_RELAX_WINDOW_CANDLES", int(gate["breakout_relax_window_candles"]))),
        swing_bias_neutral_band=max(0.0, _float_env("LIQUIDSNIPER_SWING_BIAS_NEUTRAL_BAND", float(gate["swing_bias_neutral_band"]))),
        min_secondary_confluence_hits=min_secondary,
        cooldown_seconds=cooldown_seconds,
        daily_max_trades=daily_max_trades,
        daily_max_loss_usd=daily_max_loss_usd,
        max_active_risk_positions=max_active_risk_positions,
        policy_version=os.getenv("LIQUIDSNIPER_POLICY_VERSION", "v1").strip() or "v1",
    )


def load_throttle_state(path: Path, now: datetime) -> ThrottleState:
    trading_day = _utc_day(now)
    if not path.exists():
        return ThrottleState.empty(trading_day)

    raw = json.loads(path.read_text(encoding="utf-8"))
    open_positions = []
    for item in (raw.get("open_positions") or []):
        if not isinstance(item, dict):
            continue
        open_positions.append(
            {
                "position_id": str(item.get("position_id") or ""),
                "symbol": str(item.get("symbol") or ""),
                "strategy": str(item.get("strategy") or ""),
                "status": str(item.get("status") or "open"),
                "stop_state": str(item.get("stop_state") or "initial"),
                "opened_cycle": int(item.get("opened_cycle") or 0),
                "tp1_ts": item.get("tp1_ts"),
            }
        )
    state = ThrottleState(
        trading_day=str(raw.get("trading_day") or trading_day),
        last_entry_ts=raw.get("last_entry_ts"),
        trades_open=max(0, int(raw.get("trades_open") or 0)),
        executed_today=max(0, int(raw.get("executed_today") or 0)),
        realized_pnl_today_usd=float(raw.get("realized_pnl_today_usd") or 0.0),
        seen_idempotency_keys=[str(x) for x in (raw.get("seen_idempotency_keys") or []) if str(x)],
        open_positions=open_positions,
    )
    if state.trading_day != trading_day:
        return ThrottleState.empty(trading_day)
    state.trades_open = sum(1 for p in state.open_positions if str(p.get("status", "open")) == "open")
    return state


def persist_throttle_state(path: Path, state: ThrottleState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state.trades_open = sum(1 for p in state.open_positions if str(p.get("status", "open")) == "open")
    path.write_text(json.dumps(asdict(state), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def evaluate_gates(
    *,
    policy: ProfilePolicy,
    state: ThrottleState,
    now: datetime,
    idempotency_key: str,
    side: str,
    candle_closed: bool,
    candle_ts: str,
    htf_chop: float,
    htf_chop_ci: float | None = None,
    htf_chop_er: float | None = None,
    htf_chop_soft_max_effective: float | None = None,
    htf_chop_hard_max_effective: float | None = None,
    htf_chop_mode: str = "soft_hard",
    htf_chop_penalty: float = 0.0,
    sr_first_retest: bool,
    sr_distance_bps: float,
    sr_retest_mode: str = "strict",
    sr_near_retest_used: bool = False,
    sr_penalty: float = 0.0,
    breakout_regime: bool = False,
    breakout_window_ok: bool = False,
    bos_choch: bool,
    secondary_hits: int,
    swing_votes: dict[str, float] | None = None,
) -> GateDecision:
    daily_loss_usd = max(0.0, -float(state.realized_pnl_today_usd))
    bias = compute_bias(
        profile_id=policy.profile_id,
        side=side,
        bos_choch=bos_choch,
        swing_votes=swing_votes,
        swing_bias_neutral_band=policy.swing_bias_neutral_band,
    )
    expected_bias = "long" if side == "buy" else "short"
    active_risk_positions = count_active_risk_positions(state)

    htf_soft_max_value = float(htf_chop_soft_max_effective) if htf_chop_soft_max_effective is not None else float(policy.htf_chop_soft_max)
    htf_hard_max_value = float(htf_chop_hard_max_effective) if htf_chop_hard_max_effective is not None else float(policy.htf_chop_hard_max)

    checks: dict[str, Any] = {
        "daily_loss_circuit": {
            "max_loss_usd": policy.daily_max_loss_usd,
            "actual_loss_usd": round(daily_loss_usd, 4),
            "remaining_buffer_usd": round(max(0.0, policy.daily_max_loss_usd - daily_loss_usd), 4),
            "ok": daily_loss_usd <= policy.daily_max_loss_usd,
        },
        "candle_close": {"required": policy.require_candle_close, "ok": (candle_closed or not policy.require_candle_close), "candle_ts": candle_ts},
        "htf_chop": {
            "soft_max": float(policy.htf_chop_soft_max),
            "hard_max": float(policy.htf_chop_hard_max),
            "soft_max_effective": round(htf_soft_max_value, 4),
            "hard_max_effective": round(htf_hard_max_value, 4),
            "mode": str(htf_chop_mode),
            "actual": round(float(htf_chop), 4),
            "ci": round(float(htf_chop_ci), 4) if htf_chop_ci is not None else None,
            "er_chop": round(float(htf_chop_er), 4) if htf_chop_er is not None else None,
            "penalty_max": float(policy.htf_chop_penalty_max),
            "penalty": round(float(htf_chop_penalty), 4),
            "ok": float(htf_chop) <= htf_hard_max_value,
        },
        "bias": {
            "expected": expected_bias,
            "actual": bias.direction,
            "mechanism": bias.mechanism,
            "neutral_band": float(policy.swing_bias_neutral_band),
            "votes": swing_votes or {},
            "ok": bias.direction == expected_bias,
        },
        "sr_first_retest": {
            "required": policy.require_sr_first_retest,
            "distance_bps": round(float(sr_distance_bps), 4),
            "max_distance_bps": float(policy.sr_retest_bps_max),
            "near_max_distance_bps": float(policy.sr_retest_near_bps_max),
            "near_penalty_max": float(policy.sr_near_penalty_max),
            "retest_mode": str(sr_retest_mode),
            "near_retest_used": bool(sr_near_retest_used),
            "breakout_regime": bool(breakout_regime),
            "breakout_window_ok": bool(breakout_window_ok),
            "penalty": round(float(sr_penalty), 4),
            "actual": bool(sr_first_retest),
            "ok": (bool(sr_first_retest) or not policy.require_sr_first_retest),
        },
        "secondary_confluence": {
            "min": policy.min_secondary_confluence_hits,
            "actual": int(secondary_hits),
            "ok": int(secondary_hits) >= policy.min_secondary_confluence_hits,
        },
    }

    throttle = {
        "idempotency": {"ok": idempotency_key not in state.seen_idempotency_keys},
        "daily_cap": {"max": policy.daily_max_trades, "actual": state.executed_today, "ok": state.executed_today < policy.daily_max_trades},
        "active_risk_cap": {
            "max": policy.max_active_risk_positions,
            "actual": active_risk_positions,
            "ok": active_risk_positions < policy.max_active_risk_positions,
        },
        "cooldown": {"seconds": policy.cooldown_seconds, "ok": True},
    }

    last = _parse_iso(state.last_entry_ts)
    if last is not None and policy.cooldown_seconds > 0:
        elapsed = (now - last).total_seconds()
        throttle["cooldown"].update({"elapsed_seconds": round(elapsed, 3), "ok": elapsed >= policy.cooldown_seconds})
    else:
        throttle["cooldown"].update({"elapsed_seconds": None, "ok": True})

    checks["throttle"] = throttle

    reasons: list[str] = []
    gate_trail: list[dict[str, Any]] = []

    def _record(stage: str, ok: bool, code: str | None = None) -> None:
        node = {"stage": stage, "ok": ok}
        if code:
            node["reason_code"] = code
        gate_trail.append(node)
        if (not ok) and code:
            reasons.append(code)

    _record("daily_loss_circuit", bool(checks["daily_loss_circuit"]["ok"]), "RISK_DAILY_LOSS_CAP_BREACH")
    _record("candle_close", bool(checks["candle_close"]["ok"]), "CANDLE_NOT_CLOSED")
    _record("htf_chop", bool(checks["htf_chop"]["ok"]), "HTF_CHOP_BLOCKED")
    _record("bias_permission", bool(checks["bias"]["ok"]), "BIAS_NOT_PERMITTED")
    _record("sr_retest", bool(checks["sr_first_retest"]["ok"]), "RETEST_REQUIRED")
    _record("secondary_confluence", bool(checks["secondary_confluence"]["ok"]), "CONFLUENCE_TOO_WEAK")

    _record("idempotency", bool(throttle["idempotency"]["ok"]), "IDEMPOTENCY_DUPLICATE")
    _record("daily_cap", bool(throttle["daily_cap"]["ok"]), "DAILY_CAP_REACHED")
    _record("active_risk_cap", bool(throttle["active_risk_cap"]["ok"]), "ACTIVE_RISK_CAP_REACHED")
    _record("cooldown", bool(throttle["cooldown"]["ok"]), "COOLDOWN_ACTIVE")

    checks["gate_trail"] = gate_trail
    return GateDecision(accepted=not reasons, reason_codes=tuple(reasons), gate_checks=checks)
