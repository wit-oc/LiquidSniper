# HTF Chop / SR Retest / Swing Bias Tuning Spec (V1)

Status: Draft for review  
Owner: Redact  
Author: Wit  
Date: 2026-02-23

## 1) Why this spec exists

Recent live paper runs show the candle-close timeout problem is largely improved in the latest window, but trade flow is still bottlenecked by gate concentration:

- Primary blocker now: `HTF_CHOP_BLOCKED` (dominant first-fail)
- Secondary blocker: `RETEST_REQUIRED`
- Swing lane additionally blocked by `BIAS_NOT_PERMITTED`
- Execution count remains near/at zero in recent windows

This spec defines how to tune the system without introducing strategy drift.

---

## 2) Hard constraints (must remain true)

1. Keep paper-mode deterministic behavior and existing policy authority order.
2. Keep close-confirm backoff as exactly `+5s, +10s, +15s` (30s cap).
3. No endpoint switching/failover logic.
4. No prior-candle fallback variable injection.
5. Keep risk/execution boundary hard gates non-bypassable.
6. Keep profile-parameterized tuning (`scalp` / `intraday` / `swing`), no hardcoded one-size-fits-all thresholds.

---

## 3) Tuning goals

### G1 — Reduce gate monopoly
Shift first-fail distribution away from near-monopoly by HTF chop while preserving quality controls.

### G2 — Restore healthy funnel progression
Allow more candidates to reach later gates where appropriate (without relaxing everything at once).

### G3 — Keep quality high
No overtrading spike, no risk-policy bypass, no synthetic data regressions.

---

## 4) Proposed design changes (algorithm-level)

## A) HTF chop calibration (highest priority)

### A.1 Problem with current behavior
Current chop proxy can saturate near 100, causing near-universal hard fails. We need a bounded, more separable chop signal.

### A.2 New chop calculation (deterministic)
For HTF lookback `N` bars:

1. **True-range sum**
- `TR_sum = Σ TR_i` for `i in [t-N+1, t]`

2. **Range span**
- `span = HH_N - LL_N`

3. **Choppiness Index (CI)** (bounded 0..100)
- `CI = 100 * log10(TR_sum / max(span, eps)) / log10(N)`

4. **Efficiency Ratio (ER)** trend penalty (bounded 0..100 choppy scale)
- `ER = abs(C_t - C_{t-N}) / max(Σ abs(C_i - C_{i-1}), eps)`
- `ER_chop = 100 * (1 - ER)`

5. **Final normalized chop score**
- `HTF_CHOP_NORM = clamp(w_ci * CI + w_er * ER_chop, 0, 100)`
- Proposed starting weights: `w_ci = 0.7`, `w_er = 0.3`

Rationale:
- `CI` captures range-bound vs directional market structure.
- `ER_chop` penalizes noisy non-directional movement.
- Weighted blend improves lane separability without randomness.

### A.3 Hard/soft gate behavior (replace single hard threshold)
Use lane-profiled two-threshold model:
- `soft_max`: no hard block, but apply score penalty if exceeded.
- `hard_max`: hard fail (`HTF_CHOP_BLOCKED`) if exceeded.

Penalty in soft zone:
- `p = (HTF_CHOP_NORM - soft_max) / max(hard_max - soft_max, eps)`
- `htf_chop_penalty = p * htf_chop_penalty_max`
- Confluence adjusted: `score_total_adj = score_total_raw - htf_chop_penalty`

Interpretation:
- Extreme chop still hard-blocked (authority preserved).
- Marginal chop degrades score instead of monopolizing first-fail.

### A.4 Required diagnostics
Persist both old/new components for comparability:
- `htf_chop_ci`, `htf_chop_er`, `htf_chop_norm`
- `htf_chop_soft_max`, `htf_chop_hard_max`
- `htf_chop_penalty`, `score_total_raw`, `score_total_adj`
- existing: `htf_chop_mode`, `htf_chop_threshold_effective`

---

## B) SR retest tuning (after chop)

### B.1 Keep strict retest path as primary
Strict pass remains unchanged:
- first retest eligible
- directional consistency intact
- `distance_bps <= sr_retest_bps_max`

### B.2 Add bounded near-retest path (scalp/intraday only)
Near-retest can pass **only** when all are true:
1. lane in `{scalp, intraday}`
2. breakout regime is true
3. within breakout window `k` candles (default `k=1`)
4. `sr_retest_bps_max < distance_bps <= sr_retest_near_bps_max`

Near-retest adds explicit penalty:
- `sr_penalty = ((distance_bps - sr_retest_bps_max) / max(sr_retest_near_bps_max - sr_retest_bps_max, eps)) * sr_near_penalty_max`
- `score_total_adj = score_total_adj - sr_penalty`

If outside near band: hard fail `RETEST_REQUIRED`.

Rationale:
- preserves SR discipline
- permits early breakout participation in a tightly bounded way
- keeps `swing` strict in V1

---

## C) Swing bias audit and refinement

### C.1 Add bias-confidence decomposition
For swing, compute and persist component votes:
- `v_htf`: sign(EMA20_HTF - EMA50_HTF)
- `v_itf`: sign(EMA20_ITF - EMA50_ITF)
- `v_structure`: sign(BOS/CHoCH direction)
- `v_sr_context`: sign(entry vs nearest HTF zone polarity)

Composite confidence:
- `bias_conf = 0.45*v_htf + 0.30*v_itf + 0.15*v_structure + 0.10*v_sr_context`
- `|bias_conf| < swing_bias_neutral_band` => `BIAS_NOT_PERMITTED`
- else direction = sign(`bias_conf`)

Default neutral band proposal: `0.55` (strict).

### C.2 Why this helps
- Replaces opaque all-or-nothing rejects with explainable weighted vote.
- Keeps HTF authority highest (`0.45` largest weight).
- Lets us distinguish “true no-trade regime” from derivation artifacts.

---

## D) Confluence score integrity

Confluence minimum remains **6.0**.
All new soft-path allowances are score-penalized, not free passes.
That keeps quality filter intact while reducing brittle gate monopoly.

---

## 5) Rollout plan (safe sequencing)

1. **Phase 1:** HTF chop diagnostics + normalized metric + threshold recalibration
2. **Phase 2:** SR near-retest + breakout-conditioned relaxation (scalp/intraday)
3. **Phase 3:** Swing bias audit + optional corrective patch
4. **Phase 4:** 6h / 24h before-after comparison and go/no-go

No multi-knob changes in the same validation slice unless explicitly approved.

---

## 6) Success criteria

### Core
- `HTF_CHOP_BLOCKED` first-fail share decreases materially from current dominant level
- Non-zero executed trades in representative windows
- No risk-boundary regressions

### Quality guards
- No overtrading spike (lane-level trade frequency remains within policy)
- No increase in `DATA_UNAVAILABLE` due to tuning work
- No regression in candle-close confirmation logic

### Observability
- All new diagnostic fields visible in run artifacts and debug API payloads

---

## 7) Task breakdown (review-first, no runner yet)

## T0 — Baseline pack (pre-change)
- Pull 6h/24h snapshots for first-fail, stacked reasons, funnel transitions.
- Deliverable: `artifacts/paper_mvp/tuning_baseline_<date>.json`

## T1 — HTF chop diagnostics schema
- Add raw components to artifact payload + debug API mapping.
- Tests: payload contract test updates.

## T2 — HTF chop normalization function
- Implement normalized formula with deterministic bounds.
- Tests: unit tests for monotonicity and bounds.

## T3 — Profile threshold recalibration support
- Add/validate lane-specific config params for chop thresholds.
- Tests: policy parsing + defaults.

## T4 — HTF chop gate wiring update
- Use normalized metric for gate decision while preserving raw diagnostics.
- Tests: gate pass/fail expectations by lane.

## T5 — SR near-retest parameterization
- Add lane parameters and policy parsing.
- Tests: policy + gate behavior.

## T6 — Breakout-conditioned SR relaxation (C/I only)
- Apply conditional, bounded relax mode.
- Tests: activation/non-activation, swing unaffected.

## T7 — Swing bias diagnostics
- Add bias-input traces to artifacts.
- Tests: payload + debug API fields.

## T8 — Swing bias audit report
- Analyze whether bias rejects are expected vs artifact.
- Deliverable: `docs/internal/SWING_BIAS_AUDIT_<date>.md`

## T9 — (Conditional) swing bias corrective patch
- Only if T8 indicates artifact.
- Tests: swing-specific regression coverage.

## T10 — End-to-end regression pack
- Run targeted daemon/policy/debug tests + CI-equivalent subset.

## T11 — Comparative tuning report
- 6h/24h delta report with pass-through and quality checks.
- Deliverable: `artifacts/paper_mvp/tuning_delta_<date>.json`

## T12 — PR packaging
- Open PR with phased commits + before/after evidence and rollback notes.

---

## 8) Initial parameter proposal (review together)

## A) HTF chop thresholds + penalties
- `scalp`: `soft_max=72`, `hard_max=86`, `htf_chop_penalty_max=1.2`
- `intraday`: `soft_max=68`, `hard_max=82`, `htf_chop_penalty_max=1.0`
- `swing`: `soft_max=62`, `hard_max=76`, `htf_chop_penalty_max=0.8`

Why:
- Scalp tolerates more micro-noise but pays larger penalty in soft zone.
- Swing remains strictest hard-cap from a regime perspective.

## B) SR retest near-band defaults
- `scalp`: `sr_retest_bps_max=20`, `sr_retest_near_bps_max=35`, `sr_near_penalty_max=0.8`
- `intraday`: `sr_retest_bps_max=18`, `sr_retest_near_bps_max=30`, `sr_near_penalty_max=0.7`
- `swing`: unchanged strict (no near-band in V1)

## C) Breakout relaxation window
- Default: `1` candle (`breakout_relax_window_candles=1`)
- Optional escalation to `2` only if first run still over-blocks and quality holds.

## D) Swing bias neutrality
- `swing_bias_neutral_band=0.55` (strict)
- If swing lane remains fully blocked after decomposition audit, test `0.50` in a short A/B window.

## E) Target pass-through bands (phase checkpoints)
- `scalp`: 10-25%
- `intraday`: 25-45%
- `swing`: 10-20%

These are checkpoint ranges, not guarantees, and must be validated against quality guards.

---

## 9) Out of scope for this spec

- Live trading enablement
- New data vendors/endpoints
- Re-architecting execution boundary or risk model
- Multi-factor optimizer/auto-tuner
