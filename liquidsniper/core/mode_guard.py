from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

_ALLOWED_MODES = {"paper", "live", "dry_run", "sim"}


@dataclass(frozen=True)
class ModeGuardResult:
    allowed: bool
    reason_code: str = ""


def current_mode() -> str:
    mode = os.getenv("LIQUIDSNIPER_MODE", "paper").strip().lower()
    return mode or "paper"


def _parallel_requested(payload: dict[str, Any] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    if bool(payload.get("parallel")):
        return True
    if bool(payload.get("enable_parallel")):
        return True
    lanes = payload.get("strategy_lanes")
    if isinstance(lanes, list) and len(lanes) > 1:
        return True
    return False


def guard_parallel_mode(*, mode: str | None = None, payload: dict[str, Any] | None = None) -> ModeGuardResult:
    effective_mode = (mode or current_mode()).strip().lower()
    if effective_mode not in _ALLOWED_MODES:
        return ModeGuardResult(False, "MODE_GUARD_UNKNOWN_MODE")
    if _parallel_requested(payload) and effective_mode != "paper":
        return ModeGuardResult(False, "MODE_GUARD_PARALLEL_REQUIRES_PAPER")
    return ModeGuardResult(True)


def enforce_startup_mode(*, parallel_enabled: bool, mode: str | None = None) -> None:
    payload = {"parallel": parallel_enabled}
    result = guard_parallel_mode(mode=mode, payload=payload)
    if not result.allowed:
        raise RuntimeError(result.reason_code)


def validate_api_mode_request(payload: dict[str, Any], *, mode: str | None = None) -> ModeGuardResult:
    return guard_parallel_mode(mode=mode, payload=payload)
