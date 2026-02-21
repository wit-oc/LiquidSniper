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

- [x] **[Done]** Task 09 — analysis run contract + pipeline skeleton
- [x] **[Done]** Task 10 — would-alert simulation mode
- [x] **[Done]** Task 11 — TradingView artifact linking + mount contract
- [x] **[Done]** Task 12 — minimal diagnostic UI updates
- [x] **[Done]** Task 13 — OpenClaw orchestration + rulebook/bootstrap + secrets flow
- [x] **[Done]** Task 05 — Telegram ingestion wiring integration hardening
- [x] **[Done]** Task 06 — Streamlit UI cleanup against diagnostic + card views
- [x] **[Done]** Task 07 — Docker/compose verification with shared artifact mount
- [x] **[Done]** Task 08 — runbook/validation gate update for simulation rollout

---

## Strategy automation alignment snapshot (2026-02-18)

- [x] **[Done]** Added `docs/AUTOMATED_TRADING_AGENT_ALIGNMENT_V1.md` (proposal -> LiquidSniper mapping)
- [x] **[Done]** Upgraded `docs/TRADING_STRATEGY_RUNBOOK_V1.md` to v1.1 (HTF-anchor + deterministic payload)
- [x] **[Done]** Added `docs/TRADING_STRATEGY_GLOSSARY_V1.md` (canonical strategy terminology + payload definitions)
- [x] **[Done]** Added canonical paper sequence: `docs/MVP_PAPER_SEQUENCE_V1.md`
- [x] **[Done]** Landed fail-closed dependency stubs (`.env.example`, `docs/OPERATOR_DEPENDENCY_STUBS_V1.md`, go/no-go stub gates)
- [x] **[Done]** Added Task 14 scaffold contract: `docs/HTF_ANCHOR_PROFILE_CONTRACT_V1.md`
- [ ] **[Now]** Task 14 implementation — wire rulebook/schema + regime permission integration
- [x] **[Done]** Drafted execution-core command contract (`docs/EXECUTION_CORE_COMMAND_CONTRACT_V1.md`) defining sub-agent safe interface and hard-reject reason-code model
- [ ] **[Next]** Task 15 — score mapping into deterministic payload fields
- [ ] **[Next]** Task 16 — dependency threading + non-bypass boundaries
- [ ] **[Next]** Task 17 — adversarial validation gates
- [ ] **[Next]** Task 18 — packaging boundary decision

---

## Data feed strategy snapshot (2026-02-18)

Canonical decision: **strategy-grade analysis must use canonical OHLCV feed**; Mobchart Telegram remains trigger/context only.

Reference: `docs/DATA_FEED_STRATEGY_V1.md`

- [ ] **[Now]** Task 19 — market-data provider contract + canonical candle schema
- [ ] **[Now]** Task 20 — CCXT OHLCV backfill + incremental scheduler
- [ ] **[Now]** Task 21 — candle quality gates + aggregation policy
- [ ] **[Now]** Task 22 — strategy feed integration (canonical candles as baseline)
- [ ] **[Next]** Task 23 — rate-limit controls + circuit breakers + feed health events
- [ ] **[Next]** Task 24 — trigger feed decoupling + rationale traceability
- [ ] **[Next]** Task 25 — native Blofin adapter fallback (conditional)
- [ ] **[Next]** Task 26 — feed benchmark + paper-MVP gate evidence

---

## Sequencing note (canonical)

Use this sequence for current execution:

1. `docs/MVP_PAPER_SEQUENCE_V1.md` (phase order)
2. Data feed baseline Tasks **19 -> 22**
3. Strategy/governance Tasks **14 -> 18** (with Task 15 dependent on feed baseline fields)
4. Hardening + evidence Tasks **23 -> 26**

This keeps strategy implementation aligned with actual market-data requirements and avoids false confidence from trigger-only signals.

---

## Deferred backlog (not dropped)

- [ ] Dynamic S/R level initiative integration (phase-gated sidecar)
- [ ] SR Engine V2 implementation wave (see `docs/SR_ENGINE_V2_SPEC.md`, tasks SRV2-T0..T8)
- [ ] Automated watchlist refresh/diff alerts for TradingView list inputs
- [ ] Additional TradingView automation beyond current artifact-linking contract
