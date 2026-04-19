# Phase 2A.3 -> Phase 2A.4 dynamic handoff note

Status: DRAFT COMPATIBILITY NOTE  
Date: 2026-04-14  
Phase edge: 2A.3 -> 2A.4

## Purpose
Define the minimal raw dynamic-level fields that Phase 2A.4 may consume without pulling trade interpretation up into Surveyor.

## Handoff posture
Phase 2A.3 should hand off a **raw/descriptive packet** from `engine/dynamic_levels.py`.

That means 2A.4 may safely read:
- header fields:
  - `symbol`
  - `as_of_ts`
  - `intended_direction` when provided upstream
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
- per-level raw fields:
  - `level_name`
  - `timeframe`
  - `available`
  - `level_value`
  - `price_side`
  - `distance_abs`
  - `distance_pct`
  - `zone_relation`
  - `timeframe_bar_ts`
  - `availability_reason`

## Not part of the 2A.3 canonical handoff
These are intentionally **not** part of the canonical 2A.3 dataset after the architecture ruling:
- `watcher_label`
- `strength_hint`
- `dynamic_context_label`
- `macro_context_label`
- `local_flow_label`
- `contrary_macro_present`
- `notes_for_analysis_engine`

## Safe downstream use in 2A.4
Allowed uses:
- normalize the raw dynamic dataset into a stable Surveyor contract
- preserve raw truth fields for replay and audit
- package the dynamic dataset alongside structure, S/R, and Fib outputs
- prepare an Arbiter-facing contract without deciding what the dynamic data means for trade quality

Not allowed in 2A.4 from this tranche alone:
- treating raw dynamic geometry as execution judgment by itself
- letting dynamic levels overrule structure permission inside Surveyor
- converting raw dynamic fields into hidden trade-quality labels and presenting them as if they were raw facts

## Arbiter boundary
Arbiter is the layer that should decide things like:
- whether higher-timeframe friction is materially adverse
- how dynamic context changes confidence
- how risk size should adjust
- whether dynamic evidence contributes to go / no-go

## Contract stability note
The current helper contract is packet-first and replay-friendly.
If 2A.4 needs flattened fields, it should prefer a transparent adapter layer over mutating 2A.3 into a judgment layer.

## Current open edges
Still open before full certification closeout:
- fuller provenance threading from upstream event/swing surfaces
- canonical runner-log wiring strategy
- final threshold review for `near_zone` / `far_from_zone`
- final 2A.4 packaging contract shape

## Bottom line
2A.4 should consume 2A.3 as **raw Surveyor data**.
It may wrap, normalize, and package that data, but Arbiter should remain the first layer that interprets what the dynamic surfaces mean for trade structure, risk, and execution.
