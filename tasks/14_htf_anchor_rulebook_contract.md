# Task 14 — HTF-anchor rulebook contract

## Goal

Formalize a deterministic timeframe-anchor contract so the strategy can run consistently across swing/intraday/scalp profiles.

## Deliverables

- Rulebook profile schema (e.g., `swing|intraday|scalp`) including:
  - `anchor_profile_id`
  - `htf_anchor_tf`
  - `itf_tf`
  - `ltf_trigger_tfs`
  - profile-specific viability/risk thresholds
- Regime-permission gate fields integrated into analysis payloads.
- Documentation update with canonical profile defaults and constraints.

## Acceptance criteria

- Every analysis run can be tagged with one valid anchor profile.
- Invalid profile/timeframe combinations are rejected deterministically.
- Replay fixtures include at least one 1D-anchor case and one 1H-anchor case.
