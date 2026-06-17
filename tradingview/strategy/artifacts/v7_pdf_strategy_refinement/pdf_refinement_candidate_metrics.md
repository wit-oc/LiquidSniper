# PDF Refinement Candidate Metrics

Source exports: 4

Baseline: 285 trades, net -555.84, PF 0.955, win 51.9%.

## Candidate Post-Filters

| Filter | Kept Trades | Kept Net | Kept PF | Kept Win % | Removed Trades | Removed Net |
|---|---:|---:|---:|---:|---:|---:|
| 30m/1h close alignment | 149 | 741.75 | 1.122 | 55.0 | 136 | -1297.59 |
| stop ATR floor >= 3 | 208 | 193.50 | 1.023 | 52.4 | 77 | -749.34 |
| 30m/1h + stop ATR floor | 106 | 1237.80 | 1.331 | 56.6 | 179 | -1793.64 |
| fresh strength <= 2 bars | 85 | 386.05 | 1.113 | 57.6 | 200 | -941.89 |
| 30m/1h + fresh strength + stop ATR floor | 30 | 215.00 | 1.200 | 56.7 | 255 | -770.84 |
| daily-confirmed longs | 258 | 190.37 | 1.018 | 52.3 | 27 | -746.21 |

### Route Side

| Key | Trades | Net | PF | Win % |
|---|---:|---:|---:|---:|
| BINANCE:ETHUSDT.P long | 33 | -348.82 | 0.831 | 51.5 |
| BINANCE:ETHUSDT.P short | 43 | 326.81 | 1.289 | 53.5 |
| BINANCE:SOLUSDT.P long | 28 | 850.02 | 1.714 | 60.7 |
| BINANCE:SOLUSDT.P short | 41 | -513.72 | 0.718 | 48.8 |
| BLOFIN:DOGEUSDT.P long | 29 | -50.63 | 0.969 | 62.1 |
| BLOFIN:DOGEUSDT.P short | 37 | -436.50 | 0.656 | 37.8 |
| BLOFIN:ZECUSDT.P long | 49 | -503.64 | 0.810 | 49.0 |
| BLOFIN:ZECUSDT.P short | 25 | 120.64 | 1.201 | 60.0 |

### Level

| Key | Trades | Net | PF | Win % |
|---|---:|---:|---:|---:|
| PDH | 2 | -4.63 | 0.909 | 50.0 |
| PMH | 2 | -400.55 | 0.000 | 0.0 |
| PML | 4 | -697.63 | 0.160 | 25.0 |
| PWH | 1 | 45.36 | inf | 100.0 |
| PWL | 2 | -331.16 | 0.000 | 0.0 |
| SWING_HIGH | 141 | -142.95 | 0.967 | 49.6 |
| SWING_LOW | 133 | 975.72 | 1.152 | 56.4 |

### Quality Pair

| Key | Trades | Net | PF | Win % |
|---|---:|---:|---:|---:|
| Q2 C3 | 159 | -131.61 | 0.972 | 49.7 |
| Q2 C4 | 111 | 760.48 | 1.129 | 56.8 |
| Q3 C3 | 1 | 45.36 | inf | 100.0 |
| Q3 C4 | 5 | 61.14 | 1.274 | 60.0 |
| Q3 C5 | 2 | -33.31 | 0.806 | 50.0 |
| Q3 C6 | 1 | -159.72 | 0.000 | 0.0 |
| Q4 C5 | 5 | -867.19 | 0.133 | 20.0 |
| Q5 C4 | 1 | -230.99 | 0.000 | 0.0 |

### Alert Presence

| Key | Trades | Net | PF | Win % |
|---|---:|---:|---:|---:|
| long alert | 64 | -355.38 | 0.901 | 51.6 |
| long no_alert | 75 | 302.31 | 1.076 | 57.3 |
| short alert | 66 | -595.55 | 0.747 | 45.5 |
| short no_alert | 80 | 92.78 | 1.037 | 52.5 |

### Bias Side

| Key | Trades | Net | PF | Win % |
|---|---:|---:|---:|---:|
| -1/-1 short | 144 | -317.14 | 0.931 | 49.3 |
| -1/0 short | 2 | -185.63 | 0.196 | 50.0 |
| 1/0 long | 27 | -746.21 | 0.528 | 48.1 |
| 1/1 long | 112 | 693.14 | 1.116 | 56.3 |

### Strength Age

| Key | Trades | Net | PF | Win % |
|---|---:|---:|---:|---:|
| S0-2 | 85 | 386.05 | 1.113 | 57.6 |
| S3-6 | 101 | -417.97 | 0.900 | 49.5 |
| S7+ | 99 | -523.92 | 0.891 | 49.5 |

### Risk Bps

| Key | Trades | Net | PF | Win % |
|---|---:|---:|---:|---:|
| RB<150 | 46 | -732.47 | 0.802 | 54.3 |
| RB150-250 | 140 | -546.47 | 0.900 | 50.0 |
| RB250+ | 99 | 723.10 | 1.223 | 53.5 |

### Stop ATR

| Key | Trades | Net | PF | Win % |
|---|---:|---:|---:|---:|
| RA<3 | 77 | -749.34 | 0.816 | 50.6 |
| RA3-5 | 186 | 431.82 | 1.060 | 53.2 |
| RA5+ | 22 | -238.32 | 0.790 | 45.5 |

### Entry Minute

| Key | Trades | Net | PF | Win % |
|---|---:|---:|---:|---:|
| 00/30 | 149 | 741.75 | 1.122 | 55.0 |
| 15/45 | 136 | -1297.59 | 0.795 | 48.5 |

### Weekday

| Key | Trades | Net | PF | Win % |
|---|---:|---:|---:|---:|
| Fri | 45 | -180.60 | 0.909 | 48.9 |
| Mon | 32 | -56.19 | 0.958 | 50.0 |
| Sat | 25 | -22.09 | 0.984 | 52.0 |
| Sun | 57 | -293.81 | 0.887 | 52.6 |
| Thu | 37 | 197.34 | 1.156 | 54.1 |
| Tue | 41 | 414.83 | 1.282 | 56.1 |
| Wed | 48 | -615.32 | 0.742 | 50.0 |
