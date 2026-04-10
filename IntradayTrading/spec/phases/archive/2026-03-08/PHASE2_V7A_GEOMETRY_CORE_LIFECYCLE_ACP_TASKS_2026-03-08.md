# Phase 2 — V7A Geometry/Core/Lifecycle ACP Tasks (2026-03-08)

Status: APPROVED FOR EXECUTION  
Scope: Phase-2 WATCH/INVALID/EXPIRED support context only (POI+Fib context).  
Out of scope: trigger entries, execution/risk lifecycle, Python port, 4H/15m trigger logic.

## Threading + control context
- Control thread (operator): current Phase-2 thread.
- Upstream control reminder for this workstream: `<#1477100380662927520>`.
- This ACP run should execute in its own thread-bound session and post checkpoints there.

## Hard guardrails (non-negotiable)
1. Repo lock: `/Users/wit/.openclaw/workspace/LiquidSniper` only.
2. Branch lock: `phase2-v7-zone-first-20260307` only.
3. File scope primary: `IntradayTrading/pine/PHASE2A_SR_WATCHER_V7A_ZONE_FIRST.pine`.
4. Allowed docs scope: `IntradayTrading/spec/phases/*`.
5. No dependency installs.
6. No destructive resets/cleanups.
7. Do not touch sibling repos (especially `aws-agentic-platform-standard`).

## Model + start proof
- Use ACP model: `gpt-5.4`.
- First message in execution thread must include:
  - effective model string,
  - repo path,
  - branch,
  - first task starting.

---

## Task sequence

## T1 — Dual geometry split per zone (envelope + core)
### Required changes
- Keep structural envelope fields:
  - `zStructTop`, `zStructBot`, `zStructMid`
- Add tradeable core fields:
  - `zCoreTop`, `zCoreBot`, `zCoreMid`, `zCoreWidthPct`, `zCoreScore`
- Core derivation must use strongest inner evidence subset (not full union width).
- Classing must evaluate tradeable width on **core** width, not structural envelope width.
- Render envelope and core separately (envelope lighter, core stronger).

### Acceptance
- Structural zone may remain broad while core is materially narrower and independently testable.

---

## T2 — Family-local ranking + dedupe before cap
### Required changes
- Replace first-come cap filling with per-family candidate ranking.
- Per-family dedupe keys:
  - price proximity,
  - time proximity,
  - directional equivalence.
- Keep best-N per family after ranking, then merge.

### Acceptance
- Family caps are less frequently hard-pegged on normal lookbacks.
- Duplicate shelf/flip/launch clutter reduced without obvious coverage collapse.

### Gate G1 (required post)
Post:
- commit hash,
- files changed,
- one-line pass/fail against T1/T2 acceptance.

---

## T3 — Merge segmentation hardening
### Required changes
- Add merge segmentation constraints:
  - regime boundary protection (e.g., `regimeId`/equivalent),
  - max event-time distance (`maxBarsBetweenEvents`) for merge eligibility.
- Keep event-time ATR tolerance and span caps.

### Acceptance
- Historical stale-cycle events do not over-merge into active-cycle zones.

---

## T4 — First-retest lifecycle semantics
### Required changes
- Add lifecycle fields:
  - `hasFirstRetestOccurred`
  - `firstRetestReactionATR`
  - `firstRetestFailed`
  - `timesCleanlyRejected`
  - `timesClosedThrough`
- State set (or equivalent semantics):
  - `virgin`, `first_touch_ready`, `tested_once`, `spent`, `broken`
- Tradeable classing must include first-retest/lifecycle quality.

### Acceptance
- Tradeable gating is behavior-driven, not proxy-only retest counts.

### Gate G2 (required post)
Post:
- commit hash,
- files changed,
- one-line pass/fail against T3/T4 acceptance.

---

## T5 — Base shelf refinement (dedupe + adjacency)
### Required changes
- Add shelf dedupe and shelf adjacency merge logic.
- Increase edge-touch quality weighting and breakout conviction contribution.

### Acceptance
- Fewer repeated adjacent shelves representing same structure; shelf quality ranking improves.

---

## T6 — Debug contract upgrade for cert visibility
### Required changes
Add/refresh debug rows for:
1. family saturation before/after dedupe,
2. envelope vs core width telemetry,
3. lifecycle state distribution,
4. first-retest outcome telemetry,
5. merge reject reasons (segmentation/span/overlap).

### Acceptance
- Debug panel supports deterministic operator cert decisions without code dive.

### Gate G3 (required post)
Post:
- commit hash,
- files changed,
- one-line pass/fail against T5/T6 acceptance.

---

## T7 — Handoff + operator runbook update
### Required output
Create/update phase doc under `IntradayTrading/spec/phases/` with:
- what changed,
- known risks,
- exact operator runbook for BTC/ETH 1D validation,
- before/after metric deltas,
- recommended defaults,
- follow-up tasks for V7B (4H companion map) only after this passes.

### Acceptance
- Operator can run cert from handoff doc without reading full git diff.

---

## Commit cadence
- Use prefix: `phase2(v7a): ...`
- Prefer one commit per task or tightly coupled pair.

## Blocker protocol
If blocked, respond exactly:
`BLOCKED: <specific blocker> | NEXT: <smallest unblocked step>`
