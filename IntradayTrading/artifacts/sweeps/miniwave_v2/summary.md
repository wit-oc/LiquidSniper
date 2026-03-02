# miniwave_v2 summary

Cost assumptions: fee=5.0 bps/side, slippage=2.0 bps/side, funding=1.0 bps/8h.

## Ranked shortlist
1. attempt 1 | avg_pf=0.685 | worst_dd_pct=96.89 | trades=239 | pass=False
2. attempt 3 | avg_pf=0.674 | worst_dd_pct=98.41 | trades=170 | pass=False
3. attempt 2 | avg_pf=0.635 | worst_dd_pct=93.96 | trades=201 | pass=False

Constraint verdict: FAIL (no config met trades>100, PF>1, DD<=15%).

## BLOCKED
No blocker in execution; blocker is strategy quality under current logic/cost assumptions.
Smallest next step: widen sweep to lower trigger_score_min and tune stop_buffer_frac / rr_tp2 for PF lift.
