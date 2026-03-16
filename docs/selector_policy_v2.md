# Selector Policy V2

Status: draft for Phase 2 shadow-mode migration  
Branch: `phase2-zone-engine-v3`

## 1) Purpose

Selector Policy V2 defines how the canonical Zone Schema V2 map is filtered into three distinct output surfaces:
- **Daily major**
- **4H operational**
- **nearest-four execution**

Its job is to keep **selection policy** separate from **generation policy**.
That separation is the main architectural correction.

Generation decides what valid candidates exist.
Arbitration decides which overlapping candidates represent the same tradeable idea.
Selection decides which canonical zones matter for a specific surface.

If those concerns bleed together, the system falls back into hidden tuning.
This document is meant to prevent that.

## 2) Non-negotiable policy boundaries

### 2.1 Selection is downstream of canonical zone generation

Selectors must operate on the canonical merged-zone set produced by Zone Engine V3.
They must not:
- invent family-specific generation shortcuts inside the selector
- silently modify zone bounds
- backdoor symbol-specific exceptions
- treat score rank alone as doctrine

### 2.2 Different surfaces answer different questions

The three surfaces are not interchangeable.

They answer different questions:
- **Daily major:** what sparse structural anchors define the current higher-timeframe map?
- **4H operational:** what tactically relevant zones matter for planning and context?
- **nearest-four execution:** what are the closest usable S/R references around price right now?

A zone being strong on one surface does not automatically qualify it for the others.

### 2.3 Preserve nearest-four continuity

The current nearest-four execution payload concept is preserved.
Phase 2 may improve candidate quality, provenance, and diagnostics, but it must not redefine the downstream conceptual contract.

## 3) Selector input contract

Each selector should receive:
- canonical merged zones under Zone Schema V2
- explicit timeframe context
- current reference price
- optional selector-safe diagnostics from arbitration

Minimum fields relied on by selectors:
- `zone_id`
- `symbol`
- `tf`
- `zone_kind`
- `status`
- `zone_low`
- `zone_high`
- `zone_mid`
- `candidate_family`
- `candidate_sources`
- `merge_family_count`
- `selection_score` or equivalent selector-ready rank fields
- lifecycle state fields when present

Selectors may read diagnostics, but they must emit compact keep/drop reasons instead of depending on bulky diagnostics downstream.

## 4) Common eligibility gate

Before any surface-specific ranking, apply a common eligibility gate.

A zone is eligible for selection only if:
- `status` is compatible with live/shadow consideration (`confirmed` by default)
- bounds are numerically coherent
- provenance is explicit enough to explain why the zone exists
- the zone is not archived-only
- the zone belongs to the selector's timeframe scope or has an approved cross-timeframe role

Default exclusions:
- malformed bounds
- missing zone kind
- unresolved arbitration outcome
- invalidated zones
- purely diagnostic shadow artifacts that were never promoted into the canonical merged set

## 5) Surface policy: Daily major

### 5.1 Question answered

Daily major selection answers:
**what are the sparse, durable higher-timeframe anchors that matter for the current map?**

### 5.2 Primary preferences

Daily major should prefer:
- `1D` structural relevance first
- structure-family candidates or family-fused zones with strong structural participation
- wider, more durable envelopes over narrow tactical bands
- zones that remain meaningful even when price is not immediately nearby
- anti-clutter behavior

### 5.3 Secondary preferences

Daily major may reward:
- multi-family confluence when structure is still present
- clear lifecycle integrity
- high-confidence arbitration wins
- broad map usefulness across the surrounding regime

### 5.4 Explicit anti-goals

Daily major must not degrade into:
- “top N highest score zones”
- proximity chasing
- reaction-only dominance unless there is no better structural alternative
- dense laddering that obscures the map

### 5.5 Expected output shape

Daily majors should be:
- sparse
- stable across nearby candles unless real structure changes
- explainable as macro anchors
- suitable for human map review and higher-timeframe context

## 6) Surface policy: 4H operational

### 6.1 Question answered

4H operational selection answers:
**what zones are tactically useful for planning and intraday orientation without collapsing into noise?**

### 6.2 Primary preferences

4H operational should prefer:
- `4H` relevance first
- tactically useful bounds that a trader/operator would plausibly reference in session planning
- a mix of structural, base, and reaction sources when they improve map usefulness
- zones with clearer operational specificity than Daily majors

### 6.3 Secondary preferences

4H operational may reward:
- narrow-but-credible base zones
- reaction zones with strong respect history
- family confluence that makes a level more actionable
- lifecycle states that clearly describe whether the zone is fresh, retested, or degraded

### 6.4 Explicit anti-goals

4H operational must not become:
- a clone of Daily major
- a nearest-price dump
- an overcrowded set of minor levels
- a hidden tuning surface that compensates for weak generation

### 6.5 Expected output shape

4H operational output should be:
- denser than Daily major
- materially more selective than the full candidate map
- operationally readable
- suitable for analyst review without requiring forensic diagnostics

## 7) Surface policy: nearest-four execution

### 7.1 Question answered

Nearest-four selection answers:
**what are the closest actionable support/resistance references around current price right now?**

### 7.2 Primary preferences

Nearest-four should prefer:
- proximity around the current reference price
- one coherent set of nearby support/resistance references suitable for the existing execution payload concept
- zones that remain doctrinally valid after arbitration, not merely numerically close
- bounds that can be exported as a compact LIVE-safe payload

### 7.3 Secondary preferences

Nearest-four may reward:
- tighter operational relevance
- clearer side-of-price classification
- family confluence when it improves trust without bloating payloads
- stable, reversible tie-breaks that preserve downstream continuity

### 7.4 Explicit anti-goals

Nearest-four must not become:
- a stealth cutover to a new payload contract
- a score-only selector detached from proximity
- a dense neighborhood map beyond the existing nearest-four concept
- a place where MAP-safe diagnostic richness leaks into LIVE-safe execution payloads

### 7.5 Contract continuity rule

During shadow mode:
- the existing nearest-four payload concept remains the reference contract
- V3 may attach richer MAP-safe comparison records outside the LIVE-safe payload
- any future cutover requires explicit parity review, not optimistic assumption

## 8) Timeframe-role separation

Timeframe is part of doctrinal role, not just metadata.

### 8.0 Origin role vs current role separation

Selectors must treat these as distinct concepts:
- `origin_kind` / `zone_kind`: provenance-side doctrine from generation/arbitration
- `relative_position`: where price sits versus the zone right now
- `current_role`: execution/review-facing interpretation at the current price

Required review semantics for Phase 2:
- zones **below** price surface as `current_role=support`
- zones **above** price surface as `current_role=resistance`
- zones **containing** price surface as `current_role=containing`

Guardrail:
Selectors and review surfaces must not relabel provenance to make the current map look cleaner.
A zone can originate as `resistance` and later function as current support after price acceptance above it. That is a feature of the model, not a contradiction to hide.

Default role split:
- **Daily major:** primarily `1D`
- **4H operational:** primarily `4H`
- **nearest-four execution:** primarily current execution framing around price, typically sourced from the operational/canonical set

Cross-timeframe use is allowed only when it remains explainable.
Example: a Daily structural zone may appear in operational context if it is genuinely the nearest relevant level, but it should still carry its higher-timeframe identity.

## 9) Family-role separation

Families should influence selection differently by surface.

Default stance:
- **structure** is privileged on Daily major
- **base** becomes more important on 4H operational
- **reaction** preserves continuity and remains influential on operational/execution surfaces
- **family fusion** is often strongest when arbitration shows a single tradeable idea supported by multiple families

Critical guardrail:
No selector may assume reaction-family output is the whole doctrine.
Reaction is a source family, not the constitution.

## 10) Keep/drop trace requirements

Each selector should record compact trace fields on kept and reviewed zones:
- `selector_surface`
- `selector_status`
- `selector_reason`
- `selector_rank`

Reason strings should be short but concrete.
Examples:
- `kept: daily structural anchor with multi-family confirmation`
- `dropped: tactically valid but too dense for daily-major surface`
- `kept: nearest support with stable live-safe export`

The goal is auditability without payload sprawl.

## 11) Determinism requirements

Selector behavior should be deterministic for the same input set.

That means:
- stable sorting rules
- explicit tie-break behavior
- no hidden symbol-specific overrides
- no discretionary per-run pruning

If two zones are near-equal, tie-breaks should prefer the rule that best preserves doctrinal role and shadow-review consistency, not whatever happens to look better in one sample.

## 12) Shadow-mode review expectations

Shadow mode should make selector disagreements legible.

Each review surface should be able to answer:
- what did baseline nearest-four keep?
- what would V3 nearest-four keep?
- did Daily major become cleaner or noisier?
- did 4H operational become more useful or more cluttered?
- which family-arbitration decisions caused the difference?

Required comparison lenses:
1. Daily major sparsity and anchor quality
2. 4H operational usefulness and density
3. nearest-four contract continuity and drift
4. source-family participation in kept zones
5. selector keep/drop rationale

## 13) What this policy deliberately does not decide

This document does not lock:
- score formulas
- numeric thresholds
- candidate generation rules
- exact arbitration math
- promotion/cutover timing

Those belong elsewhere.
This document defines **behavioral doctrine** and **surface separation**, not the full implementation.

## 14) Phase 2 implementation guidance

For the current branch, the practical implementation stance is:
- keep generator/scaffold work reversible
- preserve current nearest-four execution behavior as the continuity baseline
- make Daily major, 4H operational, and nearest-four selectors explicitly separate in code and docs
- prefer selector reasons and reviewability over premature score-tuning
- defer tuning passes until the architecture packet is complete

## 15) Summary

Selector Policy V2 is the rule that stops Zone Engine V3 from collapsing back into reaction-score tuning.

The core doctrine is:
- one canonical merged-zone map
- separate selectors for separate jobs
- Daily major favors sparse structure
- 4H operational favors tactical readability
- nearest-four preserves current execution continuity
- shadow mode exists to compare surfaces clearly before any promotion