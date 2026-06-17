# V7 Leverage Stop Sidebar Verdict

## Verdict

Reject leverage-scaled structural stop floors as the next Unity Trading Model implementation path.

This sidebar should remain throwaway/diagnostic. It did not produce evidence strong enough to alter the current main path: regime-specialized V7 System A, Displacement Quality entry, hard 100-125bps stop floor, BTC excluded or separately parameterized, and ZEC/ETH used as the candidate validation set.

## What Was Tested

The experiment held V7 System A Displacement Quality entry logic fixed and changed only the minimum structural risk floor:

| Leverage analogy | Tested floor |
|---|---:|
| 100x | 100bps |
| 50x | 200bps |
| 20x | 500bps |
| 10x | 1000bps |

It also tested two symbol-profile mappings:

| Profile | BTC | ETH | ZEC |
|---|---:|---:|---:|
| BTC100 ETH200 ZEC500 | 100bps | 200bps | 500bps |
| BTC125 ETH500 ZEC1000 | 125bps | 500bps | 1000bps |

Important caveat: this is not the creator's exact fixed-percent stop model. It keeps structural stops and uses leverage-derived bps values as minimum structural stop floors. A true non-structural fixed-percent stop would need a separate isolated test if we want to pressure-test that exact behavior.

## Evidence

Coverage was complete: 42 expected slots, 42 selected slots, 0 missing, 0 rejected reports.

The in-run controls were the best broad variants:

| Variant | Trades | PF | Win % | Max DD % | Total P&L |
|---|---:|---:|---:|---:|---:|
| Uniform 100x / 100bps | 128 | 1.413 | 60.2 | 4.91 | 2282.55 |
| Control 125bps | 111 | 1.622 | 60.4 | 4.52 | 2416.10 |

The wider leverage floors did not improve the implementation shape:

| Variant | Trades | PF | Max DD % | Result |
|---|---:|---:|---:|---|
| Uniform 50x / 200bps | 68 | 1.345 | 6.30 | Fails DD target and weakens BTC/ETH. |
| Uniform 20x / 500bps | 13 | 4.142 | 0.76 | Too sparse and ZEC-carried. |
| Uniform 10x / 1000bps | 0 | n/a | 0.00 | No trades. |
| Profile BTC100 ETH200 ZEC500 | 58 | 0.877 | 6.30 | Negative basket. |
| Profile BTC125 ETH500 ZEC1000 | 20 | 0.759 | 2.80 | Negative and sparse. |

BTC did not become viable under wider floors. ETH degraded materially once the floor widened beyond 125bps. ZEC tolerated 500bps better than the other symbols, but the resulting signal is narrow and not enough to justify a portfolio-level implementation pivot.

## Decision Criteria

The sidebar only mattered if it produced PF >= 1.35 with DD <= 5% without being solely ZEC-carried, or if it clearly improved BTC without harming ETH/ZEC.

It failed that bar:

- 100bps and 125bps meet the PF/DD bar, but they are the existing control direction.
- 200bps is below the PF threshold after rounding risk and exceeds the DD target.
- 500bps has attractive headline PF/DD, but only 13 trades and is essentially ZEC-only.
- 1000bps removes the system from the market.
- Symbol-profile floors are negative.

## Recommendation

Return to the main 100-125bps hard-floor refinement path. Keep the learning that wider structural floors act mostly as a trade filter, not as a BTC/ETH profitability fix. The next implementation work should refine the existing System A path rather than adopting leverage-scaled floors:

- Keep 125bps as the current best broad hard-floor control.
- Treat BTC as excluded or separately parameterized until a BTC-specific edge appears.
- Continue validating on ETH/ZEC, with drawdown-first acceptance and PF secondary.
- If we still want to test the creator's exact stop behavior, run it as a separate sidebar that replaces the structural stop with fixed-percent market-price stops rather than using bps floors.
