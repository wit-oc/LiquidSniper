# Task Board — LiquidSniper

Status legend: [Now] [Next] [Later] [Blocked] [Done]

## [Now]
- [x] Cleanup + integration pass: reconcile `WORK_ITEMS.md` with completed Tasks 09–13
- [ ] Validate end-to-end pipeline wiring (ingestor -> card/confluence -> analysis run -> diagnostic UI)
- [ ] Task 14: Land HTF-anchor strategy rulebook contract (`docs/AUTOMATED_TRADING_AGENT_ALIGNMENT_V1.md`, runbook + schema payload shape)
- [ ] Task 15: Align lecture-derived strategy scoring to deterministic decision payload fields

## [Next]
- [ ] Docker/compose verification for web + ingestor + shared artifact mount
- [ ] Runbook/CI validation gate for simulation mode rollout
- [ ] Define go/no-go checklist for promotion from simulation to guarded live pilot
- [ ] Task 16: Thread LiquidSniper dependencies and enforce non-bypass strategy -> policy -> execution boundaries
- [ ] Task 17: Add two-pass adversarial validation harness/gates for anchor profiles and strategy drift
- [ ] Task 18: Decide packaging boundary (integrated module vs separate execution core service) with explicit fork triggers

## [Later]
- [ ] Dynamic S/R level initiative integration (phase-gated sidecar)
- [ ] Automated watchlist refresh/diff alerts for shared TradingView list inputs

## [Blocked]
- none

## [Done]
- [x] Hybrid pipeline tasks T4–T8 completed via initiative runner (2026-02-15)
