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
            "htf_chop_max": 45.0,
            "require_sr_first_retest": True,
            "require_bos_choch": True,
            "min_secondary_confluence_hits": 2,
        },
    },
    "I": {
        "htf_anchor_tf": "4H",
        "itf_tf": "1H",
        "ltf_trigger_tfs": ["15m", "5m"],
        "gate": {
            "require_candle_close": True,
            "htf_chop_max": 50.0,
            "require_sr_first_retest": True,
            "require_bos_choch": True,
            "min_secondary_confluence_hits": 2,
        },
    },
    "C": {
        "htf_anchor_tf": "1H",
        "itf_tf": "15m",
        "ltf_trigger_tfs": ["5m", "1m"],
        "gate": {
            "require_candle_close": True,
            "htf_chop_max": 55.0,
            "require_sr_first_retest": True,
            "require_bos_choch": True,
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
    htf_chop_max: float
    require_sr_first_retest: bool
    require_bos_choch: bool
    min_secondary_confluence_hits: int
    cooldown_seconds: int
    daily_max_trades: int
    daily_max_loss_usd: float
    enforce_one_open_position: bool
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

    @classmethod
    def empty(cls, trading_day: str) -> "ThrottleState":
        return cls(
            trading_day=trading_day,
            last_entry_ts=None,
            trades_open=0,
            executed_today=0,
            realized_pnl_today_usd=0.0,
            seen_idempotency_keys=[],
        )


@dataclass(frozen=True)
class GateDecision:
    accepted: bool
    reason_codes: tuple[str, ...]
    gate_checks: dict[str, Any]


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

    return ProfilePolicy(
        profile_id=profile_id,
        htf_anchor_tf=str(spec["htf_anchor_tf"]),
        itf_tf=str(spec["itf_tf"]),
        ltf_trigger_tfs=tuple(str(x) for x in spec["ltf_trigger_tfs"]),
        require_candle_close=_bool_env("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", bool(gate["require_candle_close"])),
        htf_chop_max=_float_env("LIQUIDSNIPER_HTF_CHOP_MAX", float(gate["htf_chop_max"])),
        require_sr_first_retest=_bool_env("LIQUIDSNIPER_REQUIRE_SR_FIRST_RETEST", bool(gate["require_sr_first_retest"])),
        require_bos_choch=_bool_env("LIQUIDSNIPER_REQUIRE_BOS_CHOCH", bool(gate["require_bos_choch"])),
        min_secondary_confluence_hits=min_secondary,
        cooldown_seconds=cooldown_seconds,
        daily_max_trades=daily_max_trades,
        daily_max_loss_usd=daily_max_loss_usd,
        enforce_one_open_position=_bool_env("LIQUIDSNIPER_ENFORCE_ONE_OPEN_POSITION", True),
        policy_version=os.getenv("LIQUIDSNIPER_POLICY_VERSION", "v1").strip() or "v1",
    )


def load_throttle_state(path: Path, now: datetime) -> ThrottleState:
    trading_day = _utc_day(now)
    if not path.exists():
        return ThrottleState.empty(trading_day)

    raw = json.loads(path.read_text(encoding="utf-8"))
    state = ThrottleState(
        trading_day=str(raw.get("trading_day") or trading_day),
        last_entry_ts=raw.get("last_entry_ts"),
        trades_open=max(0, int(raw.get("trades_open") or 0)),
        executed_today=max(0, int(raw.get("executed_today") or 0)),
        realized_pnl_today_usd=float(raw.get("realized_pnl_today_usd") or 0.0),
        seen_idempotency_keys=[str(x) for x in (raw.get("seen_idempotency_keys") or []) if str(x)],
    )
    if state.trading_day != trading_day:
        return ThrottleState.empty(trading_day)
    return state


def persist_throttle_state(path: Path, state: ThrottleState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    candle_closed: bool,
    candle_ts: str,
    htf_chop: float,
    sr_first_retest: bool,
    bos_choch: bool,
    secondary_hits: int,
) -> GateDecision:
    daily_loss_usd = max(0.0, -float(state.realized_pnl_today_usd))

    checks: dict[str, Any] = {
        "daily_loss_circuit": {
            "max_loss_usd": policy.daily_max_loss_usd,
            "actual_loss_usd": round(daily_loss_usd, 4),
            "remaining_buffer_usd": round(max(0.0, policy.daily_max_loss_usd - daily_loss_usd), 4),
            "ok": daily_loss_usd <= policy.daily_max_loss_usd,
        },
        "candle_close": {"required": policy.require_candle_close, "ok": (candle_closed or not policy.require_candle_close), "candle_ts": candle_ts},
        "htf_chop": {"max": policy.htf_chop_max, "actual": round(float(htf_chop), 4), "ok": float(htf_chop) <= policy.htf_chop_max},
        "sr_first_retest": {"required": policy.require_sr_first_retest, "actual": bool(sr_first_retest), "ok": (bool(sr_first_retest) or not policy.require_sr_first_retest)},
        "bos_choch": {"required": policy.require_bos_choch, "actual": bool(bos_choch), "ok": (bool(bos_choch) or not policy.require_bos_choch)},
        "secondary_confluence": {
            "min": policy.min_secondary_confluence_hits,
            "actual": int(secondary_hits),
            "ok": int(secondary_hits) >= policy.min_secondary_confluence_hits,
        },
    }

    throttle = {
        "idempotency": {"ok": idempotency_key not in state.seen_idempotency_keys},
        "daily_cap": {"max": policy.daily_max_trades, "actual": state.executed_today, "ok": state.executed_today < policy.daily_max_trades},
        "one_open_position": {
            "enforced": policy.enforce_one_open_position,
            "actual_open": state.trades_open,
            "ok": (state.trades_open == 0 if policy.enforce_one_open_position else True),
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
    if not checks["daily_loss_circuit"]["ok"]:
        reasons.append("RISK_DAILY_LOSS_CAP_BREACH")
    if not checks["candle_close"]["ok"]:
        reasons.append("CANDLE_NOT_CLOSED")
    if not checks["htf_chop"]["ok"]:
        reasons.append("HTF_CHOP_BLOCKED")
    if not checks["sr_first_retest"]["ok"]:
        reasons.append("RETEST_REQUIRED")
    if not checks["bos_choch"]["ok"]:
        reasons.append("BOS_CHOCH_REQUIRED")
    if not checks["secondary_confluence"]["ok"]:
        reasons.append("CONFLUENCE_TOO_WEAK")

    if not throttle["idempotency"]["ok"]:
        reasons.append("IDEMPOTENCY_DUPLICATE")
    if not throttle["daily_cap"]["ok"]:
        reasons.append("DAILY_CAP_REACHED")
    if not throttle["one_open_position"]["ok"]:
        reasons.append("OPEN_POSITION_LOCKED")
    if not throttle["cooldown"]["ok"]:
        reasons.append("COOLDOWN_ACTIVE")

    return GateDecision(accepted=not reasons, reason_codes=tuple(reasons), gate_checks=checks)
