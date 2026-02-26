# Optimization Governance (Pine v1 sweep)

## Objective
Use parameter sweeps to shortlist robust configurations for TradingView validation while reducing overfit risk.

## Rules
1. Keep `engine_v1.py` **frozen** for a sweep cycle. Do not change logic mid-run.
2. Constrain ranges by profile (`C`, `I`, `S`) and risk caps.
3. Use reproducible seeds; every run must write `run_manifest.json`.
4. Rank by composite score, but review raw metrics (PF, win rate, DD, trade count).
5. Promote only candidates that survive out-of-sample checks.

## Selection policy
- Export **top 10** per profile by score.
- Export **3 safe picks** per profile favoring low DD and stable PF.
- Reject candidates with too few trades or unstable DD spikes.

## Risk policy
- `risk_based` sizing must respect profile risk cap.
- Notional cap guardrail is always active for risk-based sizing.
- High-confluence tiers may increase risk but never above profile cap.

## Anti-overfit checklist
- [ ] Use fixed seed for baseline comparison
- [ ] Compare across at least two time windows
- [ ] Ensure shortlist includes conservative variants
- [ ] Reconfirm shortlist behavior in TradingView strategy replay
