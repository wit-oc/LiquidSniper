from pathlib import Path

from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision


def _proposal(**overrides):
    base = {
        "trace_id": "run_breaker",
        "policy_version": "v1",
        "rulebook_ref": "RB",
        "symbol": "ETHUSDT",
        "side": "long",
        "mode": "paper",
        "risk_usd": 10,
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
            "idempotency_key": "trace-breaker",
        },
    }
    base.update(overrides)
    return base


def test_global_drawdown_blocks_new_entries(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("LIQUIDSNIPER_MAX_DAILY_DRAWDOWN_USD", "10")
    boundary = ExecutionBoundary(starting_bankroll_usd=1000)

    p1 = boundary.propose_trade(_proposal(trace_id="run_1"), PolicyDecision(True, (), "run_1", "v1"))
    o1 = boundary.execute_with_adapter(p1["proposal_id"], lambda _: {"status": "paper_fill", "pnl_usd": -12})
    assert o1["decision"] == "executed"

    p2 = boundary.propose_trade(_proposal(trace_id="run_2"), PolicyDecision(True, (), "run_2", "v1"))
    o2 = boundary.execute_with_adapter(p2["proposal_id"], lambda _: {"status": "paper_fill", "pnl_usd": 1})
    assert o2["decision"] == "blocked"
    assert o2["reason_codes"] == ("GLOBAL_DRAWDOWN_TRIPPED_ABSOLUTE",)


def test_breaker_fails_closed_when_state_corrupt(monkeypatch, tmp_path: Path):
    root = tmp_path / "artifacts"
    state_path = root / "paper_mvp" / "state" / "global_drawdown_breaker_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text("not-json", encoding="utf-8")

    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(root))
    boundary = ExecutionBoundary(starting_bankroll_usd=1000)
    p = boundary.propose_trade(_proposal(), PolicyDecision(True, (), "run_breaker", "v1"))
    out = boundary.execute_with_adapter(p["proposal_id"], lambda _: {"status": "paper_fill", "pnl_usd": 1})
    assert out["decision"] == "blocked"
    assert out["reason_codes"] == ("GLOBAL_DRAWDOWN_STATE_UNREADABLE",)
