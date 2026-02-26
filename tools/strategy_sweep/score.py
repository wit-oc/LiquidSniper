from __future__ import annotations

from typing import Dict


def composite_score(metrics: Dict[str, float]) -> float:
    """Simple deterministic optimization score.

    Higher is better; penalize drawdown, reward PF/win rate/net pnl/trade count sanity.
    """
    trades = metrics.get("trades", 0.0)
    trade_factor = min(1.0, trades / 50.0)
    return (
        metrics.get("net_pnl", 0.0) / 1000.0
        + 2.0 * metrics.get("pf", 0.0)
        + 1.5 * metrics.get("win_rate", 0.0)
        - 3.0 * metrics.get("max_dd", 0.0)
        + trade_factor
    )
