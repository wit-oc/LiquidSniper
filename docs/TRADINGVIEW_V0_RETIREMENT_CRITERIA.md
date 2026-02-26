# TradingView v0 Retirement Criteria

Objective gates to deprecate v0 Pine scripts and promote v1 fidelity scripts as default.

## Candidate scripts
- v0 indicator: `tradingview/indicator/liquidsniper_confluence_indicator.pine`
- v0 strategy: `tradingview/strategy/liquidsniper_confluence_strategy.pine`
- v1 indicator: `tradingview/indicator/liquidsniper_confluence_indicator_v1_fidelity.pine`
- v1 strategy: `tradingview/strategy/liquidsniper_confluence_strategy_v1_fidelity.pine`

## Gate A — Compile and runtime safety (hard gate)
1. v1 indicator compiles in TradingView Pine v5 with no edits.
2. v1 strategy compiles in TradingView Pine v5 with no edits.
3. No unsupported function/argument regressions during import.
4. Alerts (watch/trigger) can be created successfully.

Pass condition: **all 4 true**.

## Gate B — Mentorship-fidelity acceptance (hard gate)
Use `docs/TRADINGVIEW_MENTORSHIP_FIDELITY_MAPPING_V1.md`.

1. All R1–R7 marked **Aligned** remain aligned after QA.
2. No **new P0** misalignments introduced.
3. Existing P0 count is 0 or explicitly waived with written rationale.

Pass condition: **all 3 true**.

## Gate C — Signal quality delta vs v0 (hard gate)
Run both strategies on the same symbol/time windows/profile settings.

Required outcomes (v1 vs v0):
1. **Choppy period exposure** reduced by >= 15% (proxy: trades during high-CI windows).
2. **Stop-out density** reduced by >= 10% (stop exits / total trades).
3. **Profit factor** non-degrading: v1 PF >= 0.95 * v0 PF (minimum), with target >= v0 PF.
4. **Max drawdown** non-inferior: v1 max DD <= 1.05 * v0 DD.

Pass condition: **all 4 true**.

## Gate D — Operational readiness (hard gate)
1. `docs/TRADINGVIEW_V1_TEST_CHECKLIST.md` executed and signed off.
2. README release note present and accurate.
3. Naming/versioning stable (v1 files immutable except patch updates).
4. Team agreement recorded (engineering + strategy owner).

Pass condition: **all 4 true**.

## Promotion decision
- Promote v1 and retire v0 defaults only when **Gate A + B + C + D** all pass.
- If any hard gate fails: v0 remains default; open remediation tasks.

## Post-promotion guardrail
For first 2 weeks after promotion:
- Keep v0 scripts available as rollback artifacts.
- Track weekly drift report (trigger count, stop-out rate, PF, DD).
- Auto-revert default to v0 if PF drops >20% or DD rises >20% vs qualification baseline.
