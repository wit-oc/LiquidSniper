# V7 QS3 PDF-Guided Refinement Report

Date: 2026-06-14

## Status

Local strategy refinement is implemented, and current-export candidate metrics are reproducible.

Live TradingView validation is not complete.

Current revalidation status: the ETH hydrated reuse canary is failing in the current TradingView layout state. The first strict failure proved the active Strategy Tester report was `Unity UTM Strategy v6 Fidelity Audit M15`, not `Unity UTM Strategy v7 Generalization IV Quality Score 3`. After Pine overlay cleanup, the latest strict failure no longer exposes any Strategy Tester/report panel for the target V7 QS3 reuse instance. Object Tree verification then confirmed the current `Sherlock-Copy-v3` layout has vendor indicators attached but does not have the V7 QS3 strategy object attached. The layout menu shows `SherlockView` and two `Unnamed` recently used layouts as possible manual recovery candidates, but the automation did not load them because that would mutate TradingView state without knowing which layout contains the hydrated strategy.

The harness was hardened on 2026-06-14 so this state can no longer return a false `ok` result from chart-level `All data` or Pine Editor title text. See `HYDRATED_CANARY_REVALIDATION_2026-06-14.md`.

## PDF Strategy Intent

The Unity Trading Model is built around:

- HTF liquidity levels.
- Liquidity grabs/sweeps at those levels.
- LTF market structure shift or break of structure with candle-close confirmation.
- Delta/relative strength confirmation, especially on 30m to 1h, with 4h/daily as bonus context.
- Time-based execution around higher-volume 30m/1h candle opens and major sessions.
- True invalidation stops beyond the sweep wick, OB invalidation, or invalidating structure.
- Liquidity-pool targets using multiple take-profit zones, with 2R minimum expectation and 4R+ A+ outcomes.

The most important interpretation for this pass: QS3 should not simply trade every sweep plus MSS. It should trade reversal zones when liquidity is taken and the reaction is confirmed by structure, strength, timing, and clean invalidation.

## Current V7 QS3 Mapping

Current implementation already covers:

- HTF level detection across previous day/week/month and recent swing levels.
- Sweep plus reclaim arming.
- AIO internal MSS as the required LTF structure trigger.
- Oracle Strength as required strength direction.
- 4H/1D EMA bias alignment.
- Sweep-wick stop placement.
- Source validation for required mapped indicator sources.

Current implementation under-enforces or omits:

- Time-based execution: no active filter for 30m/1h candle-close alignment or high-volume windows.
- BOS/retest: BOS and retest are optional/default-off in the active QS3 path.
- Trade management: full position exits at TP1/stop, so the export measures 1R hit rate rather than the PDF's 2R-plus target model.
- USDT.D confirmation: the PDF checklist calls this out, but QS3 has no market-dominance confirmation.
- AIO trend alert: present as telemetry, but current exports show alert-present trades are worse, so it should not be promoted to a sentiment gate without better evidence.

## Export Deficiencies

Source: `pdf_refinement_candidate_metrics.md`, generated from the four manual hydrated CSV exports in `artifacts/v7_artifacts`.

Baseline basket:

| Trades | Net | PF | Win % |
|---:|---:|---:|---:|
| 285 | -555.84 | 0.955 | 51.9 |

Major deficiencies:

- Side/regime asymmetry is real but symbol-specific: ETH shorts and ZEC shorts work, SOL longs work, DOGE shorts are materially bad. Hardcoding sides would overfit.
- Time alignment is the strongest clean deficiency: entries at `00/30` minutes were +741.75 net/PF 1.122; `15/45` entries were -1297.59/PF 0.795.
- Stop/invalidation quality matters: `RA<3` trades were -749.34/PF 0.816; `RA3-5` trades were +431.82/PF 1.060.
- Combined `30m/1h + stop ATR floor` post-filter keeps 106 trades, +1237.80 net, PF 1.331, win 56.6%, and removes 179 trades totaling -1793.64.
- Fresh strength recency helps alone, but the strict `S<=2` version compresses the sample heavily when combined with the stronger time/stop filters.
- Alert-present trades are worse than no-alert trades, so alert gating is not supported by current evidence.

## Implemented Changes

Updated `artifacts/v7_generalization_independent_variables/generated/v7-generalization-quality-score-3.pine`:

- Added `08. PDF Strategy Filters`.
- Default-on: `Require 30m/1h Candle Close Alignment`.
- Default-on: `Require True Invalidation Stop ATR Floor`, with default floor `3.0` stop-distance ATR.
- Default-off test controls:
  - `Require Fresh Strength Shift`, default max age `2` bars.
  - `Require Daily Bias Confirmation`.
- Wired these controls into long/short readiness and entry gating.

Added supporting artifacts:

- `artifacts/v7_pdf_strategy_refinement/analyze_pdf_refinement_candidates.mjs`
- `artifacts/v7_pdf_strategy_refinement/pdf_refinement_candidate_metrics.md`
- `artifacts/v7_pdf_strategy_refinement/pdf_refinement_candidate_metrics.json`
- `artifacts/v7_pdf_strategy_refinement/tv_pdf_strategy_refinement_runs.json`

Patched the deep-date-window harness with a Pine-panel recovery attempt. The current TradingView UI now gets past Pine-overlay contamination, but the preserved chart state does not currently expose the V7 QS3 Strategy Tester report in existing-instance reuse mode.

## Ranked Change List

1. Keep the implemented time alignment plus stop ATR floor as the first live candidate.
   - Faithfulness: high.
   - Evidence: strongest current-export post-filter.
   - Risk: low to moderate.
   - Overfit risk: moderate; must validate live because post-filtering cannot model newly available trades after skipped entries.

2. Add UTM partial trade management as a separate experiment.
   - Faithfulness: very high.
   - Evidence: current full-size 1R TP is not the PDF target model.
   - Risk: moderate; TradingView partial exits need careful reservation handling.

3. Test retest/OB/POI fidelity using the existing armed zone/retest machinery.
   - Faithfulness: high.
   - Evidence: PDF checklist explicitly calls for OB/POI retest with LTF BOS.
   - Risk: moderate; may reduce sample sharply.

4. Add USDT.D confirmation only after defining the rule.
   - Faithfulness: high.
   - Risk: high unless we agree exactly how USDT.D should support long/short crypto trades.

5. Keep daily-bias confirmation as optional.
   - Evidence: removes losing `1/0` long bucket, but may conflict with reversal intent if used too bluntly.

6. Keep fresh-strength recency optional.
   - Evidence: helpful alone, weaker in the combined candidate; better as a second-stage test.

## Validation Caveat

The `30m/1h + stop ATR floor` result is a post-filter of existing exported trades, not a recomputed TradingView strategy run. Because the strategy has `pyramiding=0`, removing an earlier trade can allow a later setup that did not appear in the baseline export. Treat these metrics as directionally useful, not accepted backtest proof.

Live validation still requires:

1. Restore/select a V7 QS3 hydrated Strategy Tester report that reproduces the 76-trade ETH baseline.
2. Keep the hardened canary gates active: active report title must match V7 QS3, date selection must prove `Entire history|All history`, visible start must be on or before `2024-01-01`, and no-trade reports are invalid.
3. Confirm the edited Pine compiles.
4. Confirm mapped source values survive the validation path without collapsing to the late-2025 remapped-source window.
5. Re-export ETH as the canary.
6. Only then run the representative basket.
