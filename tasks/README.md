# Tasks (Phase 1)

These tasks are generated from `specs/` and are intended to be executed **in order**.

Conventions:
- Each task has: Goal, Deliverables, Acceptance Criteria.
- Prefer small PR-sized chunks.
- Add/extend automated tests wherever feasible.

## Ownership

Default: Wit (agent) drives sequencing, reviews, and integration.
Implementation can be done either by:
- **Agent** (Wit)
- **Codex CLI** (run by Redact) for faster code generation

## Suggested assignment (Phase 1)

- Task 01 — **Codex CLI** (scaffold + deps + pytest)
- Task 02 — **Codex CLI** (schema + migrations + tests)
- Task 03 — **Codex CLI** (parser + tests)
- Task 04 — **Codex CLI** (card engine + tests)
- Task 05 — **Agent** (Telethon wiring is sensitive; agent can implement with careful review; optionally Codex with tighter prompts)
- Task 06 — **Codex CLI** (Streamlit UI)
- Task 07 — **Agent** (Docker/compose + volume/session persistence; can delegate with careful review)
- Task 08 — **Agent** (runbook + validation + CI)

Rationale:
- Codex is great for high-volume code + tests.
- Agent should own ops/security-sensitive glue and final integration.

## Extended assignment (Hybrid pipeline)

- Task 09 — **Agent** (analysis run contract + schema additions)
- Task 10 — **Agent** (would-alert simulation mode)
- Task 11 — **Agent** (TV artifact link model + shared mount contract)
- Task 12 — **Codex CLI** (minimal diagnostic UI updates)
- Task 13 — **Agent** (OpenClaw orchestration + rulebook/bootstrap + secrets policy)

## Strategy automation alignment assignment

- Task 14 — **Agent** (HTF-anchor rulebook contract + profile constraints)
- Task 15 — **Agent** (strategy score mapping + deterministic reason-code alignment)
- Task 16 — **Agent** (dependency threading + non-bypass boundary contract)
- Task 17 — **Agent** (two-pass adversarial validation gates)
- Task 18 — **Agent** (integrated vs separate execution-core packaging decision)

## Execution order
- `01_...` → `08_...`
- `09_...` → `13_...` (backend-first hybrid confluence pipeline)
- `14_...` → `18_...` (strategy automation alignment + governance hardening)

## Initiative-runner note

For this phase we are operating as a sequential initiative build (not necessarily one PR per task), with frequent commits/pushes and review checkpoints.
