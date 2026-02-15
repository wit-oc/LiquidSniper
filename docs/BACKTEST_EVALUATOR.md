# Backtest Evaluator Harness (MVP v1)

## Purpose

Compute first-pass strategy quality guardrails from deterministic case sets:
- expectancy (R)
- max drawdown proxy (R)
- p95 latency budget

Outputs:
- structured summary dict
- markdown report for task/status updates

## Files

- Engine: `liquidsniper/core/backtest_eval.py`
- Fixture input: `tests/fixtures/backtest_eval_cases_v1.json`
- Tests: `tests/test_backtest_eval.py`

## Local test run

```bash
python3 -m pytest -q tests/test_backtest_eval.py
```

## Notes

Thresholds default to MVP v1 guardrails and can be overridden via `EvalThresholds`.
