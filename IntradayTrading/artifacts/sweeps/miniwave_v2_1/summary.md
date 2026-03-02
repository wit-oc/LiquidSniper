# miniwave_v2.1 narrow sweep

Cost assumptions: fee=5.0 bps/side, slippage=2.0 bps/side, funding=1.0 bps/8h.
Trend alignment: hard (allow_neutral_bias=False).

## Search space
- trigger_score_min: [6.4, 6.8]
- stop_buffer_frac: [0.0009, 0.0011]
- rr_tp2: [2.2, 2.5]
- near_retest_penalty_max: [0.8, 1.1]
- total attempts: 16

## Best by ranking (avg PF desc, DD asc, trades desc)
- attempt 007
- avg_pf=0.690
- worst_dd_pct=95.44
- total_trades=240
- pass_constraints=False
- params={"zone_width": 0.0015, "retest_max_bars": 8, "reclaim_buffer_frac": 0.00035, "momentum_min_frac": 0.0012, "trend_slope_min": 0.0002, "chop_slope_abs_max": 0.00012, "strict_retest_bps_max": 18.0, "near_retest_bps_max": 24.0, "score_gate_min": 5.8, "risk_pct_high_conf": 1.6, "trigger_score_min": 6.4, "stop_buffer_frac": 0.0011, "rr_tp2": 2.5, "near_retest_penalty_max": 0.8}

## Constraints check
- trades > 100: PASS (240)
- PF > 1: FAIL (0.690)
- DD <= 15%: FAIL (95.44%)

Constraint verdict: FAIL (no profile met trades>100, PF>1, DD<=15%).
