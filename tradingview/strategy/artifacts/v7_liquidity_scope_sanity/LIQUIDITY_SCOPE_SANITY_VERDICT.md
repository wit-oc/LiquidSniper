# V7 Liquidity Scope Sanity Verdict

## Decision

Proceed with a liquidity-aware symbol-admission implementation test. Do not implement a universal lower-liquidity basket.

The lower-liquidity thesis is supported in the narrow sense that multiple new smaller/reflexive symbols independently passed the fixed V7 candidate without degrading the protected prior admitted controls. It is not supported as a blanket rule across all smaller/reflexive symbols.

## Evidence

- Matrix coverage: 56/56 slots accounted, 49 successful strategy CSV exports, 7 failed slots, 0 missing slots.
- Failed/no-valid-export symbols: HYPE, AERO, RNDR. Treat these as insufficient-data symbols, not strategy failures.
- One control slot also failed automation: BTC 15m. BTC remains non-admitted and was not used as positive evidence.
- Fixed candidate held constant: V7 System A, Displacement Quality, structural stop, 125bps hard stop floor, existing R-based TP and source mappings.
- All-symbol basket remains unacceptable: PF 1.109, DD 28.59%, 742 trades.
- Smaller/reflexive basket is not tradable as a tier: PF 1.001, DD 39.65%, 491 trades.
- Smaller/reflexive pass set is strong: ARB, PYTH, SEI combined PF 2.214, DD 2.26%, 69.3% win rate, 75 trades.
- Total admitted pass set is strong: ZEC, ADA, LINK, XRP, ARB, PYTH, SEI combined PF 2.149, DD 3.46%, 69.2% win rate, 198 trades.
- Prior admitted controls are protected: ZEC, ADA, LINK, XRP combined PF 2.114, DD 3.10%.
- ZEC remains protected: PF 2.601, DD 2.92%, 57 trades.

## New Symbol Classification

| Class | Symbols | Read |
| --- | --- | --- |
| Pass | ARB, PYTH, SEI | Admit to next implementation test. |
| Marginal | JUP, ONDO | Keep diagnostic; do not admit by default. |
| Fail | VIRTUAL, FET, RENDER, WIF, TIA, SUI, INJ, ENA, PENDLE, OP | Do not admit. |
| Insufficient data/export | HYPE, AERO, RNDR | Retry only if symbol routing/export automation is corrected or a different venue symbol is selected. |

## Window Read

- ARB passed, but latest-window quality is only defensible, not strong: latest PF 1.076 with positive P&L.
- PYTH passed with strong latest-window behavior: latest PF 15.143 with positive P&L.
- SEI passed with stable early/middle/latest windows: latest PF 2.964 with positive P&L.
- JUP and ONDO are useful diagnostics because latest windows are positive, but their full-history PF remains below the pass gate.
- Several failed symbols had isolated good windows but failed full-history DD/PF, especially ENA, PENDLE, RENDER, TIA, SUI, and INJ.

## Timeframe Read

- The pass set is not exclusively a 5m artifact:
  - SEI passed on both 15m and 5m.
  - ARB was profitable on both, with 5m materially stronger.
  - PYTH was profitable on both, with 5m materially stronger.
- The broader smaller/reflexive tier is unstable on 5m. Several failures had 5m DD above 5%, including VIRTUAL, FET, RENDER, SUI, ENA, and OP.
- Do not make a global 5m liquidity rule. Timeframe admission should stay symbol-specific.

## Directional Read

- ARB passed on both sides, with long stronger than short.
- PYTH passed mostly through short-side strength, but long side was also positive.
- SEI passed on both sides, with short side carrying most trade count and long side small but clean.
- JUP and ONDO were positive on both sides but below full pass quality.
- Directional gating may be useful later, but this pass does not justify adding side rules before symbol admission is implemented.

## Recommendation

Next implementation should admit only:

ZEC, ADA, LINK, XRP, ARB, PYTH, SEI.

Keep JUP and ONDO as diagnostics. Exclude BTC, SOL, BNB, DOGE, ETH, LTC, VIRTUAL, FET, RENDER, WIF, TIA, SUI, INJ, ENA, PENDLE, and OP from the implementation candidate.

The next test should be a clean implementation candidate using this admitted set with no entry/stop/TP tuning. Validate that the admitted-set behavior survives a fresh TradingView run, preserves ZEC and prior admitted controls, and does not rely on one symbol or one latest-window burst.
