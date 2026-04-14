# Phase 2 S/R V3 Redesign Proposal — 2026-03-15

Branch: `phase2-zone-engine-v3`
Commit anchor: `e439e0d`
Repo: <https://github.com/wit-oc/LiquidSniper>

## Purpose

This is the current proposal for what to work on next and in what order.

It supersedes older next-step framing that assumed the project was already ready to move mainly into calibration. The branch has made real progress, but the newest review cycle shows a remaining **contract / semantics** problem serious enough that more tuning would be premature.

## Current state: where we are

### What is already true
The V3 architecture is substantially real now:
- shadow-first migration posture exists
- schema-first zone contract exists
- selector separation exists (Daily / 4H / nearest-four)
- native structure candidates exist
- base/reaction/structure families can merge coherently
- role-aware nearest-four exists
- canonical family provenance survives into shadow outputs
- BTC/ETH and broader basket validation work has already run

### What is not yet true enough
The review / execution-facing semantics are still wrong in a way that can poison model interpretation.

We can still end up with surfaces that look like:
- `resistance` below current price
- `support` above current price

That means the system is still leaking **origin / formation kind** into **current execution-facing role**.

## Diagnosis

There are three layers of remaining problems.

### 1) Contract / semantics problem (most immediate)
We are still conflating:
- `origin_kind` / formation history
- current execution-facing role
- relative position to current price

That is the most immediate bug because it corrupts how humans read the outputs.

### 2) Review-surface separation problem
The diagnostic UI and summaries still mix or blur:
- baseline vs shadow
- raw candidates vs selected majors
- compact summary vs deeper shadow payloads
- origin kind vs current role

That means even correct backend improvements can still look wrong to the operator.

### 3) Remaining model-truth problem
After the semantic contract is fixed, there may still be true modeling work to do:
- structure-family truth may still need refinement
- Daily promotion may still need tuning once semantics are clean
- ATR / lifecycle refinement remains support work

But those should come **after** the semantic/contract cleanup.

## What is stale / superseded

### Historical inputs only
These are still useful history, but **not** the primary next-step guide now:
- `PHASE2_SR_V3_PEER_REVIEW_BUNDLE_2026-03-12.md`
- `PHASE2_SR_V3_PEER_REVIEW_BUNDLE_2026-03-14.md`

Why they are stale for planning:
- 2026-03-12 is pre-native-structure / pre-provenance-finalization
- 2026-03-14 still framed the decision as “are we ready for calibration mode?”
- later review and UI/backend inspection show the more immediate next issue is role semantics / surface truthfulness

### Still-current review input
This remains current and relevant:
- `PHASE2_SR_V3_ROLE_SEMANTICS_REVIEW_2026-03-14.md`

## Proposed order of work

### Phase A — fix the contract first
Add and fully surface explicit fields that separate historical formation from current meaning:
- `origin_kind`
- `current_role`
- `relative_position`

Rules for review/execution-facing surfaces:
- below current price => **support**
- above current price => **resistance**
- containing current price => **active band** / **containing zone**

Keep `origin_kind` as provenance / diagnostics, not the primary user-facing label.

### Phase B — fix analytics and UI separation
Make it impossible to confuse the following:
- baseline vs shadow
- raw candidate zones vs selected majors
- origin-kind view vs current-role view

Specific UI/render changes:
- group Daily majors into:
  - below current price
  - contains current price
  - above current price
- stop rendering only a flat top-4 majors slice as the main view
- make the primary visible labels use `current_role`, not origin kind

### Phase C — re-evaluate BTC / ETH after the semantic fix
Only after A + B:
- re-read BTC and ETH
- determine how much remaining weirdness was semantic pollution vs true model weakness

### Phase D — then decide if deeper structure-family work is still needed
If BTC still looks materially wrong after A + B:
- continue with a targeted structure-family truth pass
- then revisit Daily promotion logic if necessary

### Phase E — only then resume calibration/tuning
Examples:
- Daily promotion refinements
- core-band / breadth refinement
- ATR / lifecycle refinement
- broader validation sweep refresh if necessary

## What we should not do next
Do **not** do these next:
- generic selector retuning
- blind weight nudging
- deeper ATR / lifecycle work first
- another broad validation sweep before the semantic fix
- another architecture rewrite without first fixing the role contract

## Relevant files for the next redesign pass

### Primary implementation files
- `docs/zone_schema_v2.md`
- `docs/selector_policy_v2.md`
- `liquidsniper/core/zone_engine_v3.py`
- `liquidsniper/core/pair_analytics.py`
- `liquidsniper/web/app.py`

### Current review inputs
- `IntradayTrading/spec/phases/PHASE2_SR_V3_ROLE_SEMANTICS_REVIEW_2026-03-14.md`
- `IntradayTrading/spec/phases/PHASE2_SR_V3_PEER_REVIEW_BUNDLE_2026-03-14.md` (historical checkpoint)
- `docs/phase2_zone_engine_v3_steering_packet.md`

### Optional evidence artifacts (if needed)
- `/data/artifacts/sr/shadow/v3/bootstrap_snapshot.json`
- `/data/artifacts/sr/shadow/v3/nearest_BTCUSDT.json`
- `/data/artifacts/sr/shadow/v3/nearest_ETHUSDT.json`

## Bottom line

The project is not back at square one.

The architecture is mostly real.
The next problem is narrower and more foundational:

> Fix the role-semantics contract first.
> Fix the review surfaces second.
> Then re-evaluate BTC/ETH.
> Then decide whether remaining issues are true model-truth problems or just newly visible calibration work.

That is the proposal I recommend using as the current planning anchor.
