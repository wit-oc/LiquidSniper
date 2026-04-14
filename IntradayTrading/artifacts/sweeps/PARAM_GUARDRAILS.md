# Parameter Guardrails (Intraday Revisit)

Updated: 2026-03-01 00:36 ET
Purpose: prevent degenerate tuning regions during autonomy cycles.

## Hard bounds (do not cross)
- `rr_tp2`: **[1.5, 3.0]**
  - Rationale: TP2 below 1.5R collapses payoff geometry and produced degenerate results.
- `stop_buffer_frac`: **[0.0010, 0.0025]**
  - Rationale: below 0.001 causes immediate stopout fragility; above 0.0025 over-widens risk and degrades PF.
- `trigger_score_min`: **[6.0, 8.5]**
  - Rationale: below 6.0 over-admits weak setups; above 8.5 starves throughput.
- `score_gate_min`: **[5.5, 7.5]**
  - Rationale: outside this band was either non-discriminative or over-restrictive in current scoring regime.
- `strict_retest_bps_max`: **[8, 20]**
- `near_retest_bps_max`: **[16, 40]**

## Temporarily gated knobs
- `rr_tp2` (until entry-quality improvements land)
- `near_retest_penalty_max` (low sensitivity in current flow)

## Preferred near-term tuning order
1) entry-quality/confirmation gates (especially ETH short weakness)
2) `trigger_score_min` and `score_gate_min` (within bounds)
3) `stop_buffer_frac` fine-tune (within bounds)

## Rule
If a proposed autonomous tune violates bounds/gating above, skip and emit:
`BLOCKED: proposed tune violates PARAM_GUARDRAILS | NEXT: choose an in-bounds non-gated knob`.
