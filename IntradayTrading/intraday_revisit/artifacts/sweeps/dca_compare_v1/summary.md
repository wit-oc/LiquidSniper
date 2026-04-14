# DCA comparison v1

Baseline source: artifacts/sweeps/miniwave_v2_1_autonomy/iter_2026-02-28-1900_stop_buffer_frac_0p0013.json (best post-instrumentation avg_pf).

## Fill model
- Signal generation unchanged (same entries/exits from runner).
- DCA triggers are adverse-move fractions from entry toward stop, evaluated on close prices.
- Tranche risk weights sum to 1.0, so max stop loss equals configured per-trade risk_pct.
- Unreached tranches are skipped (unused risk; no over-allocation).

## Baseline vs DCA-50/50
- total_trades: 74.0000 -> 74.0000 (+0.0000)
- avg_pf: 0.6216 -> 0.2605 (-0.3611)
- worst_dd_pct: 48.6261% -> 66.7344% (+18.1083%)
- total_net: -5824.4807 -> -11462.1642 (-5637.6835)
- avg_win_rate: 0.3721% -> 0.3721% (+0.0000%)

## Baseline vs DCA-30/30/40
- total_trades: 74.0000 -> 74.0000 (+0.0000)
- avg_pf: 0.6216 -> 0.1396 (-0.4820)
- worst_dd_pct: 48.6261% -> 75.7019% (+27.0758%)
- total_net: -5824.4807 -> -13784.4054 (-7959.9247)
- avg_win_rate: 0.3721% -> 0.3721% (+0.0000%)

## Conclusion
- No DCA variant improved PF/DD jointly versus baseline. Best PF variant: dca_50_50 (PF 0.2605, DD 66.73%).
- Caveat: close-based trigger approximation can differ from true intrabar limit fills.
