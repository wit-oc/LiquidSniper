from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from liquidsniper.core.orchestration import (
    build_run_bootstrap,
    load_required_secrets,
    load_rulebook,
)


def test_load_rulebook_hashes_external_file(tmp_path: Path) -> None:
    rulebook = tmp_path / "my_rulebook.md"
    body = "score >= 80 and context >= 70"
    rulebook.write_text(body, encoding="utf-8")

    loaded = load_rulebook(rulebook, ref="rulebook://user/v1")

    assert loaded.path == rulebook.resolve()
    assert loaded.ref == "rulebook://user/v1"
    assert loaded.sha256 == hashlib.sha256(body.encode("utf-8")).hexdigest()


def test_load_required_secrets_raises_for_missing() -> None:
    with pytest.raises(ValueError, match="Missing required secret env vars"):
        load_required_secrets(("LS_API_KEY", "LS_TELEGRAM_TOKEN"))


def test_build_run_bootstrap_requires_external_rulebook(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("LS_RULEBOOK_PATH", raising=False)
    monkeypatch.setenv("LS_TELEGRAM_TOKEN", "test-token")

    with pytest.raises(ValueError, match="LS_RULEBOOK_PATH is required"):
        build_run_bootstrap(required_secret_env=("LS_TELEGRAM_TOKEN",))

    rulebook = tmp_path / "rulebook.md"
    rulebook.write_text("external strategy", encoding="utf-8")

    monkeypatch.setenv("LS_RULEBOOK_PATH", str(rulebook))
    monkeypatch.setenv("LS_RULEBOOK_REF", "rulebook://redact/hybrid-v1")

    bootstrap = build_run_bootstrap(required_secret_env=("LS_TELEGRAM_TOKEN",))

    assert bootstrap.config.rulebook_path == rulebook
    assert bootstrap.config.rulebook_ref == "rulebook://redact/hybrid-v1"
    assert bootstrap.secrets["LS_TELEGRAM_TOKEN"] == "test-token"
