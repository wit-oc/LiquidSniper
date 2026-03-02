# DCA comparison v1

Baseline source: artifacts/sweeps/miniwave_v2_1_autonomy/iter_2026-02-28-1900_stop_buffer_frac_0p0013.json (best post-instrumentation avg_pf).

## Fill model
- Signal generation unchanged (same entries from runner).
- DCA triggers are adverse-move fractions from entry toward fixed invalidation stop, evaluated on close prices.
- TP is recalculated after each realized fill from updated blended entry and fixed stop using RR=rr_tp2.
- Planning assumption for RR design: intended tranche set is the target allocation; risk weights sum to 1.0 (no risk over-allocation).
- Execution realism: if TP is reached before full DCA completion, TP is applied only to currently filled size (remaining tranches stay unfilled).

## Baseline vs DCA-50/50
- total_trades: 74.0000 -> 74.0000 (+0.0000)
- avg_pf: 0.3572 -> 0.2655 (-0.0917)
- worst_dd_pct: 28.6895% -> 19.5054% (-9.1841%)
- total_net: -4726.3698 -> -3586.9557 (+1139.4141)
- avg_win_rate: 37.2059% -> 37.2059% (+0.0000%)

## Baseline vs DCA-30/30/40
- total_trades: 74.0000 -> 74.0000 (+0.0000)
- avg_pf: 0.3572 -> 0.2175 (-0.1397)
- worst_dd_pct: 28.6895% -> 14.3830% (-14.3065%)
- total_net: -4726.3698 -> -2798.9823 (+1927.3875)
- avg_win_rate: 37.2059% -> 37.2059% (+0.0000%)

## Conclusion
- No DCA variant improved PF/DD jointly versus baseline: both DCA models reduced PF, while drawdown improved versus baseline.
- Best PF among DCA variants: dca_50_50 (PF 0.2655 vs baseline 0.3572).
- Best DD among DCA variants: dca_30_30_40 (DD 14.38% vs baseline 28.69%).
- Caveat: close-based trigger approximation can differ from true intrabar limit fills.
