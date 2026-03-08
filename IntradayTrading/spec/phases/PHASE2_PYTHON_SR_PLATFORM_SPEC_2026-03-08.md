# Phase 2 Pivot Spec — Python S/R Platform + Verification Web Layer (2026-03-08)

Status: DRAFT FOR VALIDATION  
Scope anchor: Phase 2 WATCH/INVALID/EXPIRED context only (no trigger-entry execution logic)

## 1) Decision

We are splitting responsibilities:

- **Python = source-of-truth research engine**
  - full zone discovery
  - full scoring/lifecycle
  - multi-symbol processing
- **Web layer (Streamlit) = operator verification surface**
  - nearest actionable zones
  - full historical zone map drill-down
  - range/zone analytics observability
- **Pine = optional lightweight viewer only**
  - nearest-4 display parity checks (not full map computation)

This avoids forcing Pine to do full-map + lifecycle + execution-viewer in one runtime.

---

## 2) Initial symbol scope

Phase 2 Python platform starts with:
- `BTCUSDT`
- `ETHUSDT`

Timeframes for initial cert:
- 1D (primary)
- 4H (secondary, for context preview)

---

## 3) Product outcomes (MVP)

For each symbol/timeframe, operator can view:

1. **Nearest 4 zones around current price**
   - nearest support
   - next support below
   - nearest resistance
   - next resistance above

2. **Expanded historical map (optional)**
   - all active/retired zones
   - birth/update timeline
   - lifecycle transitions

3. **Range analytics tied to zone logic**
   - zone width (% + ATR)
   - touch/retest counts
   - first-retest outcome metrics
   - quality component scores (structure/base/launch/behavior)

4. **Exportable deterministic outputs**
   - JSON snapshot per symbol/timeframe
   - nearest-4 payload for downstream systems

---

## 4) Architecture (containerized)

Use a 3-process container stack (single compose project):

### A) `sr-worker` (Python)
- Pull candles for BTC/ETH on configured timeframes.
- Run S/R engine pass on schedule or on-demand.
- Persist outputs to DB + JSON artifacts.

### B) `sr-api` (Python FastAPI)
- Read-only API over persisted zone state.
- Endpoints for nearest-4, full-map, and diagnostics.
- Can later serve as backend for execution engine.

### C) `sr-web` (Streamlit)
- Operator UI for verification.
- Queries API/DB and renders pair dashboards.
- Includes nearest-4 card, historical zone list, and analytics panels.

Persistence:
- SQLite for MVP (existing project pattern).
- Artifact files under mounted `/data/artifacts/sr/` for reproducible snapshots.

---

## 5) Data contract (v1)

### Zone record (`zone_snapshot_v1`)
- `zone_id`
- `symbol`
- `tf`
- `struct_low`, `struct_high`, `struct_mid`
- `core_low`, `core_high`, `core_mid`
- `zone_class` (`structural` | `tradeable`)
- `zone_state` (`virgin` | `first_touch_ready` | `tested_once` | `spent` | `broken`)
- `score_total`
- `score_components` (structure/base/launch/behavior/etc)
- `touch_count`, `meaningful_touch_count`
- `has_first_retest`, `first_retest_result`, `first_retest_reaction_atr`
- `times_clean_reject`, `times_closed_through`
- `birth_ts`, `updated_ts`
- `source_version`

### Nearest-4 payload (`nearest_sr_v1`)
- `symbol`, `tf`, `asof_ts`, `last_price`
- `nearest_support`
- `next_support`
- `nearest_resistance`
- `next_resistance`
- each level includes:
  - `zone_id`
  - `distance_bps`
  - `struct_bounds`
  - `core_bounds`
  - `class`, `state`
  - `score_total`
  - `first_retest_status`

---

## 6) Selection rules for nearest-4

Distance is edge-based, not midpoint-only:
- Support distance: `max(0, price - zone_high)`
- Resistance distance: `max(0, zone_low - price)`
- Overlap with current price => distance `0`

Selection:
- 2 nearest support-side zones
- 2 nearest resistance-side zones
- If insufficient on one side, expand search horizon and retry.

---

## 7) Web UI spec (Streamlit)

### Page 1: Pair Overview
- Symbol/timeframe selector (BTC/ETH, 1D/4H)
- Current price + as-of timestamp
- Nearest-4 cards with distance + state + score
- “Why this zone” panel (score components + lifecycle stats)

### Page 2: Historical Zone Explorer
- Full zone list (filters: class/state/date range)
- Drill-down to zone detail
- Touch/retest timeline

### Page 3: Diagnostics
- Engine runtime metrics
- event counts, dedupe counts, zone counts
- rejects breakdown (width/lifecycle/other)
- latest run status

### Page 4: Export / Integration
- Download nearest-4 JSON
- Download full-map JSON
- Endpoint snippets for backend consumers

---

## 8) API endpoints (MVP)

- `GET /health`
- `GET /symbols`
- `GET /zones/latest?symbol=BTCUSDT&tf=1D`
- `GET /zones/history?symbol=BTCUSDT&tf=1D&limit=...`
- `GET /zones/nearest?symbol=BTCUSDT&tf=1D&price=...`
- `GET /diagnostics/latest?symbol=BTCUSDT&tf=1D`

---

## 9) Execution plan (incremental)

## Step A — Backend contract + persistence
- Add/extend DB schema for envelope+core + lifecycle fields.
- Implement `zone_snapshot_v1` serialization.
- Implement nearest-4 selector service.

## Step B — Worker pipeline
- Build deterministic run for BTC/ETH (1D + 4H).
- Persist full-map and nearest-4 snapshots.
- Add CLI entrypoint for on-demand runs.

## Step C — API layer
- Expose read-only endpoints above.
- Add OpenAPI docs and validation.

## Step D — Streamlit verification UI
- Build four pages above.
- Add symbol/timeframe controls.
- Add JSON export buttons.

## Step E — Containerization
- Compose stack with `sr-worker`, `sr-api`, `sr-web`.
- Data volume mount for DB/artifacts.
- One-command local startup.

---

## 10) Acceptance criteria (Phase 2 pivot)

1. BTC/ETH nearest-4 outputs are generated deterministically for 1D+4H.
2. Streamlit shows nearest-4 + full map + diagnostics without manual SQL.
3. API returns stable contracts for downstream use.
4. Runtime is operationally fast (no Pine-style chart timeout issues).
5. Operator can verify and approve zones from web layer without Pine dependency.

---

## 11) Non-goals (for this MVP)

- No auto trade execution.
- No 15m trigger engine in this phase.
- No multi-exchange breadth.
- No full portfolio orchestration.

---

## 12) What’s next after MVP passes

- Add more symbols/timeframes.
- Add Pine lightweight nearest-4 overlay for optional visual parity.
- Feed nearest-4 payload into future execution engine interface.
- Advance to Phase 3 trigger pipeline only after watcher cert confidence is stable.
