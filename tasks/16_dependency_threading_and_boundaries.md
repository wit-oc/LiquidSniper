# Task 16 — LiquidSniper dependency threading + boundary enforcement

## Goal

Thread proposal dependencies into LiquidSniper while preserving strict non-bypass boundaries between strategy scoring, policy/risk gating, and execution adapters.

## Deliverables

- Dependency map: what is reused from current modules vs what is newly introduced.
- Boundary contract documenting:
  - strategy module cannot directly execute orders,
  - policy engine is required authority,
  - execution adapters consume only approved canonical intents.
- Egress-isolation contract for Blofin path:
  - approved egress modes (`dedicated/static` preferred),
  - explicit no-main-account-egress reuse rule,
  - split-tunnel guidance when running on shared host,
  - endpoint/rate guardrails to reduce exchange abuse-risk flags.
- Audit trace requirements (`trace_id`, `policy_version`, `rulebook_ref`) enforced in all decision artifacts.

## Acceptance criteria

- A single flow diagram and contract doc show no strategy -> execution bypass path.
- Missing policy decision blocks downstream actions deterministically.
- Dependency map includes Blofin and on-chain paths explicitly.
- Blofin integration docs include egress isolation policy + stage-gate check (no progression past paper/read-only without stable egress posture).
