from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision


def _proposal(**overrides):
    base = {
        "trace_id": "run_123",
        "policy_version": "v1",
        "rulebook_ref": "TRADING_STRATEGY_RUNBOOK_V1",
        "symbol": "ETHUSDT",
        "side": "long",
        "mode": "paper",
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


def test_live_mode_is_blocked_even_when_policy_approved():
    boundary = ExecutionBoundary()

    proposed = boundary.propose_trade(
        _proposal(mode="live"),
        PolicyDecision(accepted=True, trace_id="run_123", policy_version="v1"),
    )
    out = boundary.execute_approved(proposed["proposal_id"])

    assert out["decision"] == "blocked"
    assert out["reason_codes"] == ("MODE_NOT_ALLOWED",)
