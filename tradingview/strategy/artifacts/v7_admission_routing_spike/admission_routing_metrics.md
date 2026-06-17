# V7 Admission Routing Spike Metrics

Source artifact: `tradingview/strategy/artifacts/v7_generalization_independent_variables`
Source telemetry: `tradingview/strategy/.telemetry/outputs/v7_generalization_independent_variables`

## Coverage
| Run | Parsed Trades | Telemetry Trades | Raw Slots Available |
| --- | ---: | ---: | --- |
| Baseline 125bps | 473 | 473 | 32/32 |
| Quality Score 3 | 439 | 439 | 31/32 |

## Controls
| Control | Trades | P&L | PF | Win % | DD % |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline 125bps | 473 | 5106.00 | 1.289 | 56.0 | 14.14 |
| Actual Quality Score 3 | 439 | 5430.79 | 1.328 | 56.9 | 13.38 |
| Emulated QS>=3 From Baseline | 451 | 5308.17 | 1.309 | 56.8 | 14.10 |
| Removed By QS>=3 | 22 | -202.17 | 0.585 | 40.9 | 3.22 |

## Candidate Ranking
| Rule | Family | Validity | Trades | Retained % | Admit P&L Retained % | P&L | PF | Win % | DD % | PF<1 Rows | Neg Windows | Admit Protected | Score |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 5m Only | timeframe-routing | static-timeframe | 178 | 37.6 | 67.1 | 5300.90 | 1.730 | 62.4 | 7.27 | 3 | 6 | yes | 52.01 |
| QS3 + Route Higher Avg Quality TF | timeframe-routing | lookahead-diagnostic | 192 | 40.6 | 71.4 | 5405.76 | 1.694 | 60.9 | 7.85 | 2 | 7 | yes | 51.78 |
| QS3 + 5m Only | timeframe-routing | qs3-plus-one-routing-variable | 171 | 36.2 | 69.7 | 5422.28 | 1.773 | 63.2 | 7.27 | 3 | 7 | yes | 51.03 |
| Route To Higher Avg Quality TF | timeframe-routing | lookahead-diagnostic | 211 | 44.6 | 67.9 | 5046.82 | 1.587 | 59.2 | 8.70 | 3 | 9 | yes | 44.81 |
| QS3 + Entry Risk <= 250 bps | risk-efficiency | qs3-plus-one-entry-variable | 317 | 67.0 | 84.0 | 4791.31 | 1.376 | 58.4 | 8.72 | 11 | 13 | yes | 15.48 |
| Entry Quality Score >= 4 | entry-quality | entry-time | 164 | 34.7 | 63.9 | 4079.94 | 1.455 | 59.8 | 11.91 | 16 | 6 | yes | 11.38 |
| Actual Quality Score 3 | control | tradingview-export | 439 | 92.8 | 103.2 | 5430.79 | 1.328 | 56.9 | 13.38 | 10 | 14 | yes | 10.43 |
| Entry Risk <= 250 bps | risk-efficiency | entry-time | 346 | 73.2 | 81.7 | 4474.65 | 1.325 | 57.2 | 9.70 | 12 | 15 | yes | 9.37 |
| Slot Avg Quality >= 3 | slot-admission | slot-calibration | 471 | 99.6 | 100.0 | 5212.90 | 1.297 | 56.3 | 14.14 | 10 | 16 | yes | 7.53 |
| Entry Quality Score >= 3 | entry-quality | entry-time | 451 | 95.3 | 101.0 | 5308.17 | 1.309 | 56.8 | 14.10 | 11 | 16 | yes | 5.26 |
| Level Quality >= 3 | quality-component | entry-time | 17 | 3.6 | 5.7 | 614.44 | 1.645 | 58.8 | 5.86 | 13 | 0 | no | 4.46 |
| Directional Strength Aligned | trend-persistence-proxy | entry-time | 473 | 100.0 | 100.0 | 5106.00 | 1.289 | 56.0 | 14.14 | 11 | 17 | yes | 4.00 |
| Non-Level Quality >= 2 | quality-component | entry-time | 448 | 94.7 | 99.3 | 5058.24 | 1.294 | 56.5 | 14.10 | 11 | 17 | yes | 3.85 |
| QS3 + Stop Distance / ATR <= 4.5 | risk-efficiency | qs3-plus-one-entry-variable | 284 | 60.0 | 56.2 | 1745.37 | 1.162 | 55.6 | 9.40 | 14 | 14 | no | -8.14 |
| Strength Age <= 3 | strength-freshness | entry-time | 136 | 28.8 | 26.6 | 1352.26 | 1.310 | 58.1 | 6.86 | 18 | 8 | no | -8.68 |
| Entry Range / ATR >= 2 | displacement-quality | entry-time | 228 | 48.2 | 30.2 | 1462.23 | 1.168 | 54.4 | 12.39 | 13 | 14 | no | -8.94 |
| ATR bps 75 to 250 | volatility-admission | entry-time | 99 | 20.9 | 8.3 | -227.82 | 0.924 | 47.5 | 11.74 | 9 | 8 | no | -9.91 |
| Stop Distance / ATR <= 4.5 | risk-efficiency | entry-time | 310 | 65.5 | 55.1 | 1424.01 | 1.123 | 54.2 | 9.38 | 15 | 15 | no | -12.85 |
| QS3 + 15m Only | timeframe-routing | qs3-plus-one-routing-variable | 268 | 56.7 | 33.5 | 8.51 | 1.001 | 53.0 | 17.99 | 7 | 19 | no | -13.48 |
| Route To Lower Stop/ATR TF | timeframe-routing | lookahead-diagnostic | 295 | 62.4 | 32.9 | -194.90 | 0.981 | 52.2 | 19.15 | 8 | 21 | no | -18.63 |
| 15m Only | timeframe-routing | static-timeframe | 295 | 62.4 | 32.9 | -194.90 | 0.981 | 52.2 | 19.15 | 8 | 21 | no | -18.63 |

## Delta Versus Controls
| Rule | Delta P&L vs Base | Delta PF vs Base | Delta DD vs Base | Delta P&L vs QS3 | Delta PF vs QS3 | Delta DD vs QS3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5m Only | 194.90 | 0.441 | -6.87 | -129.89 | 0.402 | -6.11 |
| QS3 + Route Higher Avg Quality TF | 299.76 | 0.405 | -6.29 | -25.03 | 0.366 | -5.54 |
| QS3 + 5m Only | 316.28 | 0.485 | -6.87 | -8.51 | 0.446 | -6.11 |
| Route To Higher Avg Quality TF | -59.18 | 0.298 | -5.44 | -383.97 | 0.259 | -4.69 |
| QS3 + Entry Risk <= 250 bps | -314.69 | 0.088 | -5.42 | -639.48 | 0.049 | -4.67 |
| Entry Quality Score >= 4 | -1026.06 | 0.166 | -2.23 | -1350.85 | 0.127 | -1.48 |
| Actual Quality Score 3 | 324.79 | 0.039 | -0.75 | 0.00 | 0.000 | 0.00 |
| Entry Risk <= 250 bps | -631.35 | 0.036 | -4.43 | -956.14 | -0.002 | -3.68 |
| Slot Avg Quality >= 3 | 106.90 | 0.008 | 0.00 | -217.89 | -0.031 | 0.75 |
| Entry Quality Score >= 3 | 202.17 | 0.020 | -0.04 | -122.62 | -0.019 | 0.72 |
| Level Quality >= 3 | -4491.56 | 0.356 | -8.28 | -4816.35 | 0.317 | -7.52 |
| Directional Strength Aligned | 0.00 | 0.000 | 0.00 | -324.79 | -0.039 | 0.75 |
| Non-Level Quality >= 2 | -47.76 | 0.005 | -0.04 | -372.55 | -0.033 | 0.72 |
| QS3 + Stop Distance / ATR <= 4.5 | -3360.63 | -0.126 | -4.73 | -3685.42 | -0.165 | -3.98 |
| Strength Age <= 3 | -3753.74 | 0.022 | -7.28 | -4078.53 | -0.017 | -6.52 |
| Entry Range / ATR >= 2 | -3643.77 | -0.120 | -1.75 | -3968.56 | -0.159 | -1.00 |
| ATR bps 75 to 250 | -5333.82 | -0.364 | -2.40 | -5658.61 | -0.403 | -1.64 |
| Stop Distance / ATR <= 4.5 | -3681.99 | -0.166 | -4.76 | -4006.78 | -0.205 | -4.01 |
| QS3 + 15m Only | -5097.49 | -0.288 | 3.85 | -5422.28 | -0.327 | 4.60 |
| Route To Lower Stop/ATR TF | -5300.90 | -0.307 | 5.01 | -5625.69 | -0.346 | 5.77 |
| 15m Only | -5300.90 | -0.307 | 5.01 | -5625.69 | -0.346 | 5.77 |

## Scope Rows For Top Candidates
| Rule | Scope | Trades | P&L | PF | Win % | DD % |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 5m Only | All symbols | 178 | 5300.90 | 1.730 | 62.4 | 7.27 |
| 5m Only | Prior admitted controls | 79 | 3992.38 | 2.718 | 74.7 | 2.43 |
| 5m Only | Prior failed controls | 25 | 430.94 | 1.425 | 52.0 | 4.79 |
| 5m Only | Major controls | 15 | 353.05 | 1.432 | 53.3 | 4.25 |
| 5m Only | Perp route probes | 59 | 524.53 | 1.169 | 52.5 | 9.97 |
| 5m Only | Failed+perp controls | 84 | 955.47 | 1.232 | 52.4 | 12.24 |
| QS3 + Route Higher Avg Quality TF | All symbols | 192 | 5405.76 | 1.694 | 60.9 | 7.85 |
| QS3 + Route Higher Avg Quality TF | Prior admitted controls | 80 | 4250.14 | 2.980 | 73.8 | 2.48 |
| QS3 + Route Higher Avg Quality TF | Prior failed controls | 34 | -96.02 | 0.940 | 41.2 | 6.89 |
| QS3 + Route Higher Avg Quality TF | Major controls | 24 | 768.72 | 1.790 | 62.5 | 4.18 |
| QS3 + Route Higher Avg Quality TF | Perp route probes | 54 | 482.92 | 1.157 | 53.7 | 9.97 |
| QS3 + Route Higher Avg Quality TF | Failed+perp controls | 88 | 386.90 | 1.083 | 48.9 | 16.26 |
| QS3 + 5m Only | All symbols | 171 | 5422.28 | 1.773 | 63.2 | 7.27 |
| QS3 + 5m Only | Prior admitted controls | 79 | 4149.82 | 2.928 | 74.7 | 2.43 |
| QS3 + 5m Only | Prior failed controls | 24 | 382.69 | 1.377 | 50.0 | 4.79 |
| QS3 + 5m Only | Major controls | 14 | 406.85 | 1.533 | 57.1 | 4.25 |
| QS3 + 5m Only | Perp route probes | 54 | 482.92 | 1.157 | 53.7 | 9.97 |
| QS3 + 5m Only | Failed+perp controls | 78 | 865.61 | 1.211 | 52.6 | 12.24 |
| Route To Higher Avg Quality TF | All symbols | 211 | 5046.82 | 1.587 | 59.2 | 8.70 |
| Route To Higher Avg Quality TF | Prior admitted controls | 80 | 4041.20 | 2.723 | 72.5 | 2.48 |
| Route To Higher Avg Quality TF | Prior failed controls | 47 | -231.38 | 0.891 | 44.7 | 8.28 |
| Route To Higher Avg Quality TF | Major controls | 25 | 712.47 | 1.693 | 60.0 | 4.18 |
| Route To Higher Avg Quality TF | Perp route probes | 59 | 524.53 | 1.169 | 52.5 | 9.97 |
| Route To Higher Avg Quality TF | Failed+perp controls | 106 | 293.15 | 1.056 | 49.1 | 18.14 |
| QS3 + Entry Risk <= 250 bps | All symbols | 317 | 4791.31 | 1.376 | 58.4 | 8.72 |
| QS3 + Entry Risk <= 250 bps | Prior admitted controls | 141 | 5000.02 | 2.282 | 71.6 | 3.64 |
| QS3 + Entry Risk <= 250 bps | Prior failed controls | 58 | -899.13 | 0.694 | 36.2 | 12.13 |
| QS3 + Entry Risk <= 250 bps | Major controls | 35 | 740.75 | 1.508 | 57.1 | 6.14 |
| QS3 + Entry Risk <= 250 bps | Perp route probes | 83 | -50.33 | 0.989 | 51.8 | 9.95 |
| QS3 + Entry Risk <= 250 bps | Failed+perp controls | 141 | -949.46 | 0.871 | 45.4 | 20.15 |
| Entry Quality Score >= 4 | All symbols | 164 | 4079.94 | 1.455 | 59.8 | 11.91 |
| Entry Quality Score >= 4 | Prior admitted controls | 66 | 3804.66 | 2.487 | 74.2 | 3.93 |
| Entry Quality Score >= 4 | Prior failed controls | 19 | -328.74 | 0.758 | 36.8 | 5.13 |
| Entry Quality Score >= 4 | Major controls | 12 | 641.04 | 1.840 | 66.7 | 6.13 |
| Entry Quality Score >= 4 | Perp route probes | 67 | -37.02 | 0.991 | 50.7 | 14.90 |
| Entry Quality Score >= 4 | Failed+perp controls | 86 | -365.76 | 0.935 | 47.7 | 17.26 |
| Actual Quality Score 3 | All symbols | 439 | 5430.79 | 1.328 | 56.9 | 13.38 |
| Actual Quality Score 3 | Prior admitted controls | 195 | 6141.53 | 2.183 | 69.2 | 3.70 |
| Actual Quality Score 3 | Prior failed controls | 75 | -1302.99 | 0.638 | 34.7 | 16.04 |
| Actual Quality Score 3 | Major controls | 46 | 568.48 | 1.304 | 52.2 | 6.18 |
| Actual Quality Score 3 | Perp route probes | 123 | 23.77 | 1.004 | 52.8 | 14.79 |
| Actual Quality Score 3 | Failed+perp controls | 198 | -1279.22 | 0.866 | 46.0 | 28.78 |
| Entry Risk <= 250 bps | All symbols | 346 | 4474.65 | 1.325 | 57.2 | 9.70 |
| Entry Risk <= 250 bps | Prior admitted controls | 144 | 4863.34 | 2.186 | 71.5 | 3.64 |
| Entry Risk <= 250 bps | Prior failed controls | 73 | -1073.40 | 0.700 | 38.4 | 14.18 |
| Entry Risk <= 250 bps | Major controls | 37 | 630.84 | 1.403 | 54.1 | 6.13 |
| Entry Risk <= 250 bps | Perp route probes | 92 | 53.87 | 1.012 | 51.1 | 9.95 |
| Entry Risk <= 250 bps | Failed+perp controls | 165 | -1019.53 | 0.874 | 45.5 | 21.60 |

## Trait Separation
| Trait | Available % | Pass Avg | Fail Avg | Delta Avg | P25 | P50 | P75 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Active Quality Score | 100.0 | 3.423 | 3.216 | 0.206 | 3.000 | 3.000 | 4.000 |
| Level Quality | 100.0 | 2.059 | 2.041 | 0.018 | 2.000 | 2.000 | 2.000 |
| Non-Level Quality Score | 100.0 | 2.368 | 2.175 | 0.192 | 2.000 | 2.000 | 3.000 |
| MSS Age | 100.0 | 2.746 | 0.982 | 1.764 | 0.000 | 0.000 | 2.000 |
| Alert Age | 44.2 | 2.678 | 0.432 | 2.246 | 0.000 | 0.000 | 1.000 |
| Strength Age | 100.0 | 9.654 | 5.901 | 3.754 | 3.000 | 6.000 | 11.000 |
| Side-Aligned Strength Slope | 100.0 | 0.993 | 1.093 | -0.100 | 0.454 | 0.812 | 1.329 |
| Absolute Strength Slope | 100.0 | 0.993 | 1.093 | -0.100 | 0.454 | 0.812 | 1.329 |
| ATR bps | 100.0 | 56.821 | 59.735 | -2.914 | 35.000 | 48.870 | 69.220 |
| Entry Range / ATR | 100.0 | 2.097 | 2.254 | -0.157 | 1.710 | 1.970 | 2.360 |
| Entry Risk bps | 100.0 | 221.876 | 228.366 | -6.490 | 151.120 | 193.640 | 255.670 |
| Stop Distance / ATR | 100.0 | 4.375 | 3.955 | 0.421 | 3.340 | 4.050 | 4.890 |

## Group Trait Diagnostics
| Group | Trades | P&L | PF | DD % | Avg Quality | Avg Non-Level Quality | Avg Strength Age | Avg Side Slope | Avg Range/ATR | Avg Stop/ATR | Avg ATR bps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Timeframe 15m | 295 | -194.90 | 0.981 | 19.15 | 3.176 | 2.142 | 4.790 | 1.114 | 2.175 | 3.697 | 68.87 |
| Timeframe 5m | 178 | 5300.90 | 1.730 | 7.27 | 3.618 | 2.551 | 15.000 | 0.858 | 2.149 | 5.295 | 35.77 |
| Prior admitted controls | 200 | 5952.46 | 2.094 | 3.72 | 3.345 | 2.285 | 8.195 | 1.070 | 2.121 | 4.162 | 59.31 |
| Prior failed controls | 92 | -1405.51 | 0.668 | 17.87 | 3.196 | 2.141 | 7.913 | 1.069 | 2.340 | 4.672 | 48.68 |
| Major controls | 49 | 433.06 | 1.216 | 6.96 | 3.204 | 2.143 | 8.184 | 1.118 | 2.309 | 4.652 | 49.07 |
| Perp route probes | 132 | 125.99 | 1.021 | 14.79 | 3.492 | 2.477 | 9.962 | 0.864 | 2.057 | 4.112 | 60.15 |

## Walk-Forward Stability Check
| Check | Trades | P&L | PF | Win % | DD % | PF<1 Rows | Neg Windows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Latest Window Control | 169 | 1426.81 | 1.180 | 52.7 | 17.39 | 18 | 7 |
| Walk-Forward Stability Gate | 93 | 818.52 | 1.195 | 53.8 | 10.05 | 6 | 4 |

## Trait Availability Notes
- Direct wick/sweep frequency before entry is not in the exported closed-trade telemetry; entryRangeAtr and stopDistanceAtr are used as pre-trade sweep/chop proxies.
- Direct multi-bar trend persistence is not in the exported closed-trade telemetry; side-aligned strength slope and non-level quality residual are used as proxies.
- Alert age is mostly unavailable/null in the current System A path, so it is not a useful discriminator in this pass.
