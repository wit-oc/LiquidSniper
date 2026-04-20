# Paper Engine Daily Checklist (Intraday Focus)

## Morning checks (before market activity)
- [ ] Runner healthy (`paper_daemon` heartbeat present)
- [ ] Active strategy lane is intraday only
- [ ] Symbol scope matches `docs/INTRADAY_COIN_SCOPE.md`
- [ ] Config hash/version recorded for the day

## Midday checks
- [ ] Trigger count by symbol (unexpected spikes?)
- [ ] Gate failure reasons top 3 (trend/chop/retest/etc.)
- [ ] Open risk within configured hard cap
- [ ] Slippage/commission drift not abnormal

## End-of-day checks
- [ ] PF / Net / DD by symbol
- [ ] Avg trade USD and commission ratio
- [ ] Win rate + avg win/loss ratio
- [ ] Compare top 5 wins/losses for obvious pattern drift
- [ ] Record any symbol-specific anomalies

## Weekly review gates
- [ ] Tier A symbols still pass promotion thresholds
- [ ] Any symbols demoted to watchlist
- [ ] Need for symbol override vs base profile change decided

## Incident triggers (immediate review)
- [ ] Daily max loss reached
- [ ] DD step-change (>25% relative jump week-over-week)
- [ ] Trigger flood in blocked/chop periods
- [ ] Persistent mismatch vs Pine validation (>10%)
