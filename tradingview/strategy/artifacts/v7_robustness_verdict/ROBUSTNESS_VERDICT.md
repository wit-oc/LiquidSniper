# V7 Robustness Verdict

## Decision

Do not implement the broad 125bps structural V7 candidate across BTC, ETH, and ZEC yet.

The overfit sanity check did not show a simple latest-window-only failure. The 125bps candidate stayed profitable across early, middle, and latest thirds of the available TradingView report ranges. The failure is symbol concentration: ZEC explains nearly all of the edge while BTC+ETH remain weak.

## Evidence

The pass reused the full-history structural-control Strategy Tester exports from the latest matrix:

- 15m reports: Oct 31, 2025 to May 28, 2026.
- 5m reports: Mar 15, 2026 to May 28, 2026.
- Coverage: 12/12 selected exports, 0 missing, 0 rejected.

Full-history basket:

| System | Trades | P&L | PF | Win % | DD % |
|---|---:|---:|---:|---:|---:|
| Structural 100bps | 132 | 2190.22 | 1.377 | 59.8 | 5.92 |
| Structural 125bps | 111 | 2416.10 | 1.622 | 60.4 | 3.85 |

125bps by relative report-window third:

| Window | Trades | P&L | PF | Win % | DD % |
|---|---:|---:|---:|---:|---:|
| Early | 38 | 616.54 | 1.664 | 60.5 | 3.88 |
| Middle | 37 | 885.03 | 1.712 | 59.5 | 4.10 |
| Latest | 36 | 914.53 | 1.534 | 61.1 | 3.37 |

125bps symbol scope:

| Scope | Trades | P&L | PF | Win % | DD % |
|---|---:|---:|---:|---:|---:|
| All symbols | 111 | 2416.10 | 1.622 | 60.4 | 3.85 |
| BTC+ETH only | 54 | 146.49 | 1.063 | 48.1 | 6.31 |
| ETH+ZEC only | 92 | 2557.05 | 1.815 | 63.0 | 3.84 |
| ZEC only | 57 | 2269.61 | 2.458 | 71.9 | 2.92 |
| BTC only | 19 | -140.95 | 0.811 | 47.4 | 2.66 |
| ETH only | 35 | 287.44 | 1.182 | 48.6 | 6.29 |

## Interpretation

The candidate is not just a one-window artifact. That is good. But it is not yet a broad Unity Trading Model implementation either. BTC is not tradable in this configuration, ETH is marginal, and ZEC supplies about 94% of total P&L.

The timeframe test also argues against broad implementation:

| Scope | Trades | P&L | PF | Win % | DD % |
|---|---:|---:|---:|---:|---:|
| 15m+5m | 111 | 2416.10 | 1.622 | 60.4 | 3.85 |
| 15m only | 63 | 362.38 | 1.168 | 52.4 | 3.68 |
| 5m only | 48 | 2053.72 | 2.190 | 70.8 | 3.95 |

Most of the edge is ZEC plus 5m. That may be a valid symbol-scoped implementation, but it is not enough evidence to claim a general BTC/ETH/ZEC Unity model.

## Recommendation

Abort broad refinement from this pass. The next path should be one of two tightly scoped options:

1. Treat V7 as a ZEC-first symbol-scoped strategy and run a dedicated ZEC robustness test with deeper symbol-specific validation.
2. Keep V7 as diagnostic and investigate why BTC/ETH fail before any implementation commitment.

Do not spend another iteration tuning global stop or entry parameters from the current BTC/ETH/ZEC basket. That would optimize around ZEC while hiding weak BTC/ETH behavior.
