# V7 Admission Routing Verdict

Generated: 2026-05-30

## Decision

The path to broader cross-coin success is most likely a timeframe routing layer, not another entry-quality component filter or stop adjustment.

The single most promising rule family is:

- Keep `Quality Score 3` as the entry-quality control.
- Add a simple `5m only` routing layer as the next implementation candidate.
- Do not use 15m for broad deployment until a separate rule can prove when 15m should be admitted.

This is not yet proof of fully universal deployment. It is the first rule that materially improves broad robustness without relying on symbol-specific names.

## Why 5m Routing Is The Lead

The prior result said Quality Score 3 was helpful but not uniform. The admission/routing spike shows the remaining damage is concentrated in 15m, not in the quality-score bundle itself.

| Candidate | Trades | P&L | PF | Win % | DD % | PF<1 Rows | Negative Windows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline 125bps | 473 | 5106.00 | 1.289 | 56.0 | 14.14 | 11 | 17 |
| Actual Quality Score 3 | 439 | 5430.79 | 1.328 | 56.9 | 13.38 | 10 | 14 |
| 5m Only | 178 | 5300.90 | 1.730 | 62.4 | 7.27 | 3 | 6 |
| QS3 + 5m Only | 171 | 5422.28 | 1.773 | 63.2 | 7.27 | 3 | 7 |

`QS3 + 5m Only` preserves most of the upside while cutting the major drawdown problem:

- P&L is almost unchanged versus QS3: `5422.28` vs `5430.79`.
- PF improves from `1.328` to `1.773`.
- DD improves from `13.38%` to `7.27%`.
- PF<1 rows drop from `10` to `3`.
- Prior admitted controls remain strong: `4149.82` P&L, `2.928` PF, `2.43%` DD.
- Failed+perp controls flip from weak to positive: `865.61` P&L, `1.211` PF, `12.24%` DD.

The remaining weak 5m rows under QS3 are small or isolated:

- `BNB 5m`: 2 trades, `-15.49` P&L, `0.855` PF.
- `LTC 5m`: 1 trade, `-53.10` P&L.
- `RENDER 5m`: 14 trades, `-266.57` P&L, `0.730` PF, `7.41%` DD.

That is a much narrower problem than the original broad failure set.

## What Did Not Explain The Edge

Quality-score decomposition does not support replacing QS3 with one clean component yet.

| Test | P&L | PF | DD % | Read |
| --- | ---: | ---: | ---: | --- |
| Emulated QS >= 3 | 5308.17 | 1.309 | 14.10 | Confirms the QS3 direction but weaker than the actual export. |
| Removed by QS >= 3 | -202.17 | 0.585 | 3.22 | QS3 removes a losing subset, but not enough to solve broad deployment. |
| Level Quality >= 3 | 614.44 | 1.645 | 5.86 | Too few trades and does not protect broad scope. |
| Non-Level Quality >= 2 | 5058.24 | 1.294 | 14.10 | Does not materially improve the baseline. |
| Entry Quality Score >= 4 | 4079.94 | 1.455 | 11.91 | Improves PF/DD but cuts too much opportunity and leaves too many weak rows. |

Keep QS3 bundled for now. The bundle works better than the individual available components.

## Trait Diagnostics

The strongest separator was timeframe. Other entry-time traits were weaker or misleading:

- 15m baseline: `-194.90` P&L, `0.981` PF, `19.15%` DD.
- 5m baseline: `5300.90` P&L, `1.730` PF, `7.27%` DD.
- Active quality score was only modestly higher in pass-like slots: `3.423` vs `3.216`.
- Level quality barely separated pass/fail slots: `2.059` vs `2.041`.
- Strength freshness was not helpful; pass-like slots had older average strength age than fail-like slots.
- Entry risk <= 250 bps improved drawdown but did not solve failed/perp controls.
- Stop distance / ATR <= 4.5 was actively bad as a broad filter.
- Direct wick/sweep frequency and true multi-bar trend persistence are not available in current closed-trade telemetry, so this pass used entry range / ATR, stop distance / ATR, and strength slope as proxies only.

## Routing Diagnostics

`QS3 + Route Higher Avg Quality TF` slightly outscored `QS3 + 5m Only`, but it is a lookahead diagnostic because it selects timeframes using full-history average quality. It should not be implemented directly.

Its value is directional: it confirms that one-timeframe-per-symbol routing can work, but the current implementable rule should stay simpler.

The implementable candidate is `QS3 + 5m Only` because it is:

- simple
- not symbol-specific
- not dependent on outcome labels
- materially better on PF and drawdown
- broad across most failed, major, and perp controls

## Walk-Forward Check

The prior-window stability gate reduced drawdown in the latest window, but it did not create a stronger broad verdict than 5m routing:

| Check | Trades | P&L | PF | Win % | DD % | PF<1 Rows | Negative Windows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Latest Window Control | 169 | 1426.81 | 1.180 | 52.7 | 17.39 | 18 | 7 |
| Walk-Forward Stability Gate | 93 | 818.52 | 1.195 | 53.8 | 10.05 | 6 | 4 |

This helps risk, but it removes too much opportunity and still leaves weak PF. It can be a later overlay, not the next primary implementation.

## Recommendation

Build the next concrete strategy candidate as `Quality Score 3 + 5m routing` and run it through TradingView as a real Pine/exported strategy, not just a telemetry simulation.

Acceptance gate for the next run:

- Same symbol matrix as the generalization run.
- 5m only.
- Entire available history.
- Compare against baseline 125 bps, QS3 all-timeframe control, and simulated QS3+5m metrics from this spike.
- Require PF to stay materially above QS3, DD near or below `7.27%`, and no expansion of negative rows beyond the simulated 5m profile.
- Specifically monitor `RENDER 5m`; it is the one non-thin 5m failure that remains.

Current verdict: broad success is plausible through an admission/routing layer, and the strongest next rule is `QS3 + 5m Only`. Do not spend the next pass on more stop logic, ATR filters, or isolated quality components.
