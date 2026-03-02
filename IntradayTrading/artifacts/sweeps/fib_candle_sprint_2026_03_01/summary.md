# Fib + Candle Sprint (2026-03-01)

Attempts tracked (strict-policy compliant): 2
BTC-first ranking key: btc_pf desc, btc_dd asc, btc_trades desc, eth_pf desc.

Best strict-compliant attempt: 017
- BTC: PF=0.000, DD=5.31%, trades=2
- ETH(diag): PF=0.000, DD=0.00%, trades=0
- Avg PF=0.000, worst DD=5.31%, total trades=2
- Params: {"zone_width": 0.0015, "retest_max_bars": 8, "reclaim_buffer_frac": 0.00035, "momentum_min_frac": 0.0012, "trend_slope_min": 0.0002, "chop_slope_abs_max": 0.00012, "strict_retest_bps_max": 18.0, "near_retest_bps_max": 24.0, "score_gate_min": 5.8, "risk_pct_high_conf": 1.6, "trigger_score_min": 6.8, "stop_buffer_frac": 0.0011, "rr_tp2": 2.2, "near_retest_penalty_max": 0.8, "fib_long_min": 0.618, "fib_long_max": 0.786, "fib_short_min": 0.618, "fib_short_max": 0.786, "retest_ordinal_max_bonus": 0.9, "retest_ordinal_decay": 0.3, "enable_candle_confirmation": true, "enable_fib_directional_gate": true, "candle_score_min": 1.6}

Latest attempt (018) delta:
- Relaxed candle_score_min from 1.6 -> 1.2 under strict premium short fib gate (0.618-0.786).
- BTC: PF=0.000, DD=17.96%, trades=3
- ETH(diag): PF=0.000, DD=3.39%, trades=1

Latest attempt (019) delta:
- Raised trigger_score_min from 6.8 -> 7.2 while keeping strict premium short fib gate (0.618-0.786).
- BTC: PF=0.000, DD=5.31%, trades=2
- ETH(diag): PF=0.000, DD=0.00%, trades=0
