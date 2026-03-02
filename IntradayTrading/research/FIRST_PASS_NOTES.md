# First Pass Metrics Notes

This pass is **rough plumbing metrics** from event logs, not final strategy performance.

Assumptions in `first_pass_metrics.py`:
- FIFO matching of exits to open positions by side.
- PnL measured in raw price points per unit size (not % equity sizing).
- `tp1_hit` is not treated as partial close yet.

Use this only as a quick quality gate before full vectorbt/backtesting.py evaluation.
