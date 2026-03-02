# Foxian Constraints v1 — Intraday Revisit

## Hard Rules
- Structure-first gating from 4H context.
- Clean, sparse SR zones; deterministic generation only.
- Retest discipline for break/reclaim entries.
- Confluence filters may refine, never override invalid structure/SR logic.
- Risk-first execution and hard breakers always on.
- Realistic costs (fees, funding, slippage) in all performance claims.

## Optional Filters
- EMA trend filter
- VWAP alignment
- ATR regime filter
- Extra candle confirmation strictness

## Anti-Patterns
- Over-zoning and chart clutter
- Hindsight zone redrawing
- BTC-only optimization claims
- Ignoring cost/funding drag
- Lookahead leakage

## Alignment Checklist
- [ ] Structure context explicit and testable
- [ ] Zone logic deterministic and sparse
- [ ] Retest mechanics codified
- [ ] Risk controls primary
- [ ] Costs included
- [ ] BTC+ETH tested OOS
