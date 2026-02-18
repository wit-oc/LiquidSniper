# Task 16 — LiquidSniper dependency threading + boundary enforcement

## Goal

Thread proposal dependencies into LiquidSniper while preserving strict non-bypass boundaries between strategy scoring, policy/risk gating, and execution adapters.

## Deliverables

- Dependency map: what is reused from current modules vs what is newly introduced.
- Boundary contract documenting:
  - strategy module cannot directly execute orders,
  - policy engine is required authority,
  - execution adapters consume only approved canonical intents.
- Audit trace requirements (`trace_id`, `policy_version`, `rulebook_ref`) enforced in all decision artifacts.

## Acceptance criteria

- A single flow diagram and contract doc show no strategy -> execution bypass path.
- Missing policy decision blocks downstream actions deterministically.
- Dependency map includes Blofin and on-chain paths explicitly.
