# Unity UTM V7 Canary K Candidate

Date: 2026-06-17

## Candidate Status

`Unity UTM Strategy v7 QS3 PDF Filter Canary K` is the current preserved V7 candidate.

It should be treated as a research candidate, not a production trading system. The current evidence is strong enough to checkpoint the branch, preserve the Pine implementation, and test it forward or out-of-sample without further tuning first.

## What Canary K Is

Canary K is Canary J signal logic plus an explicit symbol-admission layer.

The trade trigger is still the Unity Trading Model reaction sequence:

- 15m execution.
- Liquidity sweep/reclaim at a reversal zone.
- Mapped AIO internal MSS as the structure-shift trigger.
- Oracle Strength as sentiment/strength confirmation.
- 30m/1h-aligned entry timing.
- Minimum 3.0 ATR invalidation distance.
- Current strong-short confluence logic, including the delayed C3 short strength refinement.

The new Canary K element is routing. A setup can only place an order if the active symbol is admitted by the `Admission Mode` input.

Default `Admission Mode`:

`Core + Candidate Add`

Default admitted set:

| Tier | Symbols | Read |
| --- | --- | --- |
| Core | `BINANCE:ETHUSDT.P`, `BINANCE:ADAUSDT.P`, `BINANCE:ARBUSDT.P`, `BINANCE:SEIUSDT.P` | Strongest current evidence |
| Candidate add | `BLOFIN:DOGEUSDT.P`, `BINANCE:ENAUSDT.P` | Positive, but less mature |
| Monitor | `BINANCE:SOLUSDT.P`, `BLOFIN:ZECUSDT.P`, `BINANCE:WIFUSDT.P` | Research only, not default |
| Excluded | LINK, XRP, PYTH, SUI, OP, PENDLE, and unlisted symbols | Not admitted by current evidence |

## Why This Is Faithful To UTM

Canary K does not replace the strategy with a symbol hack. It preserves the UTM entry mechanics and adds a deployment control around where that model is allowed to fire.

That distinction matters because the pressure tests showed two things at the same time:

1. The UTM-style 15m reaction model has real pockets of edge.
2. The same model degrades when spread across arbitrary symbols.

The admission layer is therefore a fidelity control: do not force a liquidity-sweep/MSS/strength strategy onto symbols where the current behavior does not support that playbook.

## Current Evidence

Reference baseline:

| Version / Scope | Symbols | Trades | Net USDT | PF | Win % |
| --- | --- | ---: | ---: | ---: | ---: |
| Baseline QS3 | ETH, SOL, DOGE, ZEC | 285 | -555.84 | 0.955 | 51.93 |
| Canary E | ETH, SOL, DOGE, ZEC | 142 | 1089.93 | 1.209 | 54.23 |
| Canary J 14-symbol read | 14-symbol pressure set | 223 | 946.96 | 1.098 | 54.30 |
| Canary K core only | ETH, ADA, ARB, SEI | 64 | 2548.21 | 2.494 | 75.00 |
| Canary K candidate add only | DOGE, ENA | 22 | 530.81 | 1.759 | 68.18 |
| Canary K default | ETH, ADA, ARB, SEI, DOGE, ENA | 86 | 3079.02 | 2.280 | 73.26 |

Current Canary K default breakdown:

| Symbol | Tier | Trades | Net USDT | PF | Win % |
| --- | --- | ---: | ---: | ---: | ---: |
| `BINANCE:ETHUSDT.P` | Core | 29 | 1348.21 | 2.576 | 75.86 |
| `BINANCE:ADAUSDT.P` | Core | 12 | 356.52 | 2.111 | 66.67 |
| `BINANCE:ARBUSDT.P` | Core | 12 | 466.09 | 2.466 | 75.00 |
| `BINANCE:SEIUSDT.P` | Core | 11 | 377.39 | 2.778 | 81.82 |
| `BLOFIN:DOGEUSDT.P` | Candidate add | 15 | 345.03 | 1.636 | 66.67 |
| `BINANCE:ENAUSDT.P` | Candidate add | 7 | 185.78 | 2.187 | 71.43 |

By side:

| Side | Trades | Net USDT | PF | Win % |
| --- | ---: | ---: | ---: | ---: |
| Long | 60 | 1674.48 | 1.786 | 66.67 |
| Short | 26 | 1404.54 | 6.088 | 88.46 |

Important caveats:

- ENA shorts are negative, but only two trades.
- ADA longs are slightly negative, but only five trades.
- DOGE has one large long C6 loser, but DOGE remains positive overall and DOGE shorts are positive.
- The admission table is evidence-derived and can overfit if treated as universal truth.

## How To Use The Candidate

Use only the dedicated TradingView `Codex-Automation` layout for validation.

Run context:

- Chart timeframe: `15m`
- Strategy Tester date range: `Entire history`
- Pine backtest window: starts `2024-01-01`
- Default mode: `Admission Mode = Core + Candidate Add`

Operational modes:

| Mode | Use |
| --- | --- |
| `Core + Candidate Add` | Current default candidate |
| `Core Only` | Conservative validation set |
| `Core + Candidate + Monitor` | Research-only pressure testing |
| `Off` | Diagnostic only; disables routing protection |

Venue/symbol strings matter. For example, current DOGE evidence is on `BLOFIN:DOGEUSDT.P`, not an arbitrary DOGE perp.

## Preserved Artifacts

Primary verdict:

- `artifacts/v7_pdf_strategy_refinement/CANARY_K_ADMISSION_VERDICT.md`

Candidate Pine source:

- `artifacts/v7_generalization_independent_variables/generated/v7-generalization-quality-score-3.pine`

TradingView harness config:

- `artifacts/v7_pdf_strategy_refinement/tv_pdf_strategy_refinement_runs.json`

Supporting result summaries:

- `artifacts/v7_pdf_strategy_refinement/CANARY_K_ADMISSION_SMOKE_ETH_ADA_RESULTS.md`
- `artifacts/v7_pdf_strategy_refinement/CANARY_K_ADMISSION_CORE_ARB_SEI_RESULTS.md`
- `artifacts/v7_pdf_strategy_refinement/CANARY_K_ADMISSION_CANDIDATE_DOGE_ENA_RESULTS.md`

Supporting lineage:

- `artifacts/v7_pdf_strategy_refinement/CODEX_AUTOMATION_CANARY_E_RESULTS.md`
- `artifacts/v7_pdf_strategy_refinement/CANARY_J_DECISIVE_DELAYED_STRENGTH_RESULTS.md`
- `artifacts/v7_pdf_strategy_refinement/CANARY_J_OP_PENDLE_GENERALIZATION_VERDICT.md`
- `artifacts/v7_pdf_strategy_refinement/PDF_GUIDED_REFINEMENT_REPORT.md`

## Next Test Plan

Do not tune Canary K before the next validation step.

Recommended next work:

1. Freeze this candidate and treat the commit as the reproducible checkpoint.
2. Run a broader out-of-sample basket with Canary K unchanged.
3. Record excluded-symbol no-trade behavior separately from admitted-symbol performance.
4. Compare by symbol, side, and confluence bucket.
5. Only modify the admission table or side-specific routing if weakness repeats across new exports.

The immediate question is not whether K can be made broader by adding thresholds. The immediate question is whether the current admitted route remains stable when we test more coins without changing the rules.
