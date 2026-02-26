# Intraday Strategy Refinements (Based on Recent Runs)

## Confirmed effective
1. Risk-based sizing (`risk_based`) materially improved net returns vs percent-of-equity in tested windows.
2. MidCap-Momentum bucket (`I` profile) is currently the strongest general candidate.
3. Short-side ADX bump can reduce DD on some symbols (e.g., SOL), but is symbol-sensitive.

## Mixed / neutral
1. Time-block filters showed neutral or negative impact in combined tests.
2. Short-side stop multiplier at 0.9 showed minimal change in aggregate.

## Caution
1. Time-stop improved gross return in some runs but increased DD and reduced PF.
2. Single-value short ADX bump does not generalize across all symbols (SUI example).

## Current recommendation
- Keep base intraday profile simple.
- Use optional toggles only as targeted per-symbol overrides after validation.
- Prioritize these three levers first:
  - `risk_pct_low_conf`
  - `risk_pct_high_conf`
  - `high_conf_score_threshold`
