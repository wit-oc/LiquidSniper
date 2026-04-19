# Phase 2 — V7A Hybrid Rebalance ACP Task Packet (2026-03-08)

Status: APPROVED FOR EXECUTION  
Owner intent: Redact  
Scope lock: Phase 2 watch-engine support/resistance context only (`WATCH/INVALID/EXPIRED` support); **no trigger-entry logic**.

## Global execution guardrails (non-negotiable)

1. Repo/path scope:
   - Work only in `LiquidSniper/`.
   - Primary code file: `IntradayTrading/pine/PHASE2A_SR_WATCHER_V7A_ZONE_FIRST.pine`.
   - Allowed doc updates under `IntradayTrading/spec/phases/`.
2. Branch lock:
   - Must stay on `phase2-v7-zone-first-20260307`.
   - Do not create/switch to unrelated branches.
3. Out-of-scope repositories:
   - Do **not** read/write `aws-agentic-platform-standard/` or other sibling projects.
4. Safety:
   - No dependency installs.
   - No destructive cleanups/reset on unrelated dirty files.
5. Status proof policy:
   - Every task update must include concrete evidence (file path + changed section + commit hash when committed).

---

## Task sequence

## T1 — Split event budgets by channel (V7A.1)

### Required changes
- Replace shared `maxEvents` behavior with family caps:
  - `maxStructEvents`
  - `maxBaseEvents`
  - `maxFoxianEvents`
- Keep optional hard ceiling `maxEventsTotal` to avoid runaway memory.
- Add per-family limit enforcement in event insertion path.

### Acceptance
- Debug shows all three families with independent counts and caps.
- No default state where structure monopolizes total event budget.

---

## T2 — Structure noise control / parity posture (V7A.2)

### Required changes
- Default `structureEmitProtected = false`.
- Ensure primary structure seeds are:
  - `STRUCT_BOS_ANCHOR`
  - `STRUCT_FLIP_ANCHOR`
- If protected events enabled manually, keep low weight and low priority.

### Acceptance
- Structure channel still emits meaningful seeds while event volume is reduced.
- Debug confirms lower structure flood relative to current scaffold baseline.

### Gate checkpoint G1
- Stop and post concise status + evidence before continuing to T3.

---

## T3 — Rewrite base detector to shelf logic (V7A.3)

### Required changes
- Replace compression-only proxy with shelf detector using:
  - overlap persistence
  - edge touch counts
  - breakout confirmation
- Add base diagnostics fields:
  - `baseOverlapCount`
  - `baseTouchCountTop`
  - `baseTouchCountBot`
  - `baseCompressionScore`
  - `baseBreakoutScore`
- Emit both:
  - `BASE_SHELF`
  - `BASE_BREAKOUT`

### Acceptance
- Base channel produces non-zero events on BTC/ETH 1D windows under default settings.

---

## T4 — Move Foxian toward zone-level evidence (V7A.4)

### Required changes
- Keep Foxian event stream capped but secondary.
- Add post-provisional zone scoring inputs from Foxian quality:
  - launch quality
  - persistence proxy
  - break-beyond-range quality
- Avoid relying on impulse candles as primary geometry creators.

### Acceptance
- Foxian contributes to zone score even when direct Foxian event count is low.

### Gate checkpoint G2
- Stop and post concise status + evidence before continuing to T5.

---

## T5 — Merge governance + event-time ATR refs (V7A.5)

### Required changes
- Store `eAtrRef` per event.
- Merge logic uses event-time ATR references (not only current ATR).
- Add merge span controls:
  - `zoneMergeMaxSpanPct`
  - `zoneMergeMaxSpanATR`
  - optional overlap-required merges for structure/base

### Acceptance
- Reduced oversized-zone growth before final class gate.

---

## T6 — Real retest/lifecycle implementation (V7A.6)

### Required changes
- Implement post-birth revisit counting into `zRetestCount`.
- Drive zone state from interactions:
  - `fresh`
  - `active`
  - `weakening`
  - `broken`
- Ensure tradeable class uses real lifecycle signals.

### Acceptance
- Retest metrics non-zero where appropriate; tradeable class no longer placeholder behavior.

### Gate checkpoint G3
- Stop and post concise status + evidence before continuing to T7.

---

## T7 — Debug contract refresh + deterministic evidence

### Required changes
- Ensure compact debug panel includes:
  1. events generated (family + subtype)
  2. provisional zones (count + avg span + span rejects)
  3. zone classes
  4. tradeable reject reasons
  5. retest telemetry summary
  6. nearest visible zone
  7. config digest

### Acceptance
- Debug is screenshot-friendly and sufficient to evaluate hybrid balance.

---

## T8 — Final cert handoff pack

### Required output
- Update or create handoff note under `IntradayTrading/spec/phases/` summarizing:
  - what changed
  - remaining gaps/risks
  - exact next validation steps for Redact on chart
- Include final evidence list:
  - files changed
  - commit hashes
  - before/after debug deltas

### Acceptance
- Handoff is actionable without reading full git diff.

---

## Commit cadence

- Preferred: 1 commit per task (or tightly coupled pair), with message prefix:
  - `phase2(v7a): ...`
- At each gate (G1/G2/G3), include:
  - current head commit
  - changed files list
  - one-line pass/fail versus gate criteria

---

## Blocker contract

If blocked, respond with:

`BLOCKED: <specific blocker> | NEXT: <smallest unblocked step>`

Do not pivot to unrelated repo/workstream.
