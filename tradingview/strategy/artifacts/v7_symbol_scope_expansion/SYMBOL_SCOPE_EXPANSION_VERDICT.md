# V7 Symbol Scope Expansion Verdict

## Decision

Proceed to a symbol-admission implementation test. Do not implement a universal all-coin basket.

The fixed 125bps V7 System A candidate found multiple non-ZEC symbols with acceptable performance while preserving ZEC. That means the prior weakness was not simply "ZEC-only." It also means BTC is not a symbol we should force into the model.

The universal 10-symbol basket is not acceptable: PF 1.305 with 13.10% DD. The admitted pass-symbol set is materially better: PF 2.055, 69.1% win rate, and 3.60% DD across ZEC, ADA, LINK, and XRP.

## Classification

| Symbol | Class | Trades | P&L | PF | Win % | DD % | Read |
|---|---|---:|---:|---:|---:|---:|---|
| ZEC | pass | 57 | 2214.79 | 2.424 | 71.9 | 2.92 | Keep as profit-protection control |
| ADA | pass | 30 | 687.86 | 1.884 | 66.7 | 1.62 | Admit, but monitor latest-window weakness |
| LINK | pass | 13 | 518.48 | 2.328 | 76.9 | 2.12 | Admit, lower trade count |
| XRP | pass | 23 | 365.94 | 1.423 | 60.9 | 3.16 | Admit, mostly 5m/short edge |
| LTC | marginal | 14 | 145.62 | 1.343 | 50.0 | 2.62 | Diagnostic only |
| ETH | fail | 35 | 287.44 | 1.182 | 48.6 | 6.29 | Diagnostic only; 5m is better than 15m |
| BTC | fail | 19 | -140.95 | 0.811 | 47.4 | 2.66 | Exclude from implementation |
| DOGE | fail | 29 | -125.90 | 0.903 | 34.5 | 6.26 | Exclude |
| BNB | fail | 15 | -486.67 | 0.383 | 33.3 | 5.40 | Exclude |
| SOL | fail | 27 | -531.94 | 0.556 | 37.0 | 8.52 | Exclude |

This is a symbol-admission verdict. BTC is not the only weak symbol, but it is clearly not an implementation candidate. ZEC is not uniquely good because ADA, LINK, and XRP also passed the fixed-rule classification.

## Profit Protection

ZEC remained protected:

- ZEC PF: 2.424 versus prior control PF 2.458.
- ZEC DD: 2.92%, inside the <= 3.5% guard.
- ZEC P&L: 2214.79.
- Admitted pass-symbol set DD: 3.60%, with ZEC still the largest contributor.

The pass did not steal ZEC edge to improve weak symbols because no global tuning was applied.

## Timeframe Read

The model should not use a single global timeframe rule yet.

| Symbol | Better read |
|---|---|
| ZEC | Both 15m and 5m pass; 5m stronger |
| ADA | Both pass; 15m has more trades and stable edge |
| LINK | Both pass; low trade count but strong |
| XRP | 5m carries the edge; 15m is weak |
| LTC | 15m is viable, 5m failed with too few trades |
| ETH | 5m is viable, 15m failed |
| DOGE | 5m positive but total symbol fails |
| BTC/SOL/BNB | No admission case |

Next implementation should be symbol-timeframe admission, not 5m-only globally.

## Directional Read

Directional gating may help, but it should be tested as a second-stage independent lever:

- ZEC: both long and short are profitable.
- ADA: both long and short are profitable.
- LINK: long carries most of the edge.
- XRP: short carries most of the edge.
- LTC: short-only is the viable diagnostic case.
- ETH: long-only is the viable diagnostic case.

Do not apply a global long-only or short-only rule. It would be too blunt and could damage ZEC/ADA.

## Recommendation

Next pass should implement a fixed symbol-admission harness:

- Admit: ZEC, ADA, LINK, XRP.
- Diagnostic only: LTC, ETH.
- Exclude: BTC, SOL, BNB, DOGE.

Keep the 125bps structural stop, Displacement Quality entry, and R-based TP unchanged. The next test should only validate symbol/timeframe admission and optional symbol-specific side gating as independent levers.
