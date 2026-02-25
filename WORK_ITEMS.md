# LiquidSniper — Work Items

This is the repo-native work tracker for LiquidSniper implementation sequencing.

Tracking anchors:
- Discord: `#radiant-research` (discussion + decisions)
- Repo board: `TASK_BOARD.md` (execution state)
- This file: `WORK_ITEMS.md` (snapshot + sequencing context)

Conventions:
- One checkbox per item.
- Keep item size to ~1–2 PRs where possible.
- Prefer deterministic acceptance artifacts.

Status tags:
- **[Now]** active
- **[Next]** queued
- **[Later]** deferred backlog
- **[Blocked]** waiting on dependency/decision

---

## Integration reconciliation snapshot (2026-02-15)

- [x] **[Done]** Task 05 — Telegram ingestion wiring integration hardening
- [x] **[Done]** Task 06 — Streamlit UI cleanup against diagnostic + card views
- [x] **[Done]** Task 07 — Docker/compose verification with shared artifact mount
- [x] **[Done]** Task 08 — runbook/validation gate update for simulation rollout
- [x] **[Done]** Task 09 — analysis run contract + pipeline skeleton
- [x] **[Done]** Task 10 — would-alert simulation mode
- [x] **[Done]** Task 11 — TradingView artifact linking + mount contract
- [x] **[Done]** Task 12 — minimal diagnostic UI updates
- [x] **[Done]** Task 13 — OpenClaw orchestration + rulebook/bootstrap + secrets flow

---

## Core paper implementation reconciliation (2026-02-21)

Reference artifact:
- `initiatives/liquidsniper-paper-implementation-wave1-2026-02-18.md`

Completed in wave1:
- [x] **[Done]** Task 19 — market-data provider contract + canonical candle schema
- [x] **[Done]** Task 20 — CCXT OHLCV backfill + incremental scheduler
- [x] **[Done]** Task 21 — candle quality gates + aggregation policy
- [x] **[Done]** Task 22 — strategy feed integration (canonical candles baseline)
- [x] **[Done]** Task 14 — HTF-anchor/runtime profile contract enforcement
- [x] **[Done]** Task 15 — deterministic score payload mapping
- [x] **[Done]** Task 16 — non-bypass strategy -> policy -> execution boundary
- [x] **[Done]** Task 17 — two-pass adversarial validation harness
- [x] **[Done]** Task 23 — rate-limit budgets + circuit breakers + feed health events
- [x] **[Done]** Task 24 — trigger-feed decoupling + traceability fields
- [x] **[Done]** Task 26 — feed benchmark + gate evidence pack (`artifacts/paper_mvp/task17_26_gate_evidence.json`)
- [x] **[Done]** Task 18 — packaging-boundary ADR accepted (`docs/ADR_0018_EXECUTION_PACKAGING_BOUNDARY.md`) (2026-02-23)

Still open:
- [ ] **[Next]** Task 25 — native Blofin adapter fallback (conditional on CCXT gap assessment)

Recent safety hardening:
- [x] **[Done]** Daily-loss circuit breaker set as first policy gate (`RISK_DAILY_LOSS_CAP_BREACH`) with policy/daemon/test/runbook updates (commit `b943f15`).

---

## Immediate execution sequence (post-cleanup)

1. **Task board hygiene lane**
   - [x] Retarget daily-lane selector to unresolved work only (`scripts/select_daily_lane.py`, 2026-02-25).
2. **Task 18 decision lane**
   - [x] Publish packaging-boundary ADR + fork triggers (`docs/ADR_0018_EXECUTION_PACKAGING_BOUNDARY.md`, accepted 2026-02-23).
3. **Evidence refresh lane**
   - Re-run targeted test/evidence suite after circuit-breaker changes.
4. **Paper soak lane**
   - 1–2 week paper run with fixed tuning cadence + kill/promotion criteria.
5. **Task 25 conditional lane**
   - Only if CCXT capability gap is confirmed.

---

## Deferred backlog (not dropped)

- [ ] Dynamic S/R level initiative integration (phase-gated sidecar)
- [ ] SR Engine V2 implementation wave (see `docs/SR_ENGINE_V2_SPEC.md`, tasks SRV2-T0..T8)
- [ ] Automated watchlist refresh/diff alerts for TradingView list inputs
- [ ] Additional TradingView automation beyond current artifact-linking contract
