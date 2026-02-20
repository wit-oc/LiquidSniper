from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision
from liquidsniper.core.rollout_controls import paper_parallel_enabled, rollback_mode_enabled, strategy_accounts_enabled


def _proposal():
    return {
        "trace_id": "run_es",
        "policy_version": "v1",
        "rulebook_ref": "RB",
        "mode": "paper",
        "trade_intent": {
            "intent_id": "8e8947f4-e1f7-4d6a-b5fa-362db4f8b735",
            "ts": "2026-02-19T15:00:00Z",
            "strategy_id": "intraday",
            "mode": "paper",
            "venue": "blofin",
            "symbol": "ETHUSDT",
            "side": "buy",
            "order_type": "limit",
            "limit_price": "2750.5",
            "size_notional_usd": "120",
            "time_in_force": "GTC",
            "max_slippage_bps": 15,
            "thesis": "ok",
            "idempotency_key": "trace-es",
        },
    }


def test_feature_flags_and_rollback_controls(monkeypatch):
    monkeypatch.setenv("LIQUIDSNIPER_FEATURE_STRATEGY_ACCOUNTS", "true")
    monkeypatch.setenv("LIQUIDSNIPER_FEATURE_PAPER_PARALLEL", "true")
    monkeypatch.setenv("LIQUIDSNIPER_ROLLBACK_SINGLE_STRATEGY", "1")
    assert strategy_accounts_enabled() is True
    assert paper_parallel_enabled() is True
    assert rollback_mode_enabled() is True


def test_emergency_stop_blocks_new_entries(monkeypatch):
    monkeypatch.setenv("LIQUIDSNIPER_EMERGENCY_STOP", "true")
    boundary = ExecutionBoundary()
    p = boundary.propose_trade(_proposal(), PolicyDecision(True, (), "run_es", "v1"))
    out = boundary.execute_with_adapter(p["proposal_id"], lambda _: {"status": "paper_fill", "pnl_usd": 1})
    assert out["decision"] == "blocked"
    assert out["reason_codes"] == ("EMERGENCY_STOP_ACTIVE",)
