# Phase 2 SR timeframe-refinement checkpoint — 2026-03-25

## Status

- state: local ready-for-review checkpoint
- branch: `phase2-zone-engine-v3`
- base HEAD: `d9e0e6f9ae1f79f613d6d9dc1c979fc1e0d9a574`
- note: worktree includes local Phase 2 refinement changes; this checkpoint is intentionally artifact-first, not yet a remote push anchor

## What was repaired in this checkpoint

- Reconciled `liquidsniper/core/pair_analytics.py` after the Mar 25 cleanup pass introduced a duplicate `summarize_zone_for_pair_analytics()` definition.
- Preserved the new Daily macro/core contract while restoring the `reference_price` call path used by `build_pair_analytics_snapshot()`.
- Re-ran the narrow validation suite and regenerated BTC/ETH shadow artifacts from the current worktree.

## Validation run

```bash
python3 -m pytest -q tests/test_pair_analytics.py tests/test_zone_engine_v3.py tests/test_sr_authoritative_levels_ui.py tests/test_sr_shadow_authoritative_view.py
```

- result: **26 passed**

## Artifact refresh run

```bash
python3 -m liquidsniper.ops.sr_bootstrap --shadow-v3 --symbols BTCUSDT,ETHUSDT
```

- result: `{"ok": true, "symbols": ["BTCUSDT", "ETHUSDT"]}`

## Refreshed artifact files

- `data/artifacts/sr/shadow/v3/bootstrap_snapshot.json`
- `data/artifacts/sr/shadow/v3/nearest_BTCUSDT.json`
- `data/artifacts/sr/shadow/v3/nearest_ETHUSDT.json`
- `data/artifacts/sr/shadow/v3/run_status.json`

## Live stack verification

- `docker compose -f docker-compose.sr.yml up -d --build` completed successfully
- `liquidsniper-sr-web` is up and `http://127.0.0.1:8501/` returns `HTTP/1.1 200 OK`
- `liquidsniper-sr-worker` completed with `Exited (0)` after bootstrap

## BTCUSDT authoritative snapshot

- last_price / entry: `69,679`
- **1D**
  - `below_price` count: **6**
    - `BTCUSDT:1D:base:371:support` | kind=`support` | display=`core` | bounds `17,618 -> 17,809 -> 18,000` | macro `16,908.7 -> 18,248.67 -> 20,468` | core `17,618 -> 17,809 -> 18,000`
    - `BTCUSDT:1D:base:305:resistance` | kind=`support` | display=`core` | bounds `20,399.1 -> 20,937.5 -> 21,475.9` | macro `17,024.4 -> 20,682.82 -> 22,992.4` | core `20,399.1 -> 20,937.5 -> 21,475.9`
  - `contains_price` count: **0**
  - `above_price` count: **2**
    - `BTCUSDT:1D:base:1201:support` | kind=`resistance` | display=`core` | bounds `83,957.96 -> 84,809.48 -> 85,661` | macro `83,107.6 -> 85,360.48 -> 88,715.36` | core `83,957.96 -> 84,809.48 -> 85,661`
    - `BTCUSDT:1D:base:1280:support` | kind=`resistance` | display=`core` | bounds `107,255.7 -> 108,516.75 -> 109,777.8` | macro `106,510.18 -> 109,585.4 -> 113,400` | core `107,255.7 -> 108,516.75 -> 109,777.8`
- **4H**
  - `below_price` count: **3**
    - `BTCUSDT:4H:2:62760.15` | kind=`support` | display=`macro` | bounds `62,595.27 -> 62,760.15 -> 62,925.03` | macro `62,595.27 -> 62,760.15 -> 62,925.03` | core `62,595.27 -> 62,760.15 -> 62,925.03`
    - `BTCUSDT:4H:3:65832.89` | kind=`support` | display=`macro` | bounds `65,182.46 -> 65,832.89 -> 66,483.32` | macro `65,182.46 -> 65,832.89 -> 66,483.32` | core `65,182.46 -> 65,832.89 -> 66,483.32`
  - `contains_price` count: **0**
  - `above_price` count: **9**
    - `BTCUSDT:4H:6:72602.9` | kind=`resistance` | display=`macro` | bounds `72,413.96 -> 72,602.9 -> 72,791.84` | macro `72,413.96 -> 72,602.9 -> 72,791.84` | core `72,413.96 -> 72,602.9 -> 72,791.84`
    - `BTCUSDT:4H:7:74777.0` | kind=`resistance` | display=`macro` | bounds `74,302.4 -> 74,777 -> 75,251.6` | macro `74,302.4 -> 74,777 -> 75,251.6` | core `74,302.4 -> 74,777 -> 75,251.6`

## ETHUSDT authoritative snapshot

- last_price / entry: `2,024.86`
- **1D**
  - `below_price` count: **2**
    - `ETHUSDT:1D:structure:flip_anchor:168:468:support` | kind=`support` | display=`core` | bounds `881 -> 983.81 -> 1,086.62` | macro `881 -> 1,082.58 -> 1,258.56` | core `881 -> 983.81 -> 1,086.62`
    - `ETHUSDT:1D:base:1202:support` | kind=`support` | display=`core` | bounds `1,562.87 -> 1,610.85 -> 1,658.83` | macro `1,384.28 -> 1,570.08 -> 1,671.55` | core `1,562.87 -> 1,610.85 -> 1,658.83`
  - `contains_price` count: **2**
    - `ETHUSDT:1D:base:1216:support` | kind=`containing` | display=`core` | bounds `1,781.42 -> 1,827.63 -> 1,873.85` | macro `1,751.45 -> 1,901.57 -> 2,689.15` | core `1,781.42 -> 1,827.63 -> 1,873.85`
    - `ETHUSDT:1D:base:1177:resistance` | kind=`containing` | display=`core` | bounds `2,006.02 -> 2,011.01 -> 2,016` | macro `1,941.86 -> 2,047.17 -> 2,158.2` | core `2,006.02 -> 2,011.01 -> 2,016`
  - `above_price` count: **4**
    - `ETHUSDT:1D:structure:bos_anchor:933:946:resistance` | kind=`resistance` | display=`core` | bounds `3,439.6 -> 3,501.3 -> 3,563` | macro `3,318 -> 3,489.21 -> 3,658.66` | core `3,439.6 -> 3,501.3 -> 3,563`
    - `ETHUSDT:1D:structure:bos_anchor:1067:1068:support` | kind=`resistance` | display=`core` | bounds `3,500.22 -> 3,572.01 -> 3,643.8` | macro `3,500.22 -> 3,631.96 -> 3,726.98` | core `3,500.22 -> 3,572.01 -> 3,643.8`
- **4H**
  - `below_price` count: **2**
    - `ETHUSDT:4H:2:1827.637` | kind=`support` | display=`macro` | bounds `1,813.08 -> 1,827.64 -> 1,842.19` | macro `1,813.08 -> 1,827.64 -> 1,842.19` | core `1,813.08 -> 1,827.64 -> 1,842.19`
    - `ETHUSDT:4H:base:696:resistance` | kind=`support` | display=`macro` | bounds `1,935.03 -> 1,972.06 -> 2,014.91` | macro `1,935.03 -> 1,972.06 -> 2,014.91` | core `1,935.03 -> 1,972.06 -> 2,014.91`
  - `contains_price` count: **0**
  - `above_price` count: **10**
    - `ETHUSDT:4H:structure:bos_anchor:587:595:resistance` | kind=`resistance` | display=`macro` | bounds `2,149.65 -> 2,293.69 -> 2,402.4` | macro `2,149.65 -> 2,293.69 -> 2,402.4` | core `2,149.65 -> 2,293.69 -> 2,402.4`
    - `ETHUSDT:4H:structure:flip_anchor:141:215:support` | kind=`resistance` | display=`macro` | bounds `2,622.87 -> 2,665.36 -> 2,713.35` | macro `2,622.87 -> 2,665.36 -> 2,713.35` | core `2,622.87 -> 2,665.36 -> 2,713.35`

## Review guidance

- Use `bootstrap_snapshot.json` authoritative views as the primary review surface for chart validation.
- Treat the `nearest_*.json` files as diagnostic helpers, not the final operator truth surface.
- Current questions are now refinement questions (borderline span / clustering quality), not broken-contract questions.

## Dirty files in this local checkpoint

- `M docs/zone_schema_v2.md`
- ` M liquidsniper/core/pair_analytics.py`
- ` M liquidsniper/core/zone_engine_v3.py`
- ` M liquidsniper/core/zone_selectors.py`
- ` M liquidsniper/ops/sr_bootstrap.py`
- ` M liquidsniper/web/app.py`
- ` M tests/test_pair_analytics.py`
- ` M tests/test_zone_engine_v3.py`
- `?? IntradayTrading/spec/phases/PHASE2_V7A_GEOMETRY_CORE_LIFECYCLE_ACP_TASKS_2026-03-08.md`
- `?? IntradayTrading/spec/phases/PHASE2_V7A_HYBRID_REBALANCE_ACP_TASKS_2026-03-08.md`
- `?? IntradayTrading/spec/phases/PHASE2_V7A_HYBRID_REBALANCE_EXEC_PLAN_2026-03-08.md`
- `?? docs/PAPER_SOAK_DAY0_PACKET.md`
- `?? docs/PAPER_SOAK_PROTOCOL_V1.md`
- `?? docs/PHASE2_SR_GATEC_CLOSURE_SUMMARY_2026-03-16.md`
- `?? docs/PHASE2_SR_GATEC_SELECTOR_DOCTRINE_COMPARISON_2026-03-16.md`
- `?? docs/PHASE2_SR_GATEC_TRACE_BTC_2026-03-16.md`
- `?? docs/PHASE2_SR_GATEC_TRACE_ETH_2026-03-16.md`
- `?? docs/PHASE2_SR_PROMOTION_GATE_2026-03-16.md`
- `?? docs/PHASE2_SR_TIMEFRAME_REFINEMENT_MATRIX_2026-03-24.md`
- `?? docs/PHASE2_SR_TIMEFRAME_REFINEMENT_RULES_2026-03-24.md`
- `?? tests/test_sr_authoritative_levels_ui.py`
- `?? tests/test_sr_shadow_authoritative_view.py`
- `?? tools/strategy_sweep/data/`
- `?? tools/strategy_sweep/outputs/c_profile_run_20260226T112607Z/`
- `?? tools/strategy_sweep/outputs/i_profile_run_20260226T061437Z/`
- `?? tools/strategy_sweep/outputs/s_profile_run_20260226T112607Z/`
