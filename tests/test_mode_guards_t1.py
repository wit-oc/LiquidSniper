from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision
from liquidsniper.core.mode_guard import enforce_startup_mode, validate_api_mode_request


def _proposal(**overrides):
    base = {
        "trace_id": "run_guard",
        "policy_version": "v1",
        "rulebook_ref": "RB",
        "mode": "live",
        "parallel": True,
    }
    base.update(overrides)
    return base


def test_startup_guard_rejects_parallel_outside_paper():
    try:
        enforce_startup_mode(parallel_enabled=True, mode="live")
    except RuntimeError as exc:
        assert str(exc) == "MODE_GUARD_PARALLEL_REQUIRES_PAPER"
    else:
        raise AssertionError("expected startup guard error")


def test_api_guard_rejects_parallel_outside_paper():
    result = validate_api_mode_request({"parallel": True}, mode="dry_run")
    assert result.allowed is False
    assert result.reason_code == "MODE_GUARD_PARALLEL_REQUIRES_PAPER"


def test_runtime_guard_rejects_parallel_proposal_outside_paper():
    boundary = ExecutionBoundary()
    out = boundary.propose_trade(
        _proposal(),
        PolicyDecision(accepted=True, trace_id="run_guard", policy_version="v1"),
    )
    assert out["decision"] == "rejected"
    assert out["reason_codes"] == ("MODE_GUARD_PARALLEL_REQUIRES_PAPER",)
