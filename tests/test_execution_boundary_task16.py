from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision


def _trade_intent(**overrides):
    base = {
        "intent_id": "8e8947f4-e1f7-4d6a-b5fa-362db4f8b735",
        "ts": "2026-02-19T15:00:00Z",
        "strategy_id": "htf-confluence-v1",
        "mode": "paper",
        "venue": "blofin",
        "symbol": "ETHUSDT",
        "side": "buy",
        "order_type": "limit",
        "limit_price": "2750.5",
        "size_notional_usd": "120",
        "time_in_force": "GTC",
        "max_slippage_bps": 15,
        "thesis": "POI_RETEST_CONFIRMED",
        "idempotency_key": "trace-001",
    }
    base.update(overrides)
    return base


def _proposal(**overrides):
    base = {
        "trace_id": "run_123",
        "policy_version": "v1",
        "rulebook_ref": "TRADING_STRATEGY_RUNBOOK_V1",
        "symbol": "ETHUSDT",
        "side": "long",
        "mode": "paper",
        "trade_intent": _trade_intent(),
    }
    base.update(overrides)
    return base


def test_execute_requires_existing_approved_proposal():
    boundary = ExecutionBoundary()

    out = boundary.execute_approved("prop_999999")

    assert out["decision"] == "blocked"
    assert out["reason_codes"] == ("PROPOSAL_NOT_FOUND",)


def test_missing_policy_decision_rejects_and_blocks_execute():
    boundary = ExecutionBoundary()

    proposed = boundary.propose_trade(_proposal(), policy=None)
    blocked = boundary.execute_approved(proposed["proposal_id"])

    assert proposed["decision"] == "rejected"
    assert proposed["reason_codes"] == ("POLICY_DECISION_REQUIRED",)
    assert blocked["decision"] == "blocked"
    assert blocked["reason_codes"] == ("PROPOSAL_NOT_APPROVED",)


def test_policy_mismatch_rejects_deterministically():
    boundary = ExecutionBoundary()

    proposed = boundary.propose_trade(
        _proposal(trace_id="run_a", policy_version="v2"),
        PolicyDecision(accepted=True, trace_id="run_b", policy_version="v2"),
    )

    assert proposed["decision"] == "rejected"
    assert proposed["reason_codes"] == ("POLICY_DECISION_MISMATCH",)


def test_approved_proposal_executes_and_carries_audit_fields():
    boundary = ExecutionBoundary()

    proposed = boundary.propose_trade(
        _proposal(),
        PolicyDecision(accepted=True, trace_id="run_123", policy_version="v1"),
    )
    executed = boundary.execute_approved(proposed["proposal_id"])

    assert proposed["decision"] == "accepted"
    assert executed["decision"] == "executed"
    assert executed["trace_id"] == "run_123"
    assert executed["policy_version"] == "v1"
    assert executed["rulebook_ref"] == "TRADING_STRATEGY_RUNBOOK_V1"


def test_invalid_trade_intent_rejects_before_adapter_invocation():
    boundary = ExecutionBoundary()
    adapter_called = False

    def _adapter(_: dict):
        nonlocal adapter_called
        adapter_called = True
        return {"status": "submitted"}

    proposed = boundary.propose_trade(
        _proposal(trade_intent=_trade_intent(size_notional_usd="0")),
        PolicyDecision(accepted=True, trace_id="run_123", policy_version="v1"),
    )
    out = boundary.execute_with_adapter(proposed["proposal_id"], _adapter)

    assert proposed["decision"] == "rejected"
    assert proposed["reason_codes"] == ("TRADE_INTENT_NON_POSITIVE",)
    assert out["decision"] == "blocked"
    assert out["reason_codes"] == ("PROPOSAL_NOT_APPROVED",)
    assert adapter_called is False


def test_live_mode_is_blocked_even_when_policy_approved():
    boundary = ExecutionBoundary()

    proposed = boundary.propose_trade(
        _proposal(mode="live"),
        PolicyDecision(accepted=True, trace_id="run_123", policy_version="v1"),
    )
    out = boundary.execute_approved(proposed["proposal_id"])

    assert out["decision"] == "blocked"
    assert out["reason_codes"] == ("MODE_NOT_ALLOWED",)
