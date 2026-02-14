from __future__ import annotations

from pathlib import Path

from liquidsniper.core.replay_harness import run_fixture_pack


def _fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "replay_pack_v1.json"


def test_replay_pack_matches_golden_expectations() -> None:
    report = run_fixture_pack(_fixture_path())
    assert report["total"] == 3
    assert report["failed"] == 0, report["failures"]


def test_replay_harness_is_deterministic() -> None:
    first = run_fixture_pack(_fixture_path())
    second = run_fixture_pack(_fixture_path())
    assert first["results"] == second["results"]
