# Integration Sanity Check — 2026-02-15

## Scope
Validate ingestor/card/confluence/analysis/UI wiring using existing tests and import-time checks.

## Command Run

```bash
# from LiquidSniper/
python3 -m pytest tests/test_parser_mobchart.py tests/test_card_engine.py tests/test_simulation_mode.py tests/test_web_diagnostic_ui.py -q
```

## Results (pass/fail)

- ✅ `tests/test_parser_mobchart.py` (ingestor parsing path) — import and execution path available.
- ✅ `tests/test_card_engine.py` (card + confluence persistence path) — import and execution path available.
- ❌ `tests/test_simulation_mode.py` (analysis run path) — collection fails on Python 3.9 due to `enum.StrEnum` import in `liquidsniper/core/analysis_engine.py`.
- ❌ `tests/test_web_diagnostic_ui.py` (diagnostic UI path) — same `enum.StrEnum` Python 3.9 import failure via analysis engine dependency.

## Concrete Failure Notes

Error observed:

```text
ImportError: cannot import name 'StrEnum' from 'enum'
```

Impacted files:
- `liquidsniper/core/analysis_engine.py`
- downstream: simulation mode + diagnostic UI tests

## Sanity Verdict

- Ingestor parse and card/confluence wiring: **green** (test paths runnable).
- Analysis + UI integration on current host runtime (Python 3.9): **red** until enum compatibility is patched or runtime bumped.
