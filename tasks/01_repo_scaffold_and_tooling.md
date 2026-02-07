# Task 01 — Repo scaffold + tooling

## Goal

Create the initial code scaffold so subsequent tasks have a home.

## Deliverables

- Python package layout (proposal):
  - `liquidsniper/core/` (db, parsing, card engine)
  - `liquidsniper/ingestor/` (telethon runtime)
  - `liquidsniper/web/` (streamlit app)
- `pyproject.toml` (or requirements.txt) with pinned deps
- `pytest` configured
- `ruff` (optional) + pre-commit (optional)

## Acceptance criteria

- `pytest` runs in CI/local (even if only a dummy test initially)
- Import paths work (`python -m liquidsniper...`)
