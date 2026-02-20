from pathlib import Path


def test_compose_paper_contains_services_and_volume() -> None:
    p = Path("docker-compose.paper.yml")
    text = p.read_text(encoding="utf-8")
    assert "paper-runner:" in text
    assert "scorecard-worker:" in text
    assert "LIQUIDSNIPER_MODE=paper" in text
    assert "liquidsniper_data:" in text


def test_env_example_contains_bankroll() -> None:
    p = Path(".env.paper.example")
    text = p.read_text(encoding="utf-8")
    assert "LIQUIDSNIPER_PAPER_BANKROLL_USD" in text
    assert "LIQUIDSNIPER_DB_PATH" in text
