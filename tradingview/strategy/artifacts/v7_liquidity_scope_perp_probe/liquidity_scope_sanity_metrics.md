# V7 Liquidity Scope Sanity Metrics

Generated from 6 selected or accounted Strategy Tester slots. Expected slots: 6. Missing: 0. Failed slots: 0. Rejected report candidates: 0.

## Coverage
| Expected slots | Accounted slots | Missing | Failed | Rejected |
| --- | --- | --- | --- | --- |
| 6 | 6 | 0 | 0 | 0 |

## Source Ranges
| Asset | TV Symbol | Tier | Prior | TF | Status | Report range | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| HYPE | HYPE.P | smaller/reflexive perp probe | spot-route-unresolved | 15m | ok | Oct 31, 2025 to May 29, 2026 | 24 | -409.30 | 0.671 | 45.8 | 5.21 |
| HYPE | HYPE.P | smaller/reflexive perp probe | spot-route-unresolved | 5m | ok | Mar 15, 2026 to May 29, 2026 | 22 | 741.35 | 1.700 | 59.1 | 4.29 |
| AERO | AERO.P | smaller/reflexive perp probe | spot-route-unresolved | 15m | ok | Oct 31, 2025 to May 29, 2026 | 24 | -242.01 | 0.747 | 50.0 | 6.00 |
| AERO | AERO.P | smaller/reflexive perp probe | spot-route-unresolved | 5m | ok | Mar 15, 2026 to May 29, 2026 | 19 | 143.97 | 1.156 | 57.9 | 4.32 |
| RENDER | RENDER.P | smaller/reflexive perp probe | spot-route-fail | 15m | ok | Oct 31, 2025 to May 29, 2026 | 25 | 251.77 | 1.364 | 60.0 | 2.07 |
| RENDER | RENDER.P | smaller/reflexive perp probe | spot-route-fail | 5m | ok | Mar 15, 2026 to May 29, 2026 | 17 | -280.52 | 0.743 | 41.2 | 7.41 |

## Symbol Classification
| Asset | TV Symbol | Tier | Prior | Class | Slots ok/no/failed/missing | Reason | Trades | P&L | PF | Win % | DD % | TP1 first % | Stop first % |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AERO | AERO.P | smaller/reflexive perp probe | spot-route-unresolved | fail | 2/0/0/0 | does not meet PF/DD/window gates | 43 | -98.04 | 0.948 | 53.5 | 6.51 | 32.6 | 67.4 |
| HYPE | HYPE.P | smaller/reflexive perp probe | spot-route-unresolved | fail | 2/0/0/0 | does not meet PF/DD/window gates | 46 | 332.05 | 1.144 | 52.2 | 6.86 | 52.2 | 47.8 |
| RENDER | RENDER.P | smaller/reflexive perp probe | spot-route-fail | fail | 2/0/0/0 | does not meet PF/DD/window gates | 42 | -28.75 | 0.984 | 52.4 | 8.43 | 52.4 | 47.6 |

## Scope Summary
| Scope | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: |
| All symbols | 131 | 205.26 | 1.034 | 52.7 | 14.79 |
| Prior admitted controls | 0 | 0.00 | 0.000 | n/a | 0.00 |
| Prior failed controls | 0 | 0.00 | 0.000 | n/a | 0.00 |
| Major controls | 0 | 0.00 | 0.000 | n/a | 0.00 |
| Smaller/reflexive candidates | 0 | 0.00 | 0.000 | n/a | 0.00 |
| Admitted pass symbols | 0 | 0.00 | 0.000 | n/a | 0.00 |
| Smaller/reflexive pass symbols | 0 | 0.00 | 0.000 | n/a | 0.00 |
| Marginal symbols | 0 | 0.00 | 0.000 | n/a | 0.00 |
| Failed symbols | 131 | 205.26 | 1.034 | 52.7 | 14.79 |

## Liquidity Tier Comparison
| Tier | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: |
| smaller/reflexive perp probe | 131 | 205.26 | 1.034 | 52.7 | 14.79 |

## Windowed Robustness
| Asset | Tier | Window | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| AERO | smaller/reflexive perp probe | early | 12 | 359.73 | 2.671 | 75.0 | 1.07 |
| AERO | smaller/reflexive perp probe | latest | 20 | -429.45 | 0.599 | 40.0 | 6.66 |
| AERO | smaller/reflexive perp probe | middle | 11 | -28.32 | 0.952 | 54.5 | 4.46 |
| HYPE | smaller/reflexive perp probe | early | 16 | -456.45 | 0.451 | 37.5 | 5.30 |
| HYPE | smaller/reflexive perp probe | latest | 19 | 145.27 | 1.137 | 57.9 | 5.38 |
| HYPE | smaller/reflexive perp probe | middle | 11 | 643.23 | 2.544 | 63.6 | 2.04 |
| RENDER | smaller/reflexive perp probe | early | 20 | -728.72 | 0.397 | 40.0 | 8.53 |
| RENDER | smaller/reflexive perp probe | latest | 15 | 296.75 | 1.568 | 53.3 | 2.10 |
| RENDER | smaller/reflexive perp probe | middle | 7 | 403.22 | 8.544 | 85.7 | 0.53 |

## Timeframe Contribution
| Asset | Tier | TF | Status | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| AERO | smaller/reflexive perp probe | 15m | ok | 24 | -242.01 | 0.747 | 50.0 | 6.00 |
| AERO | smaller/reflexive perp probe | 5m | ok | 19 | 143.97 | 1.156 | 57.9 | 4.32 |
| HYPE | smaller/reflexive perp probe | 15m | ok | 24 | -409.30 | 0.671 | 45.8 | 5.21 |
| HYPE | smaller/reflexive perp probe | 5m | ok | 22 | 741.35 | 1.700 | 59.1 | 4.29 |
| RENDER | smaller/reflexive perp probe | 15m | ok | 25 | 251.77 | 1.364 | 60.0 | 2.07 |
| RENDER | smaller/reflexive perp probe | 5m | ok | 17 | -280.52 | 0.743 | 41.2 | 7.41 |

## Directional Contribution
| Asset | Tier | Side | Trades | P&L | PF | Win % | DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| AERO | smaller/reflexive perp probe | long | 18 | -183.44 | 0.844 | 55.6 | 5.94 |
| AERO | smaller/reflexive perp probe | short | 25 | 85.40 | 1.121 | 52.0 | 2.11 |
| HYPE | smaller/reflexive perp probe | long | 33 | 267.65 | 1.134 | 51.5 | 6.34 |
| HYPE | smaller/reflexive perp probe | short | 13 | 64.40 | 1.206 | 53.8 | 1.58 |
| RENDER | smaller/reflexive perp probe | long | 20 | -44.74 | 0.963 | 50.0 | 8.51 |
| RENDER | smaller/reflexive perp probe | short | 22 | 15.99 | 1.027 | 54.5 | 1.62 |

## Verdict Inputs

- Label: insufficient data
- Smaller/reflexive passes: none
- Smaller/reflexive marginals: none
- Independent smaller/reflexive pass assets: none
- Top smaller/reflexive pass P&L share: n/a%
- Outlier-dependent pass set: no
- ZEC profit-protection passed: no
- Prior admitted controls protected: no
- Insufficient/unavailable symbols: none
- Recommendation: Reject the lower-liquidity expansion thesis for now; continue with the prior admitted symbol set unless a different independent variable is tested.
