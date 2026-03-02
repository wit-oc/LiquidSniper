# Phase Sequence Execution Plan

## Control principle
Implement and certify one phase at a time. No cross-phase tuning.

## Phase 0 — Wave Engine Foundations
- Build canonical wave/state machine
- Certify events and anchors
- Deliver deterministic logs + counts

## Phase 1 — HTF Bias Certification
- Use Phase 0 engine on 1D
- Validate direction/confidence timelines on TV + Python parity

## Phase 2a — Watch Engine: POI + Fib context
- Start/stop watch windows
- No triggers

## Phase 2b — Watch lifecycle
- Expire/invalid states and reason telemetry

## Phase 3a — Trigger Engine: candle confirmation
- Soft candle scoring only

## Phase 3b — Trigger Engine: retest ordinal
- Retest weighting and one-shot behaviors

## Phase 3c — Trigger score calibration
- Threshold tuning only after 3a/3b are certified

## Phase 4 — Risk/Execution
- Confidence-tier sizing
- TP/BE/stop lifecycle

## Phase 5 — Config-only tuning
- No logic rewrites
- Guardrails + dead-knob detector enforced

## Phase 6 — Promotion/parity
- Pine/Python parity
- operator runbook + failure modes
