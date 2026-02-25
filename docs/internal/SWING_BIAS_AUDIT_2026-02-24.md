# Swing Bias Audit — 2026-02-24

## Scope
Reviewed swing bias decision path after adding decomposition diagnostics (`v_htf`, `v_itf`, `v_structure`, `v_sr_context`) and weighted confidence.

## Method
- Verified deterministic weighted aggregation in policy gate.
- Added regression coverage (`tests/test_paper_policy.py::test_evaluate_gates_swing_bias_weighted_vote`).
- Inspected gate payload fields exported through run artifacts and debug API.

## Findings
- Neutral outcomes occur when component disagreement keeps `|bias_conf| < swing_bias_neutral_band`.
- Strongly aligned votes permit expected direction and clear `BIAS_NOT_PERMITTED`.
- No derivation artifact detected in current implementation path.

## Decision
- **No corrective patch applied in T9** (not warranted by audit evidence).
- Keep neutral band default at `0.55` pending fresh live-paper sample.

## Follow-up
- Re-run audit on next 24h swing sample after tuning rollout and compare first-fail bias share.
