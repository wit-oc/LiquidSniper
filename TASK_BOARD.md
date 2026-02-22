# Task Board — LiquidSniper

Status legend: [Now] [Next] [Later] [Blocked] [Done]

## [Now]
- [ ] Execute full-scope plan in `docs/PAPER_MULTISTRATEGY_DELIVERY_PLAN_V1.md` (P0 safety + paper-only parallel lanes)
- [ ] Reconcile lane automation to unresolved units only (avoid stale Task 19 re-proposals)
- [ ] Task 18: Publish packaging-boundary decision ADR (integrated core vs separate execution service)
- [ ] Post-change evidence refresh: rerun targeted policy/daemon/replay/adversarial tests after daily-loss-breaker hardening
- [ ] Paper soak unit: 1–2 week paper run with fixed tuning cadence + explicit kill/promotion criteria
- [ ] SRV2-T0..T8: Execute `docs/SR_ENGINE_V2_SPEC.md` (HTF-anchored pivot-zone S/R engine with >=3 meaningful touches)

## [Next]
- [ ] Task 25: Run CCXT-vs-Blofin gap assessment; implement native fallback adapter only if required
- [ ] Build paper-mode metrics dashboard slice for weekly GO/HOLD/NO_GO review cadence
- [ ] Formalize operator checkpoint packet for live-transition readiness (still paper-only until explicit sign-off)

## [Later]
- [ ] Dynamic S/R level initiative integration (phase-gated sidecar)
- [ ] Automated watchlist refresh/diff alerts for shared TradingView list inputs
- [ ] Additional TradingView automation beyond current artifact-linking contract

## [Blocked]
- none

## [Done]
- [x] Hybrid pipeline tasks T4–T8 completed via initiative runner (2026-02-15)
- [x] Phase 0 dependency default/stub baseline landed (T1–T7) — fail-closed placeholders + operator dependency gates (2026-02-18)
- [x] Paper implementation wave1 delivered Tasks 19–24, 14–17, and 26 with tests + evidence artifact (`initiatives/liquidsniper-paper-implementation-wave1-2026-02-18.md`) (2026-02-19)
- [x] Daily-loss circuit breaker hard-wired as first paper gate (`RISK_DAILY_LOSS_CAP_BREACH`) with daemon/runbook/test updates (commit `b943f15`) (2026-02-20)
