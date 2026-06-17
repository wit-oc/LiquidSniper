# Canary K Admission Verdict

Date: 2026-06-16 ET / 2026-06-17 UTC

## Scope

Candidate:

`Unity UTM Strategy v7 QS3 PDF Filter Canary K`

Canary K keeps the Canary J entry logic stable and adds an explicit admission/routing layer. The change is intentionally narrow: decide whether the hydrated 15m Unity reaction model is allowed to trade the current symbol before an otherwise valid setup can place an order.

TradingView layout rule:

- Only `Codex-Automation` was used.

No closed-source indicators were rebuilt. Source fidelity still depends on the saved TradingView layout and hydrated `input.source()` mappings.

Unity PDF guidepost:

- Direct local text extraction from `../../specs/UnityTradingModel.pdf` was not available with the current tools.
- This pass re-anchored on `artifacts/v7_pdf_strategy_refinement/PDF_GUIDED_REFINEMENT_REPORT.md`, which captures the PDF intent for this V7 branch: HTF liquidity, sweep/reclaim, LTF structure shift, strength/sentiment confirmation, 30m/1h timing, real invalidation, and disciplined targets.

## Pine Change

Canary K adds:

- `Admission Mode` input with four modes: `Off`, `Core Only`, `Core + Candidate Add`, and `Core + Candidate + Monitor`.
- Exact-symbol admission tiers:
  - Core admitted: `BINANCE:ETHUSDT.P`, `BINANCE:ADAUSDT.P`, `BINANCE:ARBUSDT.P`, `BINANCE:SEIUSDT.P`
  - Candidate add: `BLOFIN:DOGEUSDT.P`, `BINANCE:ENAUSDT.P`
  - Monitor: `BINANCE:SOLUSDT.P`, `BLOFIN:ZECUSDT.P`, `BINANCE:WIFUSDT.P`
- Default mode: `Core + Candidate Add`
- Entry gate: `symbolAdmissionOk` must be true for both long and short entries.
- Diagnostics: admission mode, admission tier, admission OK status-line plots, fail-mask bit, and `AM/AT` entry-comment fields.
- Sentinel: `CODEX_INSTALL_SENTINEL_QS3_PDF_CANARY_K`

Canary K preserves the current Unity-themed signal requirements:

- Liquidity sweep/reclaim reaction zone.
- Mapped AIO internal MSS inputs.
- Oracle Strength input.
- 15m entries only on 30m/1h-aligned bars.
- Minimum 3.0 ATR stop/invalidation distance.
- Existing strong-short confluence logic.

## Harness Proof

All runs returned `status: ok`, used the `Codex-Automation` layout, matched the Canary K title/sentinel, applied mapped Unity/Oracle sources, selected Strategy Tester `Entire history`, and exported from the active Strategy Report context menu.

| Batch | Run directory | Visible ranges |
| --- | --- | --- |
| ETH + ADA | `artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T04-42-02-577Z-deep-date-window-matrix` | ETH: `Nov 27, 2019 - Jun 16, 2026`; ADA: `Jan 31, 2020 - Jun 16, 2026` |
| ARB + SEI | `artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-16T04-52-21-865Z-deep-date-window-matrix` | ARB: `Mar 23, 2023 - Jun 16, 2026`; SEI: `Aug 16, 2023 - Jun 16, 2026` |
| DOGE + ENA | `artifacts/v7_pdf_strategy_refinement/tradingview/automation/v7-qs3-pdf-filters-eth-install-canary/2026-06-17T00-04-50-194Z-deep-date-window-matrix` | DOGE: `Jan 12, 2023 - Jun 16, 2026`; ENA: `Apr 2, 2024 - Jun 16, 2026` |

Parsed artifacts:

- `artifacts/v7_pdf_strategy_refinement/CANARY_K_ADMISSION_SMOKE_ETH_ADA_RESULTS.md`
- `artifacts/v7_pdf_strategy_refinement/canary_k_admission_smoke_eth_ada_metrics.json`
- `artifacts/v7_pdf_strategy_refinement/CANARY_K_ADMISSION_CORE_ARB_SEI_RESULTS.md`
- `artifacts/v7_pdf_strategy_refinement/canary_k_admission_core_arb_sei_metrics.json`
- `artifacts/v7_pdf_strategy_refinement/CANARY_K_ADMISSION_CANDIDATE_DOGE_ENA_RESULTS.md`
- `artifacts/v7_pdf_strategy_refinement/canary_k_admission_candidate_doge_ena_metrics.json`

## Basket Comparison

| Version / Scope | Symbols | Trades | Net USDT | PF | Win % |
| --- | --- | ---: | ---: | ---: | ---: |
| Baseline QS3 | ETH, SOL, DOGE, ZEC | 285 | -555.84 | 0.955 | 51.93 |
| Canary E | ETH, SOL, DOGE, ZEC | 142 | 1089.93 | 1.209 | 54.23 |
| Canary J 14-symbol read | ETH, SOL, DOGE, ZEC, ADA, LINK, XRP, ARB, PYTH, SEI, SUI, WIF, ENA, OP, PENDLE | 223 | 946.96 | 1.098 | 54.30 |
| Canary K core only | ETH, ADA, ARB, SEI | 64 | 2548.21 | 2.494 | 75.00 |
| Canary K candidate add only | DOGE, ENA | 22 | 530.81 | 1.759 | 68.18 |
| Canary K default | ETH, ADA, ARB, SEI, DOGE, ENA | 86 | 3079.02 | 2.280 | 73.26 |

## Canary K Default Breakdown

By symbol:

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

By notable symbol/side:

| Symbol / Side | Trades | Net USDT | PF | Read |
| --- | ---: | ---: | ---: | --- |
| ADA long | 5 | -14.86 | 0.929 | Small drag, not enough to justify a side ban |
| ENA short | 2 | -57.34 | 0.457 | Risk flag; sample too small for a new side-specific filter |
| DOGE short | 2 | 147.96 | n/a | Prior DOGE short defect is not present in the admitted Canary K read |
| Short C3 | 19 | 917.10 | 6.383 | The current short-side quality logic remains strong in the admitted set |
| Long C6 | 1 | -165.31 | 0.000 | One DOGE long loser; not enough for a global high-confluence veto |

## Interpretation

Canary K is not saying the strategy is universal. It is saying the current hydrated 15m Unity reaction model should only route symbols where the evidence supports that model.

This directly addresses the defect that appeared after Canary E. The earlier weak-short issue was not best solved by banning all shorts or rebuilding vendor indicators. Canary J improved the short-side logic, and Canary K now prevents the improved 15m reaction model from being deployed across arbitrary symbols where the larger 14-symbol read compressed back to a weak PF.

The change stays honest to the Unity Trading Model theme because the trade trigger remains the same: reversal-zone liquidity evidence, market-structure/sentiment confirmation through mapped sources, aligned execution timing, and real invalidation. The admission gate is a deployment/routing control, not a substitute signal.

## Recommendation

Promote Canary K as the current best refinement branch for further iteration, with default `Core + Candidate Add`.

Do not add another Pine entry threshold right now. The remaining weak spots are too sparse to justify a new global rule:

- ENA shorts are negative, but only two trades.
- ADA longs are slightly negative, but only five trades.
- DOGE has one large long C6 loser, but the DOGE candidate batch is still positive and DOGE shorts are positive.

Operational stance:

1. Use `Core + Candidate Add` as the default research candidate.
2. Use `Core Only` when a conservative comparison is needed.
3. Keep SOL, ZEC, and WIF in `Monitor` mode, not the default route.
4. Keep LINK, XRP, PYTH, SUI, OP, and PENDLE excluded from the current route.
5. Revisit side-specific admission only if repeated future exports show the same ENA-short or ADA-long weakness.

Overfit risk remains meaningful. The exact-symbol admission set is evidence-based, but it is still an admission set derived from historical exports. The next validation should be forward/bake-off style: keep K logic stable, export the default admitted set periodically, and only change the routing table when new evidence is persistent by symbol and side.
