# Pre-merge Checklist

Use this checklist before merging any task branch into `main`.

## Branch hygiene

- [ ] Branch is scoped to a single task (or clearly related subtask).
- [ ] No generated artifacts committed (`*.egg-info`, caches, local DB files).
- [ ] Commit messages are clear and scoped.

## Local validation

- [ ] Virtual env active (`.venv`).
- [ ] Dependencies installed for this branch.
- [ ] `pytest -q` passes.
- [ ] `python -c "import liquidsniper"` passes.

## Spec/task alignment

- [ ] Implementation matches task acceptance criteria.
- [ ] If schema changes, migration is included and idempotent.
- [ ] If parsing changes, tests include representative payload fixtures.

## Docker/ops impact

- [ ] Any required env vars are documented.
- [ ] Persistent state paths are unchanged or documented (`/data/liquidsniper.sqlite`, `/data/telethon.session`).

## Docs updates

- [ ] Relevant docs updated (`specs/`, `tasks/`, runbook/setup docs).

## Merge readiness

- [ ] PR includes summary + test evidence.
- [ ] At least one reviewer pass (Wit/Redact flow).
