from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWEEP_DIR = ROOT / "tools" / "strategy_sweep"
sys.path.insert(0, str(SWEEP_DIR))

from engine_v1 import calculate_confluence, compute_risk_based_qty, gate_pass  # noqa: E402


def test_confluence_score_deterministic() -> None:
    features = {
        "trend_long": True,
        "structure_long": True,
        "first_retest_long": False,
        "ema_stack_long": True,
        "chop_ok": True,
        "candle_ok": True,
        "sr_side_ok_long": True,
    }
    score = calculate_confluence(features, "long")
    # 2 + 2 + 0 + 1 + 1 + 1 + 1
    assert score == 8.0


def test_risk_based_qty_respects_caps() -> None:
    qty = compute_risk_based_qty(
        equity=10_000.0,
        risk_pct=8.0,
        entry_price=100.0,
        stop_price=95.0,
        profile_cap_pct=5.0,
        max_notional_pct=100.0,
    )
    # risk budget = 500 (capped), per unit risk = 5 => 100 qty
    assert abs(qty - 100.0) < 1e-9

    qty_notional_clamped = compute_risk_based_qty(
        equity=10_000.0,
        risk_pct=5.0,
        entry_price=100.0,
        stop_price=99.0,
        profile_cap_pct=5.0,
        max_notional_pct=50.0,
    )
    # raw qty 500, max notional qty = 50
    assert abs(qty_notional_clamped - 50.0) < 1e-9


def test_gate_pass_sanity() -> None:
    assert gate_pass(8.0, 7.2, chop_ok=True, trend_ok=True, candle_ok=True)
    assert not gate_pass(7.0, 7.2, chop_ok=True, trend_ok=True, candle_ok=True)
    assert not gate_pass(8.0, 7.2, chop_ok=False, trend_ok=True, candle_ok=True)
    assert not gate_pass(8.0, 7.2, chop_ok=True, trend_ok=False, candle_ok=True)
