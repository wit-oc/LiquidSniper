# V7 QS3 Hydrated Canary Revalidation

Date: 2026-06-14

## Verdict

Status: `failed_current_layout_state`

The ETH hydrated reuse canary no longer proves the V7 QS3 baseline in the current TradingView layout state.

The harness now correctly rejects the false pass and distinguishes two separate bad states:

- Prior contaminated state: Pine Editor showed V7 code while the active Strategy Tester report was `Unity UTM Strategy v6 Fidelity Audit M15`.
- Latest clean state: Pine Editor was closed, but TradingView exposed no Strategy Tester/report panel for the target V7 QS3 instance.
- Required report: `Unity UTM Strategy v7 Generalization IV Quality Score 3`
- False chart-level selection caught earlier: `All data`
- Required Strategy Tester selection: `Entire history|All history`
- Required visible start: on or before `2024-01-01`

## Evidence

Latest strict canary after Pine overlay cleanup:

`artifacts/v7_deep_backtest_date_window_proof/tradingview/automation/v7-qs3-reuse-existing-manual-instance-eth-perp/2026-06-15T00-35-46-904Z-deep-date-window-matrix/pine-text-matrix-report.json`

This failed with `Could not find Strategy Report/Strategy Tester/Tester` while running in existing-instance reuse mode. The captured page text and controls show the chart, layout `Sherlock-Copy-v3`, vendor indicators, and the Pine/Products/Object Tree controls, but no V7 QS3 strategy title and no Strategy Tester panel.

Object Tree verification:

`artifacts/v7_deep_backtest_date_window_proof/tradingview/automation/v7-qs3-reuse-existing-manual-instance-eth-perp/2026-06-15T00-51-39-053Z-inspect-controls/body.txt`

The Object Tree lists drawings plus attached studies such as `Multi-Timeframe Exponential Moving Average`, `HTF Phase 1 Structure v3.3 (structure-first)`, `AIO Trend - [Unity] - V2`, `The Oracle AIO - [Unity] - V2`, and `The Oracle Strength - [Unity] - V2`. It does not list `Unity UTM Strategy v7 Generalization IV Quality Score 3`, confirming the current layout state is missing the required chart-attached strategy instance.

Products menu verification:

`artifacts/v7_deep_backtest_date_window_proof/tradingview/automation/v7-qs3-reuse-existing-manual-instance-eth-perp/2026-06-15T00-50-45-667Z-inspect-controls/body.txt`

The Products menu exposes `Screeners`, `Pine Editor`, `Calendars`, `News Flow`, `Portfolio`, `Fundamental Graphs`, `Yield Curves`, `Options`, and `Macro Maps`; it does not expose a Strategy Tester recovery route.

Layout menu verification:

`artifacts/v7_deep_backtest_date_window_proof/tradingview/automation/v7-qs3-reuse-existing-manual-instance-eth-perp/2026-06-15T00-55-59-616Z-inspect-controls/body.txt`

The layout menu shows the current active layout `Sherlock-Copy-v3` plus recently used layouts `SherlockView` and two `Unnamed` layouts on other routes. No V7-specific layout label is visible. Loading an alternate layout may be a valid manual recovery path, but the automation did not switch layouts because that would mutate the current TradingView state.

Earlier strict canary with active-title proof:

`artifacts/v7_deep_backtest_date_window_proof/tradingview/automation/v7-qs3-reuse-existing-manual-instance-eth-perp/2026-06-15T00-25-00-295Z-deep-date-window-matrix/pine-text-matrix-report.json`

Previous false-positive canary that is now rejected by the hardened gates:

`artifacts/v7_deep_backtest_date_window_proof/tradingview/automation/v7-qs3-reuse-existing-manual-instance-eth-perp/2026-06-15T00-16-20-429Z-deep-date-window-matrix/pine-text-matrix-report.json`

Previous known-good canary:

`artifacts/v7_deep_backtest_date_window_proof/tradingview/automation/v7-qs3-reuse-existing-manual-instance-eth-perp/2026-06-13T03-31-42-209Z-deep-date-window-matrix/BINANCE_ETHUSDT.P/15m/BINANCE_ETHUSDT.P_15m_strategy.csv`

## Harness Fixes

`artifacts/v7_deep_backtest_date_window_proof/tv_deep_backtest_date_window_matrix.mjs` now:

- reads the active Strategy Tester report title from the backtesting panel instead of accepting any matching body text;
- ignores Pine Editor title text when proving the active report;
- attempts to close the Pine overlay before looking for the Strategy Tester report;
- rejects chart-level `All data` when the run requires Strategy Tester `Entire history|All history`;
- requires an entire-history visible start no later than the configured `minimumStart`;
- rejects no-trade Strategy Tester reports unless a run explicitly allows no-trade data.

The reuse and PDF-filter canary manifests now require:

- `requiredSelectionPattern: "Entire history|All history"`
- `minimumStart: "2024-01-01"`

## Implication

Do not treat the edited PDF-filter strategy as live-validated yet.

Next required step is state recovery: restore/select the V7 QS3 chart-attached strategy and manual Strategy Tester report that produced the 76-trade ETH baseline, or create a new proven hydrated state that reproduces that baseline before testing the refined strategy. In the current `Sherlock-Copy-v3` layout, the required V7 QS3 strategy object is not attached. Candidate manual recovery routes are the recently used `SherlockView` layout or one of the `Unnamed` layouts, but each must be revalidated against the ETH 76-trade baseline before use.
