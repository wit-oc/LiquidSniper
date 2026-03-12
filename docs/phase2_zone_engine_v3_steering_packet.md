# Phase 2 Zone Engine V3 Steering Packet

Status: draft for shadow-mode architecture pass  
Branch: `phase2-zone-engine-v3`

## 1) Verdict

**The current system is evolvable, but only if we stop treating the reaction-family output as the final doctrine.**

That is the key call.

What exists today is not worthless and does not need a throw-it-away rewrite. It already gives us:
- a working reaction-family baseline via `sr_engine_v2`
- a merged-zone concept in `zone_engine_v3`
- nearest-four execution payload production already wired into the analytics surface
- early family arbitration and diagnostics scaffolding

But it is also **misaligned enough that we should not keep tuning it as if it were the target architecture**. Right now, `zone_engine_v3` still leans heavily on the reaction-family engine for both structure-like and reaction candidates. That makes it useful as a bridge, not as the doctrinal endpoint.

So the ruling is:
- **Continue from here** rather than restart from zero.
- **Do not do another blind tuning pass.**
- **Reframe the current implementation as a shadow-mode bridge architecture** whose job is to preserve execution continuity while we correct the generation/selection doctrine.

## 2) Problem statement

The current path over-represents zones that score well under reaction-family logic, then tries to recover structure semantics after the fact.

That creates three risks:
1. **Structure drift** — Daily/4H levels can look important because they scored well, not because they are the right structural anchors.
2. **Selector leakage** — generation and selection concerns are still too coupled, so policy changes risk becoming disguised tuning.
3. **Observability ambiguity** — a kept zone may look authoritative without clearly showing whether it came from structure, base, reaction, or a merged cluster.

The corrective direction is:
- treat **structure**, **base**, and **reaction** as separate source families
- merge them under a single zone schema with explicit provenance
- make selection policy distinct from generation policy
- preserve the current nearest-four execution payload shape during migration

## 3) Target doctrine

Zone Engine V3 should be understood as a **family-fusion engine** with a strict separation of concerns:

### 3.1 Generation layer
Generate candidate zones independently from:
- **structure family** — higher-timeframe structural pivots / bounds
- **base family** — shelves, compression bases, launch platforms
- **reaction family** — historically reactive touch/retest behavior

Generation answers:
- what candidate exists?
- what are its bounds?
- what family produced it?
- what lifecycle evidence supports it?

### 3.2 Arbitration layer
Arbitration clusters overlapping/nearby candidates and chooses a canonical merged zone while retaining diagnostics for:
- merged members
- family count
- winner reason
- score components
- family confluence bonus

Arbitration answers:
- which nearby candidates are the same tradeable idea?
- which member becomes the canonical live zone?
- what evidence explains the win?

### 3.3 Selection layer
Selection is policy, not generation.

Selection answers:
- which zones count as Daily majors?
- which count as 4H operational levels?
- which four levels become the execution payload nearest to price?

This layer must be allowed to evolve without mutating family-generation rules.

## 4) Shadow-mode migration stance

The migration must be **shadow-first, no default-path switch**.

That means:
- current execution remains anchored to the existing working path
- V3 shadow output is computed in parallel
- V3 output is compared, logged, and reviewed before any authority expansion
- the current nearest-four execution payload concept is preserved throughout

### 4.1 Non-goals for this phase
This phase is **not**:
- a parameter sweep
- a scoring retune disguised as architecture work
- a default execution-path cutover
- a symbol-specific exception pass

### 4.2 Goals for this phase
This phase **is**:
- architecture clarification
- schema clarification
- selector-policy clarification
- scaffold/document seam creation
- shadow-mode observability definition

## 5) Canonical architectural decision

**Decision:** keep the current reaction-family path as the baseline source of continuity, but explicitly demote it to one source family inside a broader V3 zone model.

Implications:
- `sr_engine_v2` remains a valid source family, not the whole theory of zones.
- `zone_engine_v3` becomes the orchestration layer that can host structure/base/reaction families together.
- daily-major, 4H-operational, and nearest-four execution outputs must be derived from the same canonical merged-zone set, but under different selector policies.

## 6) Source-family doctrine

### 6.1 Structure family
Purpose:
- provide durable high-timeframe market map anchors
- define the broader support/resistance geometry
- resist local overreaction to touch-count noise

Expected behavior:
- sparse
- high-confidence
- especially important for Daily major selection

### 6.2 Base family
Purpose:
- capture compressed shelves / launch pads / distribution shelves that matter tactically
- bridge the gap between broad structure and reaction-only evidence

Expected behavior:
- narrower than many structural zones
- tactically useful for operational framing
- often meaningful near execution without becoming pure proximity noise

### 6.3 Reaction family
Purpose:
- retain the proven current strength of the system: historically respected zones with observable reaction evidence
- continue serving as the continuity baseline during shadow mode

Expected behavior:
- best current baseline for practical relevance
- should influence but not monopolize final merged-zone selection

## 7) Selection doctrine by surface

### 7.1 Daily major surface
Daily majors should answer: **what are the sparse structural anchors that matter for the current macro map?**

Daily major policy should prefer:
- Daily-derived structural bounds
- strong family agreement
- stability over proximity
- anti-clutter behavior

It should explicitly avoid becoming “top N highest-scoring zones regardless of doctrinal role.”

### 7.2 4H operational surface
Operational zones should answer: **what levels are tactically relevant for intraday planning without collapsing into noise?**

Operational policy should prefer:
- 4H relevance
- narrower tactical usefulness
- clear provenance and lifecycle state
- enough density to guide operations, but still bounded

### 7.3 Nearest-four execution surface
Nearest-four should answer: **what are the closest actionable support/resistance references around price right now?**

Critical rule:
- **preserve the existing nearest-four execution payload concept**
- migration may improve candidate quality and provenance, but it must not break the shape/conceptual contract relied on downstream

## 8) Shadow-mode observability requirements

Shadow mode is only useful if it makes disagreements visible.

Every shadow artifact should make it easy to inspect:
- candidate family
- source family / source version
- merged family count
- merged member ids
- lifecycle state
- why the selector kept or dropped a zone
- what nearest-four payload would have been produced
- where V3 differs from the current baseline

Required comparison lenses:
1. **Baseline vs V3 nearest-four**
2. **Daily major sparsity / drift**
3. **4H operational usefulness**
4. **Family arbitration disputes**
5. **MAP-safe vs LIVE-safe field separation**

## 9) Migration phases

### Phase A — spec + scaffold
Deliver:
- steering packet
- schema doc
- selector policy doc
- acceptance test doc
- scaffold seams

Exit condition:
- architecture is explicit enough that future work is implementation, not theory-churn

### Phase B — shadow generation
Deliver:
- V3 candidate generation under the canonical schema
- merged-zone diagnostics
- selector outputs for Daily / 4H / nearest-four
- no cutover

Exit condition:
- shadow artifacts can be reviewed deterministically

### Phase C — shadow comparison
Deliver:
- pair/sample comparison between baseline and V3 outputs
- documented disagreements
- evidence of whether doctrine improves map quality without harming execution continuity

Exit condition:
- enough evidence to decide whether to promote any V3 selectors

### Phase D — controlled promotion
Deliver:
- opt-in surface-level promotion only after evidence
- preserve rollback path
- keep comparison artifacts until confidence is established

Exit condition:
- one surface promoted with explicit evidence, not vibes

## 10) Risks

### Risk 1: reaction-family dominance survives the rewrite
If structure and base are only thin wrappers around reaction-family output, the architecture will look cleaner while remaining conceptually wrong.

Mitigation:
- define family provenance explicitly in schema
- require selector policies to acknowledge family role, not just composite score

### Risk 2: selector work turns into hidden tuning
If daily-major or operational policy is expressed only as weights, the team will slip back into score-chasing.

Mitigation:
- separate policy docs from generator docs
- define class-of-behavior requirements, not just thresholds

### Risk 3: nearest-four payload regression
If migration alters the downstream payload contract, execution consumers may break or silently degrade.

Mitigation:
- preserve current nearest-four concept and shape
- stage cutover only after payload parity review

### Risk 4: shadow mode without useful evidence
Parallel generation is noise if outputs cannot be compared clearly.

Mitigation:
- require comparison artifacts and arbitration diagnostics from day one

## 11) Immediate implementation guidance

For the remaining Phase 2 tasks, proceed in this order:
1. define the canonical V3 zone schema
2. define selector policy by output surface
3. define acceptance tests that check doctrine rather than symbol-specific hacks
4. keep code scaffold thin and reversible
5. avoid any tuning pass until the packet is complete

## 12) Summary

The practical recommendation is simple:

**Do not scrap the current path, and do not keep tuning it blindly.**

Instead:
- keep the current reaction-family path as continuity baseline
- define V3 as a shadow-mode family-fusion architecture
- preserve nearest-four execution behavior
- make Daily major / 4H operational / execution selection policies explicit and separate
- use shadow-mode observability to decide whether the doctrine is actually better before promoting anything

## 13) T6 closure — minimal shadow-mode wiring plan (no default-path switch)

This section closes the final architecture task by specifying the first wiring tranche.

### 13.1 Bootstrap wiring (`liquidsniper/ops/sr_bootstrap.py`)

Add a shadow feature gate:
- CLI/config switch: `shadow_mode_v3` (`--shadow-v3` / `--no-shadow-v3`)
- default: `false` (baseline path remains canonical)

When `shadow_mode_v3=true`:
1. keep existing baseline generation/persistence fully unchanged
2. build a parallel V3 shadow snapshot from structure/base/reaction candidate families
3. write shadow artifacts to a separate namespace:
   - `sr/shadow/v3/bootstrap_snapshot.json`
   - `sr/shadow/v3/nearest_<SYMBOL>.json`
   - `sr/shadow/v3/run_status.json`
4. include baseline-to-shadow linkage fields:
   - baseline run id
   - shadow run id/status
   - shadow snapshot path in baseline run status

When `shadow_mode_v3=false`:
- baseline behavior is identical to current path
- no shadow artifact writes occur

### 13.2 App wiring (`liquidsniper/web/app.py`)

Add shadow readers and comparison surface without replacing current views:
- load baseline snapshot/status as today
- additionally load shadow snapshot/status if present
- render baseline UI unchanged first
- render a distinct shadow comparison block (nearest ladder + majors/operational summary + payload expander)

Critical guardrail:
- baseline nearest-four remains the primary execution-facing payload in this tranche
- shadow UI is observability-only

### 13.3 Observability contract for tranche 1

Each shadow run should make these comparisons inspectable per symbol:
- baseline zone count vs shadow zone count
- baseline nearest-four vs shadow nearest-four
- shadow daily-major surface and 4H operational surface
- family/arbitration diagnostics carried by shadow zones

### 13.4 Explicit non-goals for tranche 1

- no default-path cutover
- no score-weight tuning campaign
- no symbol-specific overrides
- no MAP-only fields leaking into LIVE gating

### 13.5 Promotion gate after wiring

Do not promote V3 to default until all are true:
1. acceptance tests pass (`docs/daily_major_acceptance_tests.md`)
2. nearest-four continuity is preserved for execution consumers
3. selector disagreements are explainable from family diagnostics
4. BTC diagnostic and ETH blind-check both meet doctrine without pair-specific hacks
