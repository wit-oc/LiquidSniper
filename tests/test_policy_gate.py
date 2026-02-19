from __future__ import annotations

import pytest

from liquidsniper.core.policy_gate import (
    PolicyGateValidationError,
    REJECTION_CODE_MAP,
    validate_execution_result,
    validate_policy_decision,
    validate_trade_intent,
)


def _trade_intent(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "intent_id": "8e8947f4-e1f7-4d6a-b5fa-362db4f8b735",
        "ts": "2026-02-19T15:00:00Z",
        "strategy_id": "htf-confluence-v1",
        "mode": "paper",
        "venue": "blofin",
        "symbol": "BTCUSDT",
        "side": "buy",
        "order_type": "limit",
        "limit_price": "98321.2",
        "size_notional_usd": "250",
        "time_in_force": "GTC",
        "max_slippage_bps": 15,
        "thesis": "POI_RETEST_CONFIRMED",
        "idempotency_key": "trace-001",
    }
    base.update(overrides)
    return base


def test_trade_intent_validates_and_normalizes() -> None:
    result = validate_trade_intent(_trade_intent())
    assert result.valid is True
    assert result.normalized["size_notional_usd"] == "250"


@pytest.mark.parametrize(
    ("payload", "reason_code"),
    [
        ({"mode": "oops"}, "INVALID_ENUM"),
        ({"size_notional_usd": 0}, "NON_POSITIVE"),
        ({"intent_id": "bad"}, "INVALID_UUID"),
    ],
)
def test_trade_intent_rejections_are_deterministic(payload: dict[str, object], reason_code: str) -> None:
    with pytest.raises(PolicyGateValidationError) as exc:
        validate_trade_intent(_trade_intent(**payload))

    assert exc.value.reason_code == reason_code


def test_policy_decision_validates() -> None:
    result = validate_policy_decision(
        {
            "intent_id": "8e8947f4-e1f7-4d6a-b5fa-362db4f8b735",
            "approved": False,
            "reasons": ["RISK_DAILY_LOSS_CAP_BREACH"],
            "policy_snapshot_id": "policy-v0-20260219",
            "risk_metrics": {
                "post_trade_exposure_usd": "1200",
                "projected_daily_loss_usd": "320",
            },
        }
    )
    assert result.valid is True


def test_execution_result_rejects_negative_fee() -> None:
    with pytest.raises(PolicyGateValidationError) as exc:
        validate_execution_result(
            {
                "intent_id": "8e8947f4-e1f7-4d6a-b5fa-362db4f8b735",
                "venue_order_id": "ord-123",
                "status": "accepted",
                "filled_qty": "0",
                "avg_fill_price": "0",
                "fees_usd": "-0.01",
                "tx_hash": None,
                "error_code": None,
                "ts": "2026-02-19T15:01:00Z",
            }
        )

    assert exc.value.reason_code == "NEGATIVE_VALUE"


def test_rejection_code_map_has_expected_core_codes() -> None:
    for code in ("MISSING_FIELD", "TYPE_MISMATCH", "INVALID_ENUM", "INVALID_UUID", "INVALID_TIMESTAMP"):
        assert code in REJECTION_CODE_MAP
