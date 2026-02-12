# Task 13 — OpenClaw skill orchestration, rulebook bootstrap, and secrets flow

## Goal

Run analysis as a background OpenClaw skill/pipeline with parameterized inputs, external rulebook, and secure secret loading.

## Deliverables

- Orchestration entrypoint for scheduled/background runs.
- Rulebook bootstrap model:
  - user-provided strategy rubric prompt file
  - not shipped as hardcoded universal rulebook
- Secrets policy:
  - values loaded from keychain/secret manager
  - injected as env vars in memory at runtime
  - never committed to repo
- Shared mount config for backend + diagnostic UI container.

## Acceptance criteria

- Pipeline can run with user-specific rulebook and env-only secrets.
- No secrets or personal rulebook embedded in source defaults.
