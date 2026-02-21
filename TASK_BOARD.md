# Task Board — LiquidSniper

Status legend: [Now] [Next] [Later] [Blocked] [Done]

## [Now]
- [ ] Execute full-scope plan in `docs/PAPER_MULTISTRATEGY_DELIVERY_PLAN_V1.md` (P0 safety + paper-only parallel lanes)
- [ ] Follow canonical execution order in `docs/MVP_PAPER_SEQUENCE_V1.md`
- [ ] Task 19: Lock market-data provider contract + canonical candle schema (`docs/DATA_FEED_STRATEGY_V1.md`)
- [ ] Task 20: Implement CCXT OHLCV backfill + incremental candle-close scheduler
- [ ] Task 21: Implement candle quality gates + aggregation policy
- [ ] Task 22: Integrate strategy path to canonical candles (trigger feed becomes context only)
- [ ] Task 14: Execute HTF-anchor rulebook contract implementation using `docs/HTF_ANCHOR_PROFILE_CONTRACT_V1.md` scaffold
- [ ] SRV2-T0..T8: Execute `docs/SR_ENGINE_V2_SPEC.md` (HTF-anchored pivot-zone S/R engine with >=3 meaningful touches)

## [Next]
- [ ] Task 23: Add provider rate-limit budgets + circuit breakers + feed health events
- [ ] Task 24: Finalize trigger-feed decoupling and rationale traceability
- [ ] Task 15: Align lecture-derived score buckets to deterministic decision payload fields
- [ ] Task 16: Thread dependencies and enforce non-bypass strategy -> policy -> execution boundaries
- [ ] Task 17: Add two-pass adversarial validation harness/gates
- [ ] Task 25: Implement native Blofin adapter fallback only if CCXT gap assessment fails coverage
- [ ] Task 26: Produce feed benchmark + paper-MVP gate evidence pack
- [ ] Task 18: Decide packaging boundary (integrated module vs separate execution-core service)

## [Later]
- [ ] Dynamic S/R level initiative integration (phase-gated sidecar)
- [ ] Automated watchlist refresh/diff alerts for shared TradingView list inputs
- [ ] Additional TradingView automation beyond current artifact-linking contract

## [Blocked]
- none

## [Done]
- [x] Hybrid pipeline tasks T4–T8 completed via initiative runner (2026-02-15)
- [x] Phase 0 dependency default/stub baseline landed (T1–T7): canonical sequence matrix, `.env.example` fail-closed placeholders, operator dependency stubs, go/no-go gate updates, Task 14 scaffold contract, and final unblocked/waiting checkpoint (2026-02-18)
