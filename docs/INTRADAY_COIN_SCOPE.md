# Intraday Coin Scope (v1.1)

Use this scope for initial live-paper validation of the Pine-derived intraday model.

## Tier A — Primary validation set
- SOLUSDT
- AVAXUSDT
- XRPUSDT
- SUIUSDT

## Tier B — Secondary validation set
- LINKUSDT
- ADAUSDT
- DOGEUSDT
- TONUSDT

## Tier C — Controls / broad market anchors
- BTCUSDT
- ETHUSDT

## Inclusion rules
1. Keep profile fixed to `I`.
2. Use the same parameter pack across all Tier A symbols first.
3. Promote symbol to production scope only if:
   - PF >= 1.10
   - DD within tolerance
   - No severe divergence vs Pine validation
4. If one symbol repeatedly deviates, treat it as a symbol override candidate (do not mutate base profile first).

## Exclusion flags
Pause symbol if any occurs over rolling 7 days:
- PF < 1.0
- DD > 1.5x portfolio DD target
- Frequent gate mismatch vs Pine (>10% disagreement on trigger bars)
