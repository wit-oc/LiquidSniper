"""OpenClaw orchestration bootstrap helpers for hybrid analysis runs.

This module is intentionally side-effect free: it only validates runtime inputs
(rulebook path, env-backed secrets, shared artifact mount contract).
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RulebookBootstrap:
    """Metadata for an external user-owned rulebook artifact."""

    path: Path
    ref: str
    sha256: str


@dataclass(frozen=True)
class OrchestrationConfig:
    """Parameterization contract for background analysis runs."""

    artifact_root: Path
    rulebook_path: Path
    rulebook_ref: str

    @classmethod
    def from_env(cls) -> "OrchestrationConfig":
        artifact_root = Path(os.getenv("LS_ARTIFACT_ROOT", "/data/artifacts"))

        rulebook_path_raw = os.getenv("LS_RULEBOOK_PATH")
        if not rulebook_path_raw:
            raise ValueError("LS_RULEBOOK_PATH is required (external user rulebook file)")

        rulebook_path = Path(rulebook_path_raw)
        rulebook_ref = os.getenv("LS_RULEBOOK_REF", f"rulebook://local/{rulebook_path.name}")
        return cls(
            artifact_root=artifact_root,
            rulebook_path=rulebook_path,
            rulebook_ref=rulebook_ref,
        )


@dataclass(frozen=True)
class RunBootstrap:
    """Validated runtime bootstrap bundle for orchestrated runs."""

    config: OrchestrationConfig
    rulebook: RulebookBootstrap
    secrets: dict[str, str]


def load_rulebook(path: Path, *, ref: str) -> RulebookBootstrap:
    """Validate and fingerprint an external rulebook file."""
    expanded = path.expanduser().resolve()
    if not expanded.exists() or not expanded.is_file():
        raise FileNotFoundError(f"Rulebook file not found: {expanded}")

    raw = expanded.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError(f"Rulebook file is empty: {expanded}")

    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return RulebookBootstrap(path=expanded, ref=ref, sha256=digest)


def load_required_secrets(required_env: tuple[str, ...]) -> dict[str, str]:
    """Load required secret values from env; never from repo defaults."""
    missing = [name for name in required_env if not os.getenv(name)]
    if missing:
        raise ValueError(f"Missing required secret env vars: {', '.join(sorted(missing))}")

    return {name: os.environ[name] for name in required_env}


def build_run_bootstrap(*, required_secret_env: tuple[str, ...]) -> RunBootstrap:
    """Build a validated bootstrap context for background OpenClaw runs."""
    config = OrchestrationConfig.from_env()
    rulebook = load_rulebook(config.rulebook_path, ref=config.rulebook_ref)
    secrets = load_required_secrets(required_secret_env)
    return RunBootstrap(config=config, rulebook=rulebook, secrets=secrets)
