# OpenClaw Orchestration Bootstrap (Task 13)

Hybrid analysis background runs must load rulebooks/secrets at runtime.

## Required runtime inputs

- `LS_RULEBOOK_PATH` (required): path to user-owned strategy rubric file.
- `LS_RULEBOOK_REF` (optional): human-readable reference/version string.
- `LS_ARTIFACT_ROOT` (optional, default `/data/artifacts`): shared mount used by backend + diagnostic UI.

## Secrets policy

- Secrets are loaded from environment variables only (in-memory at runtime).
- Never commit secret values to source control.
- Call `build_run_bootstrap(required_secret_env=(...))` to enforce required secret presence.

## Python entrypoint

Use `liquidsniper.core.orchestration`:

- `OrchestrationConfig.from_env()` -> validates externalized rulebook path + shared mount config
- `load_rulebook(...)` -> validates/fingerprints rulebook file
- `load_required_secrets(...)` -> enforces env-only secret loading
- `build_run_bootstrap(...)` -> one-call validation bundle for background run orchestration
