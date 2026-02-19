# Task 21 — Candle quality gates + timeframe aggregation policy

## Goal

Ensure canonical candle data is decision-grade before it is consumed by strategy scoring.

## Deliverables

- Candle quality checks: gap detection, stale detection, dedupe, monotonic timestamp checks.
- Timeframe aggregation policy (derive HTF from lower TF when valid) and validation logic.
- Feed health reason codes for quality-gate failures.

## Acceptance criteria

- Missing/stale candle conditions are machine-detected and persisted.
- Invalid candle windows fail closed for decision promotion.
- Aggregated HTF candles match expected deterministic transformations.
