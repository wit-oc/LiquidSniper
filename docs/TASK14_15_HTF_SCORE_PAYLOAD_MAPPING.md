# Task 14/15 HTF Score Payload Mapping (v1)

Status: implementation contract (paper-mode only)  
Last updated: 2026-02-18

## Purpose

Define a deterministic mapping from HTF anchor-profile payloads (Task 14) into score inputs/outputs (Task 15) so replay runs produce stable, auditable decisions.

## Canonical profile map (source of truth)

| anchor_profile_id | htf_anchor_tf | itf_tf | ltf_trigger_tfs |
|---|---|---|---|
| `S` | `1D` | `4H` | `["1H","15m"]` |
| `I` | `4H` | `1H` | `["15m","5m"]` |
| `C` | `1H` | `15m` | `["5m","1m"]` |

Validation and fail-closed behavior are inherited from `docs/HTF_ANCHOR_PROFILE_CONTRACT_V1.md`.

## Input payload contract (score engine ingest)

Required fields for Task 15 scoring:

- `trace_id` (string)
- `anchor_profile_id` (`S|I|C`)
- `htf_anchor_tf` (string)
- `itf_tf` (string)
- `ltf_trigger_tfs` (string[])
- `regime_permission` (`allow|degrade|deny`)
- `regime_reason_codes` (string[] non-empty)
- `zone_priority_score` (0-100 number)
- `context_score` (0-100 number)
- `agent_confidence_score` (0-100 number, optional when agent stage skipped)
- `rulebook_ref` (string)
- `policy_version` (string)

## Deterministic mapping matrix

| Mapping key | Source field(s) | Transform | Output field | Reject reason code on failure |
|---|---|---|---|---|
| `profile_identity` | `anchor_profile_id` | enum validate (`S|I|C`) | `profile_valid=true` | `invalid_profile_id` |
| `profile_timeframes` | `htf_anchor_tf`,`itf_tf`,`ltf_trigger_tfs` | exact match against canonical profile map | `profile_tf_valid=true` | `profile_tf_mismatch` |
| `hierarchy_guard` | `htf_anchor_tf`,`itf_tf`,`ltf_trigger_tfs` | enforce `HTF > ITF > each LTF` | `tf_hierarchy_valid=true` | `invalid_tf_hierarchy` |
| `regime_gate` | `regime_permission`,`regime_reason_codes` | presence + non-empty reasons | `regime_gate_valid=true` | `missing_regime_gate` |
| `zone_stage` | `zone_priority_score` | clamp 0..100, preserve integer/decimal as provided | `zone_priority_score` | `invalid_zone_score` |
| `context_stage` | `context_score` | clamp 0..100 | `context_score` | `invalid_context_score` |
| `pre_score` | `zone_priority_score`,`context_score` | `0.55*zone + 0.45*context` | `pre_score` | `pre_score_compute_failed` |
| `agent_stage_gate` | `pre_score` | run agent only when `pre_score >= 60` | `agent_stage_eligible` | n/a |
| `agent_score_default` | `agent_confidence_score` | if not eligible -> force `0` | `agent_confidence_score_effective` | `invalid_agent_score` |
| `final_score` | `pre_score`,`agent_confidence_score_effective` | `0.70*pre + 0.30*agent` | `final_score` | `final_score_compute_failed` |
| `decision_floor` | `pre_score`,`regime_permission` | if `pre_score < 60` or `deny` -> `watch_only` | `decision_tier` | n/a |
| `decision_thresholds` | `final_score` (+ runbook gate) | >=70 `publish_candidate`; >=80 `high_priority`; else `watch_only` | `decision_tier` | `decision_policy_violation` |

## Decision policy resolution order

Apply in strict order:

1. **Schema/profile validation** (reject on any hard failure).
2. **Regime gate override**:
   - `deny` => `watch_only` (never promote).
   - `degrade` => max tier capped at `publish_candidate`.
3. **Score thresholds** from Hybrid Confluence v0.
4. **Runbook confluence gate override** (`docs/archive/2026-04-19-first-archive-pass/telegram-mobchart/HYBRID_CONFLUENCE_PIPELINE_SPEC.md` §4b):
   - missing primary confluences => `watch_only` regardless of score.

## Output payload contract (score engine egress)

- `trace_id`
- `anchor_profile_id`
- `pre_score`
- `agent_confidence_score_effective`
- `final_score`
- `decision_tier` (`reject|watch_only|publish_candidate|high_priority`)
- `decision_reason_codes` (ordered deterministic array)
- `rulebook_ref`
- `policy_version`

## Replay fixtures required for Task 14/15 completion

Minimum deterministic fixtures:

1. `S_allow_publish_candidate.json` — valid swing profile, pass primary gate, final score >=70.
2. `C_deny_watch_only.json` — valid scalp profile with `regime_permission=deny`.
3. `S_profile_tf_mismatch_reject.json` — invalid timeframe mapping.
4. `I_pre_score_below_floor_watch_only.json` — valid profile, `pre_score < 60`.
5. `C_degrade_caps_priority.json` — score would be high priority, but `degrade` caps to publish.

Each fixture must include expected `decision_tier` and ordered `decision_reason_codes`.

## Non-goals

- No live-order routing behavior.
- No strategy optimization/tuning in this contract.
- No profile-specific threshold divergence beyond explicit regime cap rules in v1.
