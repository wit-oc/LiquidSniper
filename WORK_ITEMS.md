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

## Phase 2 certification wave (2026-04-13)

- [x] **[Done]** Task DL-01 — Phase 2A.3 dynamic-level packet helper: lock contract, raw `1D`/`4H` anchored `YVWAP` / `QVWAP`, `1D` rolling `RYVWAP` / `RQVWAP`, `EMA200` / `EMA12`, and deterministic provenance threading.
- [x] **[Done]** Task DL-02 — Phase 2A.3 price-relative + zone-relative mapping plus raw-only runner/log adapter export, with evaluative labels removed from the canonical packet.
- [x] **[Done]** Task DL-03 — Phase 2A.3 replay certification artifacts (BTC + ETH), raw-only Phase 2A.4 handoff compatibility note, and runner/log adapter proof artifacts.

## Surveyor v1 checkpoint (2026-04-19)

Completed in the current checkpoint:
- [x] **[Done]** SV-01 — Canonical Surveyor packet assembly path wired from repo-local structure/Fib/dynamic-level contracts plus authoritative SR surfaces (`liquidsniper/core/surveyor_snapshot.py`, `IntradayTrading/engine/surveyor_packet.py`).
- [x] **[Done]** SV-02 — Canonical feed refresh path for Surveyor via OKX/CCXT into `market_candles` + `feed_checkpoints` for `5m`, `4h`, `1d`, `1w` (`liquidsniper/ops/surveyor_feed_refresh.py`).
- [x] **[Done]** SV-03 — Streamlit Surveyor Packet tab wired into the audit UI, with repo-root path fixes so the app can launch outside the repo cwd (`liquidsniper/web/app.py`).
- [x] **[Done]** SV-04 — Snapshot tests covering store-preferred timeframe loading and complete/partial packet states (`tests/test_surveyor_snapshot.py`).

Next:
- [ ] **[Next]** SV-05 — Freeze one shared structure/provenance adapter across Surveyor packet assembly and downstream consumers.
- [ ] **[Next]** SV-06 — Define the Arbiter handoff contract so interpretation/decision logic stays separate from Surveyor’s descriptive packet.
- [ ] **[Next]** SV-07 — Build robust backtesting/simulation on top of the canonical Surveyor packet + canonical candle store, rather than ad hoc legacy analytics paths.

## Deferred backlog (not dropped)

- [ ] Dynamic S/R level initiative integration (phase-gated sidecar)
- [ ] SR Engine V2 implementation wave (see `docs/SR_ENGINE_V2_SPEC.md`, tasks SRV2-T0..T8)
- [ ] Automated watchlist refresh/diff alerts for TradingView list inputs
- [ ] Additional TradingView automation beyond current artifact-linking contract
