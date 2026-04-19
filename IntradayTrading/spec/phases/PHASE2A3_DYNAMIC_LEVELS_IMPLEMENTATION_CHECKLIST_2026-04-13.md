# Phase 2A.3 Dynamic Levels Implementation Checklist

Status: COMPLETE / CERTIFIED  
Date: 2026-04-14  
Phase: 2A.3  
Owners: Redact + Wit

Primary spec:
- `LiquidSniper/IntradayTrading/spec/phases/PHASE2A3_DYNAMIC_LEVELS_SPEC_V1.md`

## Architecture ruling (2026-04-14)
Phase 2A.3 is a **raw/descriptive Surveyor dataset** tranche.

This lane should surface:
- anchored `YVWAP`, `QVWAP` on `1D` and `4H`
- rolling `RYVWAP`, `RQVWAP` on `1D` only
- `EMA200`, `EMA12`
- point-in-time `1D` and `4H` values
- price-relative geometry
- zone-relative geometry
- feed/provenance fields
- technical availability state when a value cannot yet be reconstructed

This lane should **not** surface:
- supportive / contrary labels
- macro or local-flow summaries
- confidence or risk implications
- execution-facing judgment

Canonical VWAP basis decision:
- use **HLC3 / typical price** for Surveyor VWAP-family surfaces
- do **not** use close-only basis as the canonical Phase 2A.3 architecture contract
- close-only basis may remain a research/operator comparison path, but not the canonical Surveyor output

Phase 2A.4 may wrap the contract.
Arbiter is the layer that should synthesize what the data means.

## Goal
Turn the Phase 2A.3 dynamic-level surface spec into a deterministic raw packet that later layers can consume without inheriting upstream opinion.

## Progress snapshot
Completed:
- helper boundary implemented at `LiquidSniper/IntradayTrading/engine/dynamic_levels.py`
- mirrored replay/test surface at `intraday_revisit/engine/dynamic_levels.py`
- certified timeframe packet surfaces implemented for `1D` and `4H`
- approved level set implemented: anchored `YVWAP`, `QVWAP` on `1D` and `4H`, rolling `RYVWAP`, `RQVWAP` on `1D`, plus `EMA200`, `EMA12`
- price-relative mapping implemented
- zone-relative mapping implemented
- replay/test surface exists under `intraday_revisit/artifacts/phase2a3_dynamic_levels_replay/`

Now being corrected/refined:
- remove evaluative fields from the canonical 2A.3 packet
- update docs/tests/replay artifacts to the raw-only contract

Follow-on after certification:
- fuller provenance threading from upstream event/swing surfaces
- next-phase wiring into the unified Surveyor packet/UI path

## Guardrails
- Do not turn this lane into a watcher-owned scoring engine.
- Do not let dynamic levels invent setups on their own.
- Do not introduce a separate candle-source contract from the rest of Phase 2.
- Keep point-in-time replay discipline on every step.
- Preserve provenance compatibility with the structure source-of-truth lane.
- Prefer descriptive geometry over inferred meaning.

## Definition of done for the lane
The lane is done when:
1. The watcher can emit a deterministic dynamic-level packet for `1D` and `4H`.
2. The packet includes anchored `YVWAP`, `QVWAP`, `EMA200`, and `EMA12` on `1D` and `4H`, plus `RYVWAP` and `RQVWAP` on `1D`.
3. Price-relative and zone-relative positioning are explicit for every level.
4. Feed / candle provenance is explicit.
5. Missing/unavailable values fail clearly.
6. BTC and ETH replay packets prove point-in-time reconstruction.
7. The output is ready for 2A.4 packaging and later Arbiter synthesis.

---

## Checklist

### 1) Lock the raw packet contract
- [x] Confirm canonical output path / module boundary for the dynamic-level packet.
- [x] Confirm the first implementation target is a helper-backed packet surface.
- [x] Confirm the packet is raw/descriptive only.
- [x] Confirm downstream-required provenance fields are threaded through unchanged where available.

**Exit proof:** packet contract and spec reflect the raw-only architecture ruling.

### 2) Lock feed and timeframe assumptions
- [x] Confirm `OKX` remains the provisional primary certification feed for this tranche.
- [x] Confirm the certified timeframes for this lane are `1D` and `4H`.
- [x] Confirm packet fields for feed provenance: provider, timeframe, bar timestamp, and provenance note.
- [x] Confirm no hidden alternate candle pull path is used during certification runs.

**Exit proof:** constants/docs reflect feed/timeframe assumptions.

### 3) Implement raw level computation / acquisition
- [x] Implement or wire acquisition for anchored `YVWAP`.
- [x] Implement or wire acquisition for anchored `QVWAP`.
- [x] Implement or wire acquisition for `RYVWAP` (`1D` only).
- [x] Implement or wire acquisition for `RQVWAP` (`1D` only).
- [x] Implement or wire acquisition for `EMA200`.
- [x] Implement or wire acquisition for `EMA12`.
- [x] Lock VWAP-family price basis to **HLC3 / typical price**.
- [x] Ensure all four levels are available for both `1D` and `4H` contexts when sufficient history exists.
- [x] Ensure every value is tied to the correct point-in-time bar.
- [x] Ensure missing/unavailable values fail clearly rather than silently degrading the packet.

**Exit proof:** raw-level snapshot can be emitted for historical bars on both certified timeframes.

### 4) Implement price-relative mapping
- [x] Compute `price_side` for each level (`above`, `below`, `overlapping`).
- [x] Compute `distance_abs` for each level.
- [x] Compute `distance_pct` for each level.
- [x] Ensure overlapping / near-zero cases are handled deterministically.

**Exit proof:** packet output shows stable price-relative fields for all approved certified level surfaces.

### 5) Implement zone-relative mapping
- [x] Read selected zone context from the upstream S/R surface when supplied.
- [x] Map each level relative to the active zone.
- [x] Emit `zone_relation` with the approved surface labels.
- [x] Confirm the mapper behaves correctly when the zone spans the level.
- [x] Confirm the mapper behaves correctly when levels cluster around the zone.

**Exit proof:** packet output includes explicit zone-relative fields for every level.

### 6) Enforce the interpretation boundary
- [x] Remove `watcher_label` from the canonical 2A.3 packet.
- [x] Remove `strength_hint` from the canonical 2A.3 packet.
- [x] Remove aggregate evaluative fields from the canonical 2A.3 packet.
- [x] Ensure docs and replay artifacts no longer frame 2A.3 as a judgment layer.

**Exit proof:** no evaluative dynamic fields remain in the raw packet surface.

### 7) Thread provenance and upstream references
- [x] Include `zone_id` / selected-zone reference.
- [ ] Include `source_event_id` when available.
- [ ] Include `source_swing_id` when available.
- [x] Include `source_contract_version` when available.
- [x] Include `fib_context_id` when available.
- [x] Verify compatibility with the sibling structure source-of-truth lane.

**Exit proof:** replay packet shows provenance fields populated as far as current upstream surfaces allow.

### 8) Add deterministic tests
- [x] Unit-test level computation / acquisition for `YVWAP`, `QVWAP`, `RYVWAP`, `RQVWAP`, `EMA200`, `EMA12`.
- [x] Unit-test price-side classification.
- [x] Unit-test zone-relation mapping.
- [x] Unit-test missing-data / null-data handling.
- [x] Unit-test point-in-time reconstruction on historical bars.
- [x] Remove evaluative-field expectations from tests.

**Exit proof:** targeted test suite passes against the raw-only contract.

### 9) Build replay / certification artifacts
- [x] Build at least one BTC replay packet.
- [x] Build at least one ETH replay packet.
- [x] Refresh artifacts so they prove the raw-only contract instead of evaluative labels.
- [x] Show exact bar timestamps, level values, price-relative fields, zone-relative fields, availability state, and provenance.
- [x] Save artifacts in a predictable Phase 2A.3 replay location.

**Suggested artifact family:**
- `intraday_revisit/artifacts/phase2a3_dynamic_levels_replay/...`

**Exit proof:** reviewer-facing raw packets exist and are sufficient to inspect dynamic-level truth without reading code.

### 10) Validate handoff into Phase 2A.4
- [x] Confirm 2A.4 treats 2A.3 as a raw dataset, not a scoring layer.
- [x] Confirm contract-wrapping logic is deferred downstream.
- [x] Confirm Arbiter remains the interpretation boundary.

**Exit proof:** short compatibility note exists for the raw-only handoff posture.

### 11) Closeout packet
- [x] Record implementation paths / modules touched.
- [x] Record tests run and results.
- [x] Record replay artifacts produced.
- [x] Record unresolved edge cases.
- [x] Record recommendation for remaining follow-on before certification.

**Exit proof:** a concise closeout note exists that would let the control thread decide whether 2A.3 is ready to certify.

---

## Suggested execution order
1. Raw packet contract correction
2. Doc correction
3. Test correction
4. Replay artifact refresh
5. Validation
6. Closeout note

## Explicit non-goals during implementation
Do **not** use this checklist as cover for:
- full analysis-engine scoring design
- reaction-evidence scoring
- lifecycle / expiry design
- trigger logic
- trade-entry permissioning
- introducing extra dynamic levels beyond the approved four

## Bottom line
The right implementation posture for 2A.3 is:
- surface the levels cleanly,
- map price and zone against them honestly,
- preserve provenance,
- fail clearly when unavailable,
- and stop before Surveyor starts making Arbiter’s judgments.
