# Phase 2 S/R Promotion Gate — 2026-03-16

## Purpose

Define the explicit gate for moving out of build churn and into validation / config tweaking.

This gate exists so we do not confuse:
- better architecture
- better UI
- and actual model-truth confidence

## Promotion target

We consider Phase 2 ready to enter **validation/config tweaking mode** when all of the following are true.

## Gate A — Authoritative Levels View exists
A dedicated operator-facing view exists for the **shadow path** that shows:

### 1D
- below current price / support
- contains current price / active band
- above current price / resistance

### 4H
- below current price / support
- contains current price / active band
- above current price / resistance

And each section is:
- sorted lowest → highest
- labeled by `current_role`
- with `origin_kind` secondary

## Gate B — Review surfaces are semantically clean
The operator can clearly distinguish:
- baseline vs shadow
- raw candidates vs selected majors
- origin/provenance vs current execution-facing role

## Gate C — Selector truth is traced well enough
For BTC and ETH, we can explain where truth is lost (if lost):
- raw candidates
- merged candidates
- selected majors
- nearest ladders

We should be able to answer, concretely:
- Did the level exist?
- Did merge remove it?
- Did selection remove it?
- What won instead, and why?

## Gate D — Human chart validation loop is usable
Redact can use the authoritative view to compare the engine levels against marked chart levels and classify them as:
- good
- borderline
- wrong

without reverse-engineering debug payloads.

## Gate E — Tuning knobs are isolated
We know which next changes are:
- semantics / review-surface work
- selector / model-truth work
- config / threshold / weighting tweaks

This prevents “tuning” from hiding another redesign pass.

## Two execution lanes before promotion

### Lane A — Authoritative Levels View
Goal:
- satisfy Gate A and most of Gate B

### Lane B — Selector Truth Closure
Goal:
- satisfy Gate C

### Join point
Once both lanes are complete, run the first human chart validation pass.
That is the transition into validation/config tweaking mode.

## What is explicitly not part of this gate
Do not require these before entering validation/config tweaking mode:
- final certification across every pair
- full ATR / lifecycle refinement
- another broad architecture rewrite

Those may still matter later, but they are not the threshold for leaving build churn.

## Bottom line

We exit build churn when:
1. the levels are visible in a clean authoritative view,
2. the remaining selector-truth issues are traceable,
3. and a human chart-validation loop is practical.
