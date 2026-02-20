"""Trusted Trading Core v0 policy gate starter: schema validators + rejection codes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import os
from typing import Any
from uuid import UUID


REJECTION_CODE_MAP: dict[str, str] = {
    "MISSING_FIELD": "Required field is missing.",
    "TYPE_MISMATCH": "Field has invalid type.",
    "INVALID_ENUM": "Field value is outside allowed enum set.",
    "INVALID_UUID": "Field must be a valid UUID.",
    "INVALID_TIMESTAMP": "Field must be a valid ISO-8601 timestamp.",
    "NON_POSITIVE": "Field must be greater than zero.",
    "NEGATIVE_VALUE": "Field must be zero or greater.",
}


class PolicyGateValidationError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


TRADE_INTENT_ENUMS = {
    "mode": {"paper", "live"},
    "venue": {"blofin", "onchain"},
    "side": {"buy", "sell"},
    "order_type": {"market", "limit"},
    "time_in_force": {"GTC", "IOC", "FOK"},
}

EXECUTION_RESULT_ENUMS = {
    "status": {"accepted", "rejected", "filled", "partial", "failed"},
}

PAPER_STRATEGIES = {"scalp", "intraday", "swing"}


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    normalized: dict[str, Any]


def _require(payload: dict[str, Any], field: str, expected_type: type | tuple[type, ...]) -> Any:
    if field not in payload:
        raise PolicyGateValidationError("MISSING_FIELD", f"missing required field: {field}")
    value = payload[field]
    if not isinstance(value, expected_type):
        raise PolicyGateValidationError("TYPE_MISMATCH", f"field '{field}' has invalid type")
    return value


def _parse_uuid(value: str, field: str) -> str:
    try:
        UUID(value)
    except ValueError as exc:
        raise PolicyGateValidationError("INVALID_UUID", f"field '{field}' must be a UUID") from exc
    return value


def _parse_iso8601(value: str, field: str) -> str:
    candidate = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise PolicyGateValidationError("INVALID_TIMESTAMP", f"field '{field}' must be ISO-8601") from exc
    return value


def _decimal(value: Any, field: str) -> str:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PolicyGateValidationError("TYPE_MISMATCH", f"field '{field}' must be numeric") from exc
    if not d.is_finite():
        raise PolicyGateValidationError("TYPE_MISMATCH", f"field '{field}' must be finite")
    text = format(d, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _enum(value: str, field: str, allowed: set[str]) -> str:
    if value not in allowed:
        raise PolicyGateValidationError("INVALID_ENUM", f"field '{field}' is outside allowed enum values")
    return value


def validate_trade_intent(payload: dict[str, Any]) -> ValidationResult:
    normalized = {
        "intent_id": _parse_uuid(_require(payload, "intent_id", str), "intent_id"),
        "ts": _parse_iso8601(_require(payload, "ts", str), "ts"),
        "strategy_id": _require(payload, "strategy_id", str).strip().lower(),
        "mode": _enum(_require(payload, "mode", str), "mode", TRADE_INTENT_ENUMS["mode"]),
        "venue": _enum(_require(payload, "venue", str), "venue", TRADE_INTENT_ENUMS["venue"]),
        "symbol": _require(payload, "symbol", str).strip(),
        "side": _enum(_require(payload, "side", str), "side", TRADE_INTENT_ENUMS["side"]),
        "order_type": _enum(_require(payload, "order_type", str), "order_type", TRADE_INTENT_ENUMS["order_type"]),
        "limit_price": _decimal(_require(payload, "limit_price", (int, float, str)), "limit_price"),
        "size_notional_usd": _decimal(_require(payload, "size_notional_usd", (int, float, str)), "size_notional_usd"),
        "time_in_force": _enum(_require(payload, "time_in_force", str), "time_in_force", TRADE_INTENT_ENUMS["time_in_force"]),
        "max_slippage_bps": int(_require(payload, "max_slippage_bps", int)),
        "thesis": _require(payload, "thesis", str).strip(),
        "idempotency_key": _require(payload, "idempotency_key", str).strip(),
    }

    if Decimal(normalized["size_notional_usd"]) <= 0:
        raise PolicyGateValidationError("NON_POSITIVE", "size_notional_usd must be > 0")
    if Decimal(normalized["limit_price"]) < 0:
        raise PolicyGateValidationError("NEGATIVE_VALUE", "limit_price must be >= 0")
    if normalized["max_slippage_bps"] < 0:
        raise PolicyGateValidationError("NEGATIVE_VALUE", "max_slippage_bps must be >= 0")
    if not normalized["strategy_id"]:
        raise PolicyGateValidationError("STRATEGY_REQUIRED", "strategy_id is required")
    if normalized["mode"] == "paper" and normalized["strategy_id"] not in PAPER_STRATEGIES:
        allow_fallback = os.getenv("LIQUIDSNIPER_ALLOW_LEGACY_STRATEGY_FALLBACK", "false").strip().lower() in {"1", "true", "yes"}
        if allow_fallback:
            normalized["strategy_id"] = "intraday"
        else:
            raise PolicyGateValidationError("INVALID_STRATEGY", "paper mode requires scalp|intraday|swing strategy")

    return ValidationResult(valid=True, normalized=normalized)


def validate_policy_decision(payload: dict[str, Any]) -> ValidationResult:
    risk_metrics = _require(payload, "risk_metrics", dict)
    normalized = {
        "intent_id": _parse_uuid(_require(payload, "intent_id", str), "intent_id"),
        "approved": _require(payload, "approved", bool),
        "reasons": _require(payload, "reasons", list),
        "policy_snapshot_id": _require(payload, "policy_snapshot_id", str).strip(),
        "risk_metrics": {
            "post_trade_exposure_usd": _decimal(_require(risk_metrics, "post_trade_exposure_usd", (int, float, str)), "risk_metrics.post_trade_exposure_usd"),
            "projected_daily_loss_usd": _decimal(_require(risk_metrics, "projected_daily_loss_usd", (int, float, str)), "risk_metrics.projected_daily_loss_usd"),
        },
    }

    if any(not isinstance(reason, str) for reason in normalized["reasons"]):
        raise PolicyGateValidationError("TYPE_MISMATCH", "reasons must be a list of strings")

    return ValidationResult(valid=True, normalized=normalized)


def validate_execution_result(payload: dict[str, Any]) -> ValidationResult:
    tx_hash = payload.get("tx_hash")
    error_code = payload.get("error_code")
    if tx_hash is not None and not isinstance(tx_hash, str):
        raise PolicyGateValidationError("TYPE_MISMATCH", "tx_hash must be string|null")
    if error_code is not None and not isinstance(error_code, str):
        raise PolicyGateValidationError("TYPE_MISMATCH", "error_code must be string|null")

    normalized = {
        "intent_id": _parse_uuid(_require(payload, "intent_id", str), "intent_id"),
        "venue_order_id": _require(payload, "venue_order_id", str).strip(),
        "status": _enum(_require(payload, "status", str), "status", EXECUTION_RESULT_ENUMS["status"]),
        "filled_qty": _decimal(_require(payload, "filled_qty", (int, float, str)), "filled_qty"),
        "avg_fill_price": _decimal(_require(payload, "avg_fill_price", (int, float, str)), "avg_fill_price"),
        "fees_usd": _decimal(_require(payload, "fees_usd", (int, float, str)), "fees_usd"),
        "tx_hash": tx_hash,
        "error_code": error_code,
        "ts": _parse_iso8601(_require(payload, "ts", str), "ts"),
    }

    for field in ("filled_qty", "avg_fill_price", "fees_usd"):
        if Decimal(normalized[field]) < 0:
            raise PolicyGateValidationError("NEGATIVE_VALUE", f"{field} must be >= 0")

    return ValidationResult(valid=True, normalized=normalized)
