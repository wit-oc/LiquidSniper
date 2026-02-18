# Automated Trading Agent Alignment (v1)

Status: Draft (2026-02-18)  
Scope: Align the Blofin + on-chain automated trading proposal with current LiquidSniper docs, task tracker, and near-term implementation sequence.

---

## 1) What this alignment does

This document translates the completed multi-pass proposal (`initiatives/artifacts/blofin-onchain-trading-bot-proposal-v1.md`) into LiquidSniper-native action items.

It answers:
1. How this design maps to existing LiquidSniper docs/tasks.
2. How the emerging lecture-based strategy becomes the core decision foundation.
3. Whether this should stay inside LiquidSniper or fork into a separate execution core.
4. What adversarial risks remain after adding HTF-anchored strategy assumptions.

---

## 2) Alignment to current repo docs

### Already aligned

- `docs/HYBRID_CONFLUENCE_PIPELINE_SPEC.md`
  - Deterministic-first confluence pipeline and staged decisioning.
- `docs/TRADING_STRATEGY_RUNBOOK_V1.md`
  - Current confluence gate policy (primary + secondary tiers).
- `docs/PHASE2_CONFLUENCE_RESEARCH_SPEC.md`
  - Deterministic feature/label research plan.
- `docs/OPENCLAW_ORCHESTRATION.md`
  - External rulebook + env-only secret model.
- `docs/GO_NO_GO_CHECKLIST.md`
  - Simulation -> guarded pilot gate framework.

### Gaps this alignment closes

1. No canonical **HTF-anchor contract** for strategy portability across time horizons.
2. No explicit mapping from strategy playbook buckets -> current confluence scoring objects.
3. No implementation-level boundary decision for “integrated in LiquidSniper” vs “separate execution core.”
4. No adversarial test checklist attached directly to strategy-timeframe assumptions.

---

## 3) Alignment to current tasks and open items

### Existing open items to keep

From `TASK_BOARD.md` / `WORK_ITEMS.md`:
- Validate end-to-end pipeline wiring (ingestor -> confluence -> analysis -> diagnostic UI)
- Docker/compose verification and simulation gate hardening
- Go/no-go promotion discipline

These remain mandatory and are not replaced by strategy work.

### New strategy-alignment workstream (added as Tasks 14–18)

- **Task 14:** HTF-anchor rulebook contract
- **Task 15:** Strategy score engine alignment (playbook buckets -> decision payload)
- **Task 16:** Dependency threading + non-bypass boundaries
- **Task 17:** Two-pass adversarial validation harness
- **Task 18:** Packaging boundary decision (integrated module vs separate service)

---

## 4) Strategy foundation update (HTF-anchor model)

## 4.1 Assumption check: “time is relative”

**Verdict: conditionally true.**

The structure/confluence framework is fractal enough to re-anchor from:
- `HTF=1D` (swing/intraday bias), to
- `HTF=1H` (scalp bias),

**if** the model preserves timeframe ratios and cost/microstructure constraints.

### Required constraints

1. Keep hierarchical spacing (example: HTF:ITF:LTF ≈ 1:4:16 or 1:6:24).
2. Recompute edge/cost assumptions per anchor profile (fees/funding/gas/slippage are not scale-invariant).
3. Tighten risk caps for smaller anchors (higher noise, higher execution drag).
4. Disable cross-profile parameter reuse unless replay parity and guardrails pass.

## 4.2 Canonical anchor profiles (v1)

- **Profile S (Swing):** HTF `1D`, ITF `4H`, LTF trigger `1H/15m`
- **Profile I (Intraday):** HTF `4H`, ITF `1H`, LTF trigger `15m/5m`
- **Profile C (Scalp):** HTF `1H`, ITF `15m`, LTF trigger `5m/1m`

The decision engine must carry `anchor_profile_id` and `htf_anchor_tf` in every analysis run.

## 4.3 Core strategy invariants (must hold across profiles)

1. Primary structural gates remain mandatory:
   - S/R first retest
   - BoS/CHoCH structural alignment
2. Secondary confluences are confidence boosters, not thesis replacements.
3. No trade when regime permissions fail (or unresolved contradiction state).
4. Risk policy remains final authority.

---

## 5) LiquidSniper dependency threading

## 5.1 Reuse dependencies (recommended)

Use existing LiquidSniper modules as scaffolding:
- `liquidsniper/core/replay_harness.py`
- `liquidsniper/core/analysis_engine.py`
- `liquidsniper/core/simulation_mode.py`
- `liquidsniper/core/orchestration.py`
- Diagnostic UI + artifact links for explainability

## 5.2 Non-bypass rule

Any strategy module (including lecture-derived rulebook logic) is advisory until approved by:
1. deterministic rulebook contract,
2. risk/policy gate,
3. audit/replay contract.

No direct adapter execution path may bypass risk decisions.

## 5.3 Order-book alignment question

If the strategy thesis does not require order-book alignment, treat order-book features as **optional quality modifiers**, not hard blockers.

This avoids forcing strategy invalidation when order-book data is unavailable while still allowing future quality lift experiments.

---

## 6) Integrated vs forked architecture decision

## Recommendation (current):

**Do not fork yet.** Keep this inside LiquidSniper as a bounded module set through constrained-live design work.

### Why

- Existing pipeline/replay/orchestration foundations are already in place.
- Faster iteration while strategy rules are still settling.
- Lower integration cost for diagnostics and policy evidence packs.

### Fork triggers (future)

Fork into a separate execution service only when one or more become true:
1. signer/key isolation requires independent deployment boundary,
2. release cadence diverges sharply from analytics pipeline,
3. regulatory/compliance controls require separate artifact and access domains,
4. dependency graph growth materially harms deterministic replay reliability.

Until then: **single repo, strict module boundaries, policy non-bypass enforcement.**

---

## 7) Two-pass adversarial review (new positions)

## Pass 1 — Strategy/microstructure adversarial review

### Findings

1. **Fractal overconfidence risk:** HTF portability can hide execution-drag asymmetry when moving from 1D to 1H anchors.
2. **Cost non-stationarity risk:** scalp anchor profiles are more sensitive to funding spikes, spread drift, and on-chain inclusion variance.
3. **Trigger inflation risk:** lower-timeframe trigger abundance can overfit confidence tiers and erode expectancy.

### Required responses

- Anchor-profile-specific viability thresholds and risk caps.
- Separate cost calibration by profile and path.
- Minimum sample-size and drift guards before enabling profile promotion.

## Pass 2 — Systems/governance adversarial review

### Findings

1. **Boundary blur risk:** strategy docs can accidentally become execution authority without schema/policy controls.
2. **Dependency coupling risk:** over-reliance on one pipeline can obscure failure domains.
3. **Override drift risk:** manual interpretation creep can silently bypass deterministic controls.

### Required responses

- Schema-validated rulebook payload with version pinning.
- Explicit non-bypass contract between strategy scorer and execution adapters.
- Replay parity and reason-code audits as promotion blockers.

---

## 8) Immediate refinement checklist

1. Land Task 14 to formalize HTF-anchor and profile schema.
2. Land Task 15 to map strategy bucket scoring into canonical decision payloads.
3. Land Task 16 to document and enforce dependency boundaries.
4. Land Task 17 to codify adversarial validation as gate criteria.
5. Land Task 18 to make boundary decision explicit (with evidence) before live execution path expansion.

This keeps strategy-first iteration and risk-first operations coupled correctly, while avoiding premature architectural fragmentation.
