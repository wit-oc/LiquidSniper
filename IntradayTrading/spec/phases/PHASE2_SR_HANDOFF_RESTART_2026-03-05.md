# Phase 2 S/R — Handoff + Restart Plan (2026-03-05)

## Why this handoff exists
We iterated through V1→V5.1 with many diagnostics and partial refactors. We are now hitting diminishing returns from tuning and need a clean next-session restart plan.

---

## Current objective (unchanged)
Build a deterministic S/R watcher that:
1. identifies meaningful reaction anchors,
2. clusters them into robust zones,
3. avoids noise without missing important pivot/reaction structure,
4. works consistently across timeframes (especially 1D/1W and lower TF behavior drift).

---

## Canonical repo + branch
- Repo: `../workspace/LiquidSniper`
- Branch: `intraday-trading-migration-20260302`

---

## Latest scripts (in `IntradayTrading/pine/`)
- `PHASE2A_SR_WATCHER_V4_REACTION_ANCHOR_AUDIT.pine`
- `PHASE2A_SR_WATCHER_V5_TIME_NORMALIZED_REACTION_MODEL.pine`
- `PHASE2A_SR_WATCHER_V5_1_TIME_NORMALIZED_REACTION_MODEL.pine` ← latest experimental path
- Import docs:
  - `README_PHASE2A_TV_IMPORT_V4.md`
  - `README_PHASE2A_TV_IMPORT_V5.md`
  - `README_PHASE2A_TV_IMPORT_V5_1.md`

---

## What is working now
1. **Diagnostics are much better than early versions**
   - Dot overlays visible and color-coded.
   - Failed-anchor diagnostics available.
   - Date-window filtering for dot diagnostics exists.
   - Single-candle inspect mode exists (per-side fail code + move/persist/score).

2. **Time-normalized windows in V5/V5.1**
   - Move/no-revisit/persistence windows are hour-based, reducing TF bias.

3. **Side-aware anti-spam gap logic exists**
   - Same-side and opposite-side gap separated.

4. **Candidate bypass lane exists in V5.1**
   - Intended to admit “small candle, strong follow-through” anchors.

---

## What is NOT working well yet
1. **Still missing some intuitively important anchors/zones**
   - Especially specific candles in manually highlighted regions.

2. **Tuning often shifts failure mode rather than solving it**
   - Example: lowering score increased zone count/noise rather than recovering the intended anchor cleanly.

3. **Candidate gate remains dominant blocker in multiple cases**
   - Inspect output example from session:
     - `Inspect R/S code: FAIL_C / FAIL_C`
     - `Inspect R/S mATR|p|S: 1.64|0|2.29 / 2.11|3|3.75`
   - Interpretation: candle failed candidate prefilter before becoming anchor despite non-trivial excursion behavior.

4. **Zone quality depends heavily on upstream anchor quality**
   - If anchors are off, cluster knobs become compensatory/fragile.

---

## Forensic note: orange-circle candle (key issue)
Observed behavior:
- Candle expected by user to be reaction-significant did not produce an accepted anchor.
- Diagnostics showed `FAIL_C` (candidate gate) on both sides in at least one focused run.

Implication:
- Current model still over-relies on candidate prefilter in edge cases where “setup candle looks small but expedition is strong.”

---

## Root cause summary
We have mixed models coexisting:
- Structural prefilter (local-extrema + bar-range),
- Excursion scoring,
- Retention pruning,
- Cluster promotion.

When these disagree, we get opaque behavior and iterative “whack-a-mole” tuning.

---

## Recommended restart path (next session)
### Phase A — Anchor engine reset (anchor-only mode)
Goal: trust anchor acceptance logic before any zone clustering.

Implement/lock:
1. **Raw candidate stream** (all-bars optional, local-extrema optional) with explicit reason codes.
2. **Excursion-first acceptance** as primary gate (time-normalized), with candidate prefilter as optional modifier (not hard blocker unless configured).
3. **Deterministic score + rank retention** (top-% / max-kept) with clear debug distribution.
4. **Mandatory per-candle inspect report** including full gate booleans:
   - `C/M/R/P/S/G` as true/false, not only final fail code.

Acceptance for Phase A:
- Given an inspected candle, reason chain is unambiguous.
- Changing one knob predictably changes one failure bucket.

### Phase B — Cluster engine reset (zones from accepted anchors only)
1. Build clusters from accepted anchors only.
2. Use robust envelope controls (core-vs-outlier policy explicitly configurable).
3. Keep `minClusterPoints`, `minClusterScore`, `clusterTolPct` as only primary cluster knobs.

Acceptance for Phase B:
- Zone formation changes are explainable by cluster stats (points/score/width).

### Phase C — Cross-timeframe sanity harness
Run fixed scenarios on BTC 1D/1W and one lower TF.
Track:
- anchor pass ratio,
- missing expected anchors,
- zone count stability,
- nearest-target distance for known reference levels.

---

## Guardrails for next session
- Avoid adding new knobs until a failure bucket is clearly identified.
- Keep **anchor-first** and **zone-second** separation strict.
- Prefer reason-code clarity over visual tuning.
- If a candle is contested, use inspect diagnostics first, then tune.

---

## Suggested immediate next-session starting config (for reproducibility)
Use this as first test baseline on BTCUSD 1D with date window around the contested area:
- Mode: `DIAG`
- Anchor candidate mode: `local-extrema`
- Candidate len: `3`
- Min candidate range ATR: `1.0`
- Move/noRevisit/persist hours: `96 / 96 / 72`
- Min anchor move ATR: `2.75`
- Min persistence bars: `5`
- Persist threshold ATR: `0.60`
- Score gate: ON, min score `~6.0`
- Side-aware gaps: same `120h`, opposite `24h`
- Date-window diagnostics: ON
- Show failed anchors: ON
- Inspect one candle: ON (for contested candle)

---

## If V5.1 still fails after clean replay
Stop tuning and start `V6` as a clean anchor-first implementation (single-file prototype), then port only proven components forward.

---

## Requested from next session owner
1. Reproduce one contested candle with inspect diagnostics enabled.
2. Capture exact gate booleans for that candle.
3. Decide whether candidate gate can veto excursion (policy decision).
4. Implement policy consistently and rerun baseline.
