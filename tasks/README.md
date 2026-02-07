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

## Execution order
- `01_...` → `08_...`
