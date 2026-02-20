from __future__ import annotations

import os


def _enabled(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def strategy_accounts_enabled() -> bool:
    return _enabled("LIQUIDSNIPER_FEATURE_STRATEGY_ACCOUNTS", "true")


def paper_parallel_enabled() -> bool:
    return _enabled("LIQUIDSNIPER_FEATURE_PAPER_PARALLEL", "false")


def emergency_stop_enabled() -> bool:
    return _enabled("LIQUIDSNIPER_EMERGENCY_STOP", "false")


def rollback_mode_enabled() -> bool:
    return _enabled("LIQUIDSNIPER_ROLLBACK_SINGLE_STRATEGY", "false")
