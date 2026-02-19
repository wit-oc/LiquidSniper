# Task 25 — Blofin native adapter fallback (conditional)

## Goal

Provide a controlled fallback adapter if CCXT cannot satisfy required Blofin data contract semantics.

## Deliverables

- Gap assessment between CCXT coverage and required Blofin fields/endpoints.
- Native Blofin market-data adapter behind `MarketDataProvider` interface.
- Config flag to choose provider path without changing downstream strategy logic.

## Acceptance criteria

- Native adapter is only enabled intentionally via config.
- Downstream strategy/analysis code remains provider-agnostic.
- Adapter passes the same quality/rate-limit contracts as CCXT path.
