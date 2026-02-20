from concurrent.futures import ThreadPoolExecutor
from uuid import NAMESPACE_URL, uuid5

from liquidsniper.core.execution_boundary import ExecutionBoundary, PolicyDecision


def _proposal(trace_id: str):
    return {
        "trace_id": trace_id,
        "policy_version": "v1",
        "rulebook_ref": "RB",
        "symbol": "ETHUSDT",
        "side": "long",
        "mode": "paper",
        "risk_usd": 1,
        "trade_intent": {
            "intent_id": str(uuid5(NAMESPACE_URL, trace_id)),
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
            "idempotency_key": trace_id,
        },
    }


def _accept(trace_id: str):
    return PolicyDecision(True, (), trace_id, "v1")


def test_threshold_under_at_over(monkeypatch, tmp_path):
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("LIQUIDSNIPER_MAX_DAILY_DRAWDOWN_USD", "10")
    b = ExecutionBoundary(starting_bankroll_usd=1000)

    p1 = b.propose_trade(_proposal("run-01"), _accept("run-01"))
    o1 = b.execute_with_adapter(p1["proposal_id"], lambda _: {"pnl_usd": -9})
    assert o1["decision"] == "executed"

    p2 = b.propose_trade(_proposal("run-02"), _accept("run-02"))
    o2 = b.execute_with_adapter(p2["proposal_id"], lambda _: {"pnl_usd": -1})
    assert o2["decision"] == "executed"

    p3 = b.propose_trade(_proposal("run-03"), _accept("run-03"))
    o3 = b.execute_with_adapter(p3["proposal_id"], lambda _: {"pnl_usd": 2})
    assert o3["decision"] == "blocked"


def test_restart_persists_tripped_state(monkeypatch, tmp_path):
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("LIQUIDSNIPER_MAX_DAILY_DRAWDOWN_USD", "5")

    b1 = ExecutionBoundary(starting_bankroll_usd=1000)
    p1 = b1.propose_trade(_proposal("run-11"), _accept("run-11"))
    assert b1.execute_with_adapter(p1["proposal_id"], lambda _: {"pnl_usd": -8})["decision"] == "executed"

    b2 = ExecutionBoundary(starting_bankroll_usd=1000)
    p2 = b2.propose_trade(_proposal("run-12"), _accept("run-12"))
    out2 = b2.execute_with_adapter(p2["proposal_id"], lambda _: {"pnl_usd": 1})
    assert out2["decision"] == "blocked"
    assert out2["reason_codes"] == ("GLOBAL_DRAWDOWN_TRIPPED_ABSOLUTE",)


def test_overtrading_regression_guard_when_breaker_engaged(monkeypatch, tmp_path):
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("LIQUIDSNIPER_MAX_DAILY_DRAWDOWN_USD", "2")
    b = ExecutionBoundary(starting_bankroll_usd=1000)

    first = b.propose_trade(_proposal("run-21"), _accept("run-21"))
    assert b.execute_with_adapter(first["proposal_id"], lambda _: {"pnl_usd": -3})["decision"] == "executed"

    blocked = 0
    for i in range(10):
        rid = f"run-22-{i}"
        p = b.propose_trade(_proposal(rid), _accept(rid))
        out = b.execute_with_adapter(p["proposal_id"], lambda _: {"pnl_usd": 1})
        if out["decision"] == "blocked":
            blocked += 1
    assert blocked == 10


def test_concurrency_only_one_trade_executes_before_breaker_blocks(monkeypatch, tmp_path):
    monkeypatch.setenv("LS_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("LIQUIDSNIPER_MAX_DAILY_DRAWDOWN_USD", "1")
    b = ExecutionBoundary(starting_bankroll_usd=1000)

    def run_one(i: int) -> str:
        rid = f"run-3{i}"
        p = b.propose_trade(_proposal(rid), _accept(rid))
        out = b.execute_with_adapter(p["proposal_id"], lambda _: {"pnl_usd": -2 if i == 0 else 1})
        return out["decision"]

    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(run_one, [0, 1]))
    assert "executed" in results
    assert "blocked" in results
