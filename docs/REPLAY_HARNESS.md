# Deterministic Replay Harness (MVP v1)

## Purpose

Run a fixed fixture pack through LiquidSniper scoring and verify outputs against golden expected values.

This gives us a cheap regression signal for:
- deterministic score computation
- threshold/decision behavior
- status-path stability before paper-trade runs

## Files

- Engine: `liquidsniper/core/replay_harness.py`
- Fixture pack: `tests/fixtures/replay_pack_v1.json`
- Tests: `tests/test_replay_harness.py`

## Local run

```bash
python3 -m pytest -q tests/test_replay_harness.py
```

## Fixture format (summary)

Each case contains:
- `event`: deterministic inputs from parser/enrichment path
- `context`: optional context-stage features
- `agent`: optional agent-stage confidence + tv status
- `expected`: golden outputs (scores + decision)

When `expected` is present, replay harness compares exact values and reports mismatches.
