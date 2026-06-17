# V7 Admission Routing Spike Snapshot

Snapshot date: 2026-05-30

## Protected State

This spike does not overwrite the protected v7 125 bps baseline, the Quality Score 3 candidate, or any TradingView exports from the prior generalization run. It only reads existing telemetry and raw ignored Strategy Tester CSVs.

| Item | Value |
| --- | --- |
| Branch | `codex/unity-utm-feasibility-spike` |
| HEAD | `f5a58c1045feb7d1600a00729097044daae98851` |
| Source artifact | `tradingview/strategy/artifacts/v7_generalization_independent_variables` |
| Source verdict SHA-256 | `8a6aad535f36a61f3cd88659c2271e5a24d5e07dd7bf08d996f780e90d307729` |
| Source metrics SHA-256 | `b2c314e0f6224d7427324b162f9005bb088c8d2f1d201d5540fb8f4cb117f831` |
| Source manifest SHA-256 | `52682251102b4d8d749f28b336535c49e6f1e8c11edbee64537fab55c5abd1e3` |

## Boundary

This pass is an admission/routing spike. It does not change stop logic, does not generate a new Pine candidate, and does not run new TradingView exports. The first pass is intentionally telemetry-first so the next TradingView run can be narrowly scoped.

Current controls:

- Baseline 125 bps: protected static strategy control.
- Quality Score 3: prior best independent variable and current candidate control.
- ATR Regime Filter: rejected in prior verdict.
- Close Confirmed Stop: rejected in prior verdict.

## Evidence Inputs

- `tradingview/strategy/artifacts/v7_generalization_independent_variables/GENERALIZATION_INDEPENDENT_VARIABLES_VERDICT.md`
- `tradingview/strategy/artifacts/v7_generalization_independent_variables/generalization_independent_variables_metrics.md`
- `tradingview/strategy/.telemetry/outputs/v7_generalization_independent_variables/v7-generalization-baseline-125bps/liquidity_scope_sanity_metrics.json`
- `tradingview/strategy/.telemetry/outputs/v7_generalization_independent_variables/v7-generalization-quality-score-3/liquidity_scope_sanity_metrics.json`
- Ignored raw Strategy Tester CSVs referenced by the telemetry `sourceFile` fields.

## Test Shape

The analyzer parses the encoded entry signal from raw CSVs so rules can be tested from entry-time or calibration-time traits:

- active quality score
- level quality
- non-level quality residual
- MSS age
- alert age where available
- strength age and strength slope
- entry risk bps
- ATR bps
- entry range / ATR
- stop distance / ATR
- symbol/timeframe routing
- prior-window stability gates

Rules that require full-history knowledge are labeled as diagnostics, not implementation-ready candidates.
