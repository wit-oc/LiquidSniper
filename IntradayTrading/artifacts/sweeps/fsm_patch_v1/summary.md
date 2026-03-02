# FSM Patch v1 (one-pass)

## Scope implemented
- Replaced neutral-dependent behavior in active decision path with **persistent bullish/bearish regime state**.
- Added CHoCH -> BoS flip confirmation logic before regime flips.
- Added entry FSM lifecycle in runner:
  - `IDLE -> WATCH` when regime + POI context is valid.
  - `WATCH -> TRIGGER` only when fib directional + candle confirmation + retest quality pass (and trigger score threshold).
  - `WATCH -> INVALID` on acceptance failure or structure invalidation.
  - `WATCH -> EXPIRED` on timeout.
- Kept fib + candle in trigger path (not post-hoc).
- Extended telemetry with regime/FSM transition fields and reasons.

## Files changed
- `intraday_revisit/engine/structure.py`
  - Added `RegimeState`, `RegimePoint`, `RegimeTransition`, `project_regime(...)`.
- `intraday_revisit/engine/runner.py`
  - Added persistent regime FSM (no neutral active regime).
  - Added WATCH/TRIGGER/INVALID/EXPIRED flow.
  - Added telemetry fields for regime + entry FSM transitions.
- `intraday_revisit/tests/test_structure.py`
  - Added CHoCH->BoS regime flip test.
- `intraday_revisit/tests/test_runner.py`
  - Updated harness config for deterministic trigger path in test fixtures.
- `intraday_revisit/tests/test_runner_logs.py`
  - Added assertions for regime/FSM telemetry fields.

## Validation (BTC-first)
Baseline used: `intraday_revisit/artifacts/initial_run_v4`.
Patched run: `intraday_revisit/artifacts/sweeps/fsm_patch_v1`.

- Metrics report: no change vs baseline (both baseline + patched are zero-trade under current default cost/gate assumptions).
- BTC telemetry funnel unchanged at high level (no entries in either run).
- Full machine-readable output: `intraday_revisit/artifacts/sweeps/fsm_patch_v1/result.json`.

## Test status
Executed targeted deterministic suite:

```bash
python3 -m pytest \
  intraday_revisit/tests/test_structure.py \
  intraday_revisit/tests/test_runner.py \
  intraday_revisit/tests/test_runner_logs.py \
  intraday_revisit/tests/test_signals.py -q
```

Result: `10 passed`.

Note: full `intraday_revisit/tests` run still includes an unrelated pre-existing failure in `test_first_pass_metrics.py` expecting a different `Trade(...)` constructor contract.
