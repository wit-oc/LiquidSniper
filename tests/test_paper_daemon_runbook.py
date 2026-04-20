from pathlib import Path


def test_paper_daemon_runbook_contains_operator_commands() -> None:
    text = Path("docs/archive/2026-04-19-first-archive-pass/paper-runtime/PAPER_DAEMON_RUNBOOK_V1.md").read_text(encoding="utf-8")
    assert "make paper-daemon-up" in text
    assert "make paper-daemon-down" in text
    assert "make paper-daemon-logs" in text
    assert "make paper-scorecard-once" in text
