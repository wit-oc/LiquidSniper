# Intraday Knob Gating (Autonomy Guard)

Updated: 2026-02-28 18:26 ET
Source: `intraday_revisit/artifacts/sweeps/miniwave_v2_1/*`

## GATED (do not tune until unblocked)
These knobs showed near-zero sensitivity in prior v2.1 neighborhood.

- `near_retest_penalty_max` (0.8 vs 1.1)

## UNGATED AFTER INSTRUMENTATION/DESATURATION
- `trigger_score_min` is now ungated for future cycles after strict-retest and score desaturation changes (2026-02-28 19:30 ET). Re-test sensitivity in next runs.

Observed pattern: repeated attempts with these changes produced same `total_trades`, same `avg_pf`, same/worse `worst_dd_pct`.

## ALLOWED FOR NEXT ITERATIONS
- `stop_buffer_frac` (bounded by PARAM_GUARDRAILS)
- `trigger_score_min` / `score_gate_min` (bounded by PARAM_GUARDRAILS)
- (after entry-quality pass) `strict_retest_bps_max`, `near_retest_bps_max`

## RE-GATED NOW
- `rr_tp2` (degenerate drift observed down to 0.1R; re-enable only after explicit approval)

## Unblock rule
A gated knob may be re-enabled only if at least one upstream gate/funnel metric changes materially in telemetry (e.g., strict/near retest rates, score_ok rates, entry mix) after another parameter change.
