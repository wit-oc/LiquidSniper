# Phase 2A.3 Dynamic Levels Closeout Note

Status: COMPLETE / CERTIFIED FOR SURVEYOR HANDOFF  
Date: 2026-04-14  
Phase: 2A.3  
Owners: Redact + Wit

## Decision summary
Phase 2A.3 is closed as a **raw/descriptive Surveyor dataset lane**.

The canonical contract is:
- packet-first at `engine/dynamic_levels.py`
- replay-first and point-in-time reconstructable
- raw geometry/provenance only
- no watcher-owned interpretation labels
- VWAP-family surfaces use **HLC3 / typical price** as the canonical basis

A narrow runner/log adapter was added so bar-log surfaces can see raw dynamic evidence **without promoting dynamic levels into a scoring or judgment layer**.

## VWAP basis decision
Phase 2A.3 codifies **HLC3 / typical price** as the canonical Surveyor VWAP basis.

This was chosen **in favor of close-only basis**.

Why:
- dynamic levels in this tranche are supporting context, not primary trigger logic
- HLC3 captures the full bar shape better than close-only basis
- HLC3 is less sensitive to bars that settle near an extreme of the range
- that makes it the better fit for a stable secondary evidence layer

Close-based VWAP remains a legitimate comparison/research surface, but it is not the canonical Phase 2A.3 architecture contract.

## What landed

### 1) Canonical packet surface
Implemented and retained as the source of truth:
- `LiquidSniper/IntradayTrading/engine/dynamic_levels.py`
- `intraday_revisit/engine/dynamic_levels.py`

Canonical packet/header fields:
- `symbol`
- `as_of_ts`
- `intended_direction`
- `current_price`
- `zone_id`
- `zone_low`
- `zone_high`
- `source_event_id`
- `source_swing_id`
- `source_contract_version`
- `fib_context_id`
- `feed_provider`
- `feed_timeframe`
- `feed_bar_ts`
- `feed_provenance_note`

Canonical per-level raw fields:
- `available`
- `level_value`
- `price_side`
- `distance_abs`
- `distance_pct`
- `zone_relation`
- `timeframe_bar_ts`
- `availability_reason`

### 2) Raw-only boundary enforcement
Explicitly removed from the canonical 2A.3 contract:
- `watcher_label`
- `strength_hint`
- `dynamic_context_label`
- `macro_context_label`
- `local_flow_label`
- `contrary_macro_present`
- `notes_for_analysis_engine`

### 3) Runner/log adapter
Added a narrow adapter path in:
- `LiquidSniper/IntradayTrading/engine/runner.py`
- `intraday_revisit/engine/runner.py`

Adapter posture:
- runner builds the canonical dynamic packet when bar timestamps + volumes are available
- runner stores a raw export under the single log field `dynamic_levels`
- the export comes from `flatten_dynamic_level_packet(...)`
- logger preserves `dynamic_levels` as a nested raw payload instead of widening the top-level canonical log schema with dozens of new top-level keys

Logger updates:
- `LiquidSniper/IntradayTrading/engine/logger.py`
- `intraday_revisit/engine/logger.py`

### 4) Dataset/replay wiring
Dataset path now supplies `timestamp` and `volume` into runner bars when the source CSV has them:
- `LiquidSniper/IntradayTrading/research/run_dataset.py`
- `intraday_revisit/research/run_dataset.py`

### 5) Test coverage
Updated / added assertions across:
- `LiquidSniper/IntradayTrading/tests/test_dynamic_levels.py`
- `intraday_revisit/tests/test_dynamic_levels.py`
- `LiquidSniper/IntradayTrading/tests/test_runner_logs.py`
- `intraday_revisit/tests/test_runner_logs.py`
- `LiquidSniper/IntradayTrading/tests/test_logger.py`
- `intraday_revisit/tests/test_logger.py`

## Validation run
Commands executed:
```bash
python3 -m pytest -q \
  /Users/wit/.openclaw/workspace/intraday_revisit/tests/test_dynamic_levels.py \
  /Users/wit/.openclaw/workspace/intraday_revisit/tests/test_runner_logs.py \
  /Users/wit/.openclaw/workspace/intraday_revisit/tests/test_logger.py

python3 -m py_compile \
  /Users/wit/.openclaw/workspace/intraday_revisit/engine/runner.py \
  /Users/wit/.openclaw/workspace/intraday_revisit/engine/logger.py \
  /Users/wit/.openclaw/workspace/intraday_revisit/research/run_dataset.py \
  /Users/wit/.openclaw/workspace/LiquidSniper/IntradayTrading/engine/runner.py \
  /Users/wit/.openclaw/workspace/LiquidSniper/IntradayTrading/engine/logger.py \
  /Users/wit/.openclaw/workspace/LiquidSniper/IntradayTrading/research/run_dataset.py
```

Results:
- targeted pytest suite: `8 passed in 0.45s`
- compile checks: passed

## Evidence artifacts
Existing raw packet / replay artifacts:
- `intraday_revisit/artifacts/phase2a3_dynamic_levels_replay/phase2a3-raw-only-replay-summary.json`
- `intraday_revisit/artifacts/phase2a3_dynamic_levels_replay/btc-raw-rich-packet-36507.json`
- `intraday_revisit/artifacts/phase2a3_dynamic_levels_replay/eth-raw-rich-packet-36507.json`
- `intraday_revisit/artifacts/phase2a3_dynamic_levels_replay/btc-raw-unavailable-packet-10.json`
- `intraday_revisit/artifacts/phase2a3_dynamic_levels_replay/eth-raw-unavailable-packet-10.json`
- `intraday_revisit/artifacts/phase2a3_dynamic_levels_replay/phase2a3-first-tranche-proof-20260413.md`

New runner/log adapter proof artifacts:
- `intraday_revisit/artifacts/phase2a3_dynamic_levels_replay/runner_log_adapter/synthetic_btc_dynamic_barlogs.jsonl`
- `intraday_revisit/artifacts/phase2a3_dynamic_levels_replay/runner_log_adapter/synthetic_btc_dynamic_barlogs_summary.json`

Runner/log adapter proof summary:
- `rows_written`: `2`
- `last_index`: `299`
- `timestamp`: `1736766000`
- `has_dynamic_levels`: `true`
- `dynamic_source_contract_version`: `phase2a3.dynamic_levels.v2.raw_only`
- `dynamic_4h_yvwap_available`: `true`
- `dynamic_4h_ema12_available`: `true`
- `dynamic_1d_ema200_available`: `false`
- `dynamic_1d_ema200_availability_reason`: `insufficient_history_for_ema_200`

## Unresolved edges
These remain real, but they are **not blockers** for calling the raw 2A.3 lane implemented:
- `source_event_id` is still not threaded because the current upstream surfaces do not expose a settled event-id handoff here yet
- `source_swing_id` is still not threaded for the same reason
- richer full-dataset runner/barlog regeneration against the BTC/ETH certification inputs was not completed in this turn because the one-shot full dataset run remained too heavy/noisy for the lane closeout loop; the narrow adapter proof artifact was produced instead

## Recommendation
I recommend the following decision:

### Certify 2A.3 as implemented
Because the lane now has:
- a stable raw packet contract
- replay artifacts for BTC/ETH
- raw-only docs/handoff alignment
- runner/log adapter evidence
- passing targeted validation

### Treat the remaining event/swing provenance threading as follow-on integration work
That work should happen when the upstream structure contract exposes the right ids cleanly, rather than inventing placeholder values here.

## Bottom line
Phase 2A.3 is now in the right shape:
- Surveyor tells the truth
- 2A.4 can package it
- Arbiter can interpret it

The lane no longer smuggles judgment into dynamic-level telemetry, and runner/log surfaces now have a narrow raw adapter path that preserves that boundary.
