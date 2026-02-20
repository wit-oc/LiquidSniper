from pathlib import Path


def test_makefile_contains_paper_daemon_targets() -> None:
    text = Path("Makefile").read_text(encoding="utf-8")
    assert "paper-daemon-up:" in text
    assert "paper-daemon-down:" in text
    assert "paper-daemon-logs:" in text
    assert "paper-scorecard-once:" in text
    assert "docker-compose.paper.yml" in text
