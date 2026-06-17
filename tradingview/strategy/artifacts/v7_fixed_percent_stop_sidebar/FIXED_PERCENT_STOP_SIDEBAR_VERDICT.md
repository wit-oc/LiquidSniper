# Fixed Percent Stop Sidebar Verdict

## Scope

This was an isolated throwaway sidebar for Unity Trading Model V7. It tested the creator-style idea that stop distance can be set as a fixed percent of market price, roughly inverse to leverage:

| Variant | Stop distance |
|---|---:|
| 100x | 1.0% / 100bps |
| 50x | 2.0% / 200bps |
| 20x | 5.0% / 500bps |
| 10x | 10.0% / 1000bps |
| Profile A | BTC 100bps, ETH 200bps, ZEC 500bps |
| Profile B | BTC 125bps, ETH 500bps, ZEC 1000bps |

Unlike the earlier leverage sidebar, this spike replaced the actual stop distance with the fixed-percent stop. It was not just a structural floor. The TP remained R-based off that fixed stop distance, and the same V7 System A / Displacement Quality entry stack was used.

## Decision

Do not adopt fixed-percent stops for the curated V7 implementation path.

The 125bps structural control remains the best candidate from this matrix: 111 trades, 2416.10 total P&L, PF 1.622, 60.4% win rate, and 4.52% max row DD. Every fixed-percent basket missed the decision bar. The best fixed-percent PF was only 1.134 at 10.0%, while the symbol-profile variants were outright negative.

## What Failed

The fixed-percent stop model did not solve the core problem. Tight fixed stops, especially 1.0%, generated more trades but materially worsened BTC and drawdown. Wider fixed stops lowered drawdown but also collapsed realized edge because fewer trades reached TP1 before max-hold.

The clearest telemetry signal is max-hold drift:

| Stop model | TP1 first % | Stop first % | MaxHold % | PF |
|---|---:|---:|---:|---:|
| Structural 125bps | 60.4 | 39.6 | 0.0 | 1.622 |
| Fixed 2.0% | 54.1 | 44.1 | 1.8 | 1.086 |
| Fixed 5.0% | 34.1 | 31.9 | 33.3 | 1.025 |
| Fixed 10.0% | 19.8 | 13.8 | 65.5 | 1.134 |

Wider stops were not creating better winners. They were mostly allowing positions to linger until time-based exits.

## Symbol Read

BTC improved only in the narrow sense that the 10.0% fixed stop nearly flattened BTC P&L with low drawdown: -19.70 P&L, PF 0.936, 1.07% DD. That is still not a tradable edge, and it came with severe ETH degradation: -301.35 P&L, PF 0.412.

ZEC remained the main positive contributor, but fixed-percent stops reduced ZEC quality versus the structural control. Structural 125bps produced ZEC PF 2.458 and 2269.61 P&L; the best fixed-percent ZEC result was 10.0% with PF 1.494 and 590.74 P&L.

ETH did not justify the model either. Fixed 2.0% held ETH near positive, but wider stops degraded it and profile B turned ETH negative.

## Practical Verdict

The creator-style fixed-percent stop concept may rely on a different full trading method, position sizing model, manual discretion, or exit logic. In this harness, as a direct replacement for structural invalidation inside V7 System A, it is not practical.

Return to the curated V7 path: System A, Displacement Quality entry, structural stop with hard 100-125bps floor, and BTC treated as excluded or separately parameterized until it shows an actual edge.
