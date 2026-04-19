# Phase 2 S/R Architecture and Phase 1 Equivalence Audit

Date: 2026-04-14  
Status: code-anchored audit of the live branch  
Scope: `liquidsniper` V3 shadow S/R pipeline and the current Fib anchor path in `IntradayTrading`

## Executive summary

### 1) What the live S/R system actually is
The live V3 shadow S/R stack is a **three-family zone engine**:
- **structure family**: derives zones from Phase 1 market-structure events
- **base family**: derives zones from compressed shelves that break cleanly
- **reaction family**: derives zones from clustered pivots plus measured reaction behavior

Those families are then:
1. **merged/arbitrated** into shared zones,
2. **rescored** with lifecycle and confluence bias,
3. passed through **selector policy** that decides which zones become the operator-facing truth.

The operator-facing truth is therefore **not raw structure output** and not a simple pivot map. It is a **selected surface built on top of family-fusion zones**.

### 2) Where market structure matters
Market structure is upstream and real.
The structure family uses `run_phase1_htf_structure(...)` as its seed engine, then turns specific BoS/CHoCH + locked-swing events into structure candidates.

### 3) Is S/R using the same structure logic as Fib?
**Mostly yes at the engine family level, but not exactly.**

The SR structure family and the Fib Phase 1 contract path both use the same upstream callable family:
- `IntradayTrading/engine/htf_phase1.py::run_phase1_htf_structure(...)`

But they are **not byte-for-byte equivalent** in current branch behavior because:
- SR calls it with `break_min_frac_of_candle=0.20`
- Fib Phase 1 contract context calls it with `break_min_frac_of_candle=0.15`
- they also consume the outputs differently:
  - SR uses event + lock pairing to create zones
  - Fib uses regime direction + eligible swing pair selection to create anchor pairs

So the correct verdict is:
- **same structural engine family**
- **same overall doctrine**
- **not yet identical contract/configuration**
- **good unification candidate**

### 4) What should be unified
Unify the **upstream Phase 1 HTF structure adapter/contract**, not the downstream consumers.

That means one shared module should own:
- aggregation to target HTF
- Phase 1 parameters
- output contracts for `bars`, `events`, `swings`, current bias/confidence

Then:
- SR can keep building zones from event/lock structure seeds
- Fib can keep selecting anchor pairs from the same shared structure state

That removes duplicated structure calculation without incorrectly collapsing zones and Fib into one thing.

---

## Part I. Live S/R architecture

## A. Top-level workflow

The shadow bootstrap path in `liquidsniper/ops/sr_bootstrap.py` does this per symbol and timeframe:

1. load candles
2. generate three candidate families
   - `build_structure_candidates(...)`
   - `build_base_candidates(...)`
   - `build_reaction_candidates(...)`
3. merge nearby/overlapping family candidates with `merge_candidate_zones(...)`
4. rescore merged zones with `score_zone(...)`
5. select final surfaces
   - Daily: `select_daily_majors(...)`
   - 4H: `select_operational_zones(...)`
6. build the operator-facing authoritative view from those **selected** surfaces

That path is the live answer to “how are S/R levels calculated?”

---

## B. Candidate generation families

## B1. Structure family

The structure family is seeded by:
- `run_phase1_htf_structure(highs, lows, closes, left=2, right=2, n_init=min(25, len(candles)), break_min_frac_of_candle=0.20, choch_break_min_frac_of_candle=0.15, strict_gating=False, bos_require_fresh_cross=True, enable_continuation_break=True)`

### What Phase 1 emits
`run_phase1_htf_structure(...)` tracks:
- candidate swings
- validated swings
- protected high / protected low
- `bos_confirmed`
- `choch_detected`
- subsequent locked swing events:
  - `swing_low_locked`
  - `swing_high_locked`

### How SR turns that into zones
SR does **not** turn every protected level into a zone.
Instead it applies a seed policy:
- allowed seed sources: `bos_confirmed`, `choch_detected`
- allowed seed kinds: `bos_anchor`, `flip_anchor`
- it only accepts the matching locked swing within the next 3 follow-up events
- it rejects raw rolling protected-level spam

### Structure-family zone geometry
For each accepted seed:
- anchor candle is the locked swing candle
- `anchor_mid = seed.anchor_price`
- `anchor_span = anchor_high - anchor_low`
- `body_span = anchor_body_high - anchor_body_low`

Support zone:
- `zone_low = min(anchor_low, anchor_mid)`
- `zone_high = max(anchor_body_high, anchor_mid)`

Resistance zone:
- `zone_low = min(anchor_body_low, anchor_mid)`
- `zone_high = max(anchor_high, anchor_mid)`

Fallback padding if degenerate:
- `pad = max(atr_ref * 0.08, max(anchor_span, body_span, 1e-6) * 0.25)`
- `zone_low = anchor_mid - pad`
- `zone_high = anchor_mid + pad`

### Structure-family scoring math
Let:
- `break_distance_atr = abs(seed.break_price - anchor_mid) / atr_ref`
- `width_atr = zone_width / atr_ref`

Then:
- `structure_score = min(100, 58 + 18*min(break_distance_atr, 2.0) + 10*min(anchor_span/atr_ref, 1.5))`
- `efficiency_score = min(100, 52 + 22*min(break_distance_atr, 1.5) - 6*max(width_atr - 1.0, 0.0))`
- `carry_score = min(100, 48 + 10*min(body_span/zone_width, 1.0) + (8 if flip_anchor else 4))`
- `reaction_score = min(100, 50 + 16*min(break_distance_atr, 2.0))`
- `body_respect_score = min(100, 44 + 18*min(body_span/zone_width, 1.0))`

Hard filter:
- skip seed if `break_distance_atr < 0.05`

So structure-family zones are explicitly **price-move validated**, not just “there was a swing there.”

---

## B2. Base family

The base family looks for a compressed 5-candle shelf followed by a breakout.

### Qualification rules
Using:
- `window = 5`
- `breakout_lookahead = 3`
- `compression_max_atr = 1.10`
- `breakout_min_atr = 0.80`
- `breakout_close_min_atr = 0.35`
- `overlap_min_ratio = 0.45`
- `min_overlap_links = 2`
- `touch_tol = atr_ref * 0.10`

It requires:
1. shelf span is narrow enough: `span_atr <= 1.10`
2. adjacent candle overlap is meaningful at least twice
3. both upper and lower shelf edges are actually touched
4. breakout range and close exceed minimum ATR thresholds

### Base-family features
- `compression_bonus = max(0, 1 - min(span_atr / 1.10, 1))`
- `overlap_score = min(1, overlap_links / (window - 1))`
- `edge_score = min(1, edge_touch_total / (window + 1))`
- `battle_score = min(1, (edge_balance + overlap_links) / (window + 1))`

### Base-family scoring math
- `score = min(100, 28 + 24*breakout_atr + 18*close_breakout_atr + 14*overlap_score + 12*edge_score + 10*compression_bonus + 8*battle_score)`
- `reaction_score = min(100, 44 + 22*breakout_atr + 10*close_breakout_atr)`
- `reaction_efficiency_score = min(100, 42 + 24*close_breakout_atr + 12*overlap_score)`
- `carry_score = min(100, 34 + 7*edge_touch_total + 6*overlap_links)`
- `body_respect_score = min(100, 40 + 20*compression_bonus + 18*battle_score)`

This family is looking for **compression + contested shelf + decisive breakout**.

---

## B3. Reaction family

This is the existing `sr_engine_v2` logic reused as the reaction-family generator.

### Step 1: extract pivots
It finds support/resistance pivots from local highs/lows over a `k=3` window.

### Step 2: cluster pivots into raw zones
Pivots are sorted by price and clustered when:
- `abs(p.price - cluster_center) / atr_value <= eps`

Then zone bounds are built from pivot price quantiles:
- `low = q20(prices)`
- `high = q80(prices)`
- `mid = (low + high) / 2`
- `width = max(high - low, mid*pct_floor, atr*atr_floor_mult)`
- final zone = midpoint-centered interval with that width

### Step 3: measure touch/reaction behavior
For each intersecting candle:
- look ahead 3 candles for immediate reaction magnitude
- look ahead 7 candles for carry/follow-through
- classify `reject_up`, `reject_down`, or `flat`
- track whether touches are meaningful by ATR threshold

Key derived rates:
- `body_overlap_rate`
- `wick_only_rate`
- `close_inside_rate`
- `directional_close_rate`
- `counter_close_rate`

### Reaction-family carry and body-respect math
Let:
- `carry_ref = q80(carry_samples)`
- `adverse_ref = q80(adverse_samples)`
- `net_carry = max(0, carry_ref - 0.65*adverse_ref)`
- `carry_dominance = clamp01((carry_ref - adverse_ref)/carry_ref)` when `carry_ref > 0`

Then:
- `carry_score = clamp01(0.7*log_norm(net_carry, 8.0) + 0.3*carry_dominance) * 100`
- `body_respect_raw = 0.22 + 0.38*body_overlap_rate + 0.48*directional_close_rate - 0.42*close_inside_rate - 0.72*counter_close_rate - 0.22*wick_only_rate`
- `body_respect_score = clamp01(body_respect_raw) * 100`

### Reaction-family strength math
With:
- `touch_component = 18 * log_norm(meaningful_touch_count, 40)`
- `pivot_component = 15 * log_norm(pivot_count, 18)`
- `reaction_component = 30 * clamp01(max_reaction_atr / 2.5)`
- `carry_component = 9 * carry_norm`
- `body_component = 12 * body_norm`
- `efficiency_ratio = (0.8*max_reaction_atr + 0.2*(carry_norm*3.0)) / log1p(touch_load)`
- `reaction_efficiency = clamp01(efficiency_ratio / 0.95)`
- `efficiency_component = 16 * reaction_efficiency`
- retest bonus:
  - `+12` if first retest = `reject`
  - `+7` if first retest = `deviation`
- `spent_zone_penalty = 30 * touch_excess * (1 - (0.7*reaction_efficiency + 0.2*carry_norm + 0.1*body_norm))`
- `width_penalty = 12 * clamp01((zone_width_bps - 300)/220)`
- `chop_penalty = 12 * clamp01((55 - body_respect_score)/55)`

Then:
- `strength_raw = 14 + touch_component + pivot_component + reaction_component + carry_component + body_component + efficiency_component + retest_component - spent_zone_penalty - width_penalty - chop_penalty`
- `strength_score = clamp01(strength_raw / 100) * 100`
- `reaction_score = clamp01(max_reaction_atr / 3.0) * 100`
- `selection_score` initially starts as `strength_score`

So reaction-family zones are the “historically respected and behaviorally defended” branch.

---

## C. Merge and arbitration layer

After structure/base/reaction generation, V3 merges nearby compatible zones.

### Merge conditions
Two candidates are merged when:
- same symbol
- same timeframe
- compatible support/resistance kind
- and either:
  - intervals overlap, or
  - midpoints are within a merge tolerance

Merge tolerance is:
- `max(width, seed_width, atr_ref*0.35, seed_atr*0.35, abs(seed_mid)*0.0035)`

### Arbitration
Within a cluster, candidates are ranked by:
1. `selection_score` or `strength_score`
2. `reaction_efficiency_score`
3. `carry_score`

The winner becomes the representative zone, but the merged zone keeps:
- envelope bounds across candidates
- family provenance from all families
- arbitration diagnostics

### Confluence bonus
Merged zone gets:
- `family_bonus = 4 * max(0, family_count - 1)`
- `selection_score = max(candidate_base_scores) + family_bonus`

So multi-family corroboration is explicitly promoted.

---

## D. Post-merge scoring layer

Merged zones are rescored by `score_zone(...)`.

### Base score
- `base_score = 0.54*strength + 0.16*reaction + 0.16*efficiency + 0.10*carry`

### Width bonus
If ATR exists:
- `width_atr = zone_width / atr_ref`
- `width_bonus = clamp((1.2 - width_atr) * 4, -10, 8)`

So narrower-than-1.2 ATR zones get a reward, very wide zones get a penalty.

### Lifecycle bonus
Using `side_aware_interaction(...)`:
- `+4` if either side sees a `virgin` state
- `+2` if either side sees `first_touch`
- `-4` if either side sees `deep_test`
- `-10` if either side sees `broken`

### Family confluence bonus
- `family_bonus = 3 * max(0, family_count - 1)`

### Final V3 score
- `selection_score = base_score + width_bonus + lifecycle_bonus + family_bonus`

This is the main “bring a zone into focus” score **before** selector-specific policy.

---

## E. Selector policy, the real focus mechanism

The generators create possibilities. The selectors decide what becomes operator truth.

## E1. Daily majors selector

Daily majors do **not** use raw `selection_score` alone.
They apply a Daily-specific score with retest and provenance weighting.

### Daily retest weight
Let:
- `carry = carry_score / 100`
- `body = body_respect_score / 100`
- `close_through = counter_close_rate`
- `close_inside = close_inside_rate`

Base retest weight:
- `reject -> 1.00`
- `deviation -> 0.92`
- `accept -> 0.80` strict or `0.86` relaxed
- `none -> 0.82` strict or `0.88` relaxed
- other -> `0.84`

Dynamic adjustment:
- `dynamic = 0.05*carry + 0.04*body - 0.06*close_through - 0.03*close_inside`
- `retest_weight = clamp(base + dynamic, 0.6, 1.0)`

### Daily provenance weight
Daily majors slightly promote structural corroboration:
- `+0.06` if structure provenance exists
- `+0.02` per extra merged family, capped at `+0.04`
- `-0.06` if pure base-only shelf
- clamp to `[0.88, 1.12]`

### Daily major score
- `daily_selection_score = (strength * retest_weight * provenance_weight) + 0.08*reaction + 0.16*efficiency + 0.06*carry + 0.10*body_respect`

That is one of the most important formulas in the live system.

### Daily focus workflow
After scoring, Daily majors go through:
1. confirmed-only filter
2. minimum strength filter
3. local band representative selection
4. distance collapse
5. spatial diversity selection
6. operator-core refinement
7. pocket consolidation
8. current-regime coverage repair

### Macro vs core doctrine
This is critical:
- `zone_low/zone_high/zone_mid` = **macro coverage truth**
- `core_low/core_high/core_mid` = **display/operator core**

The selector now explicitly distinguishes:
- `_daily_macro_interval(...)` for coverage truth
- `_daily_display_interval(...)` for display narrowing

That means Daily coverage classification must be based on the **macro interval**, not the narrowed core.

### Pocket consolidation and demotion
Daily majors are grouped into macro pockets, then each pocket keeps one representative, while preserving:
- `daily_pocket_member_ids`
- `daily_pocket_demoted_ids`
- `daily_pocket_member_count`

So “which zones lost and why” is part of the review contract.

### Current-regime coverage repair
This is the closeout doctrine that makes Daily selection price-relative.
It uses `reference_price` and macro intervals to repair gaps.

There are two explicit repair cases:
1. **daily current-regime coverage anchor**
2. **daily intermediate upside coverage anchor**

That means the final Daily map is not only “highest scoring zones.”
It is “highest scoring zones that still preserve truthful macro coverage around current price and major upside gap structure.”

---

## E2. 4H operational selector

Operational 4H zones use a different focus doctrine.

### Provenance-weighted representative choice
Operational provenance weight:
- `+0.06` if structure present
- `+0.02` if reaction present
- `+0.02` per extra merged family beyond one, capped overall at `+0.05`
- `-0.05` if pure base-only
- clamp to `[0.88, 1.15]`

Representative ranking uses:
1. `selection_score * provenance_weight`
2. merge family count
3. reaction efficiency
4. touch count
5. narrower width
6. raw base score

### Same-side neighborhood logic
Zones of the same role are grouped if they overlap enough or are close enough in edge/mid distance.
One provenance-weighted representative survives each same-side local neighborhood.

That is why the operational surface is less about macro pocket coverage and more about **usable local representatives**.

---

## F. Authoritative surface and UI truth

The 8501 authoritative/shadow UI is a **consumer** of selected surfaces.
It is not an independent zone engine.

`sr_bootstrap.py` builds:
- a shadow snapshot from generated/merged/scored/selected zones
- an `authoritative_view` from the selected Daily and 4H surfaces

`pair_analytics.py::summarize_zone_for_pair_analytics(...)` then carries forward:
- macro bounds
- core bounds
- display-width-floor diagnostics
- family provenance
- arbitration diagnostics
- Daily pocket metadata
- local cluster metadata

So the UI/operator contract is downstream of the selection pipeline, not a separate truth source.

---

## Part II. Market structure equivalence audit

## A. The actual upstream SR structure callable

The SR structure family uses:
- `IntradayTrading/engine/htf_phase1.py::run_phase1_htf_structure(...)`

That engine:
- detects swings with lookahead-safe pivot logic (`left=2`, `right=2`)
- tracks validated highs/lows
- maintains protected high/protected low
- emits `bos_confirmed` and `choch_detected`
- emits locked swing events immediately after those transitions
- keeps regime direction and confidence as state

This is the real upstream market-structure engine for SR structure-family candidates.

---

## B. What the current Fib path uses

The Fib anchor path in `IntradayTrading/engine/runner.py` now defaults to:
- `fib_use_phase1_contract_anchors = True`

When enabled, it builds HTF contexts with:
- `build_phase1_contract_context_for_timeframe(...)`

That function also calls:
- `run_phase1_htf_structure(...)`

Then anchor selection uses:
- current Phase 1 regime direction/confidence from `phase1_bars`
- latest eligible swing pair from the Phase 1 `swings` log

So the current Fib contract path is **already Phase 1-backed**, not just raw pivot-pair guessing.

---

## C. Exact overlap between SR and Fib

They match on:
- same upstream function: `run_phase1_htf_structure(...)`
- same pivot/swing window: `left=2`, `right=2`
- same `n_init=25`
- same `choch_break_min_frac_of_candle=0.15`
- same `strict_gating=False`
- same `bos_require_fresh_cross=True`
- same `enable_continuation_break=True`
- same general doctrine: structure must be point-in-time, replay-safe, event-driven

This is strong evidence that they are intended to live under one structure contract.

---

## D. Exact differences between SR and Fib

### Difference 1: BoS conviction threshold
SR structure seeds use:
- `break_min_frac_of_candle = 0.20`

Fib Phase 1 contract context uses:
- `break_min_frac_of_candle = 0.15`

That means marginal BoS confirmation cases can diverge.

### Difference 2: downstream consumer logic
SR uses Phase 1 outputs to build zones from:
- event type
- locked anchor side
- anchor candle geometry
- break distance

Fib uses Phase 1 outputs to build anchor pairs from:
- current regime direction
- latest eligible swing pair in that direction

So they share upstream structure truth, but they **materialize different downstream artifacts**.

### Difference 3: fallback behavior
Fib still has a debug fallback path based on `detect_pivots(...)` / pivot-pair anchor selection.
That is a backup path, not the primary contract when `fib_use_phase1_contract_anchors=True`.

---

## E. What about `IntradayTrading/engine/structure.py`?

This file is a separate, simpler pivot/regime projector:
- detect pivots
- infer bullish/bearish bias from HH/HL vs LH/LL
- project regime with CHoCH-candidate then BoS-confirmed flip semantics

It is **not** the primary structure engine used by SR structure-family generation.
And it is **not** the primary path of the current Fib contract anchors when the Phase 1 flag is on.

So if the question is:
- “Is SR using the same logic as `structure.py`?”
  - **No, not as the main upstream engine.**
- “Is SR using the same Phase 1 structure engine family that Fib now uses?”
  - **Yes, with parameter/config drift.**

---

## Final verdict

### Verdict in one line
SR structure-family generation and Fib contract anchors are **structurally aligned siblings built on the same Phase 1 engine**, but they are **not yet identical implementations**.

### The precise answer
- **Equivalent at the architectural/doctrinal layer:** yes
- **Equivalent at the exact configuration layer:** no
- **Equivalent at the downstream artifact layer:** no, by design
- **Ready for upstream unification:** yes

---

## Recommended unification plan

## 1. Create one shared Phase 1 HTF adapter
A shared module should own:
- aggregation to target timeframe
- Phase 1 parameter profile
- returned `bars`, `events`, `swings`, and current regime state

## 2. Stop calling `run_phase1_htf_structure(...)` directly from multiple places
Both SR and Fib should call the shared adapter.

## 3. Decide one canonical BoS conviction threshold
Current drift:
- SR: `0.20`
- Fib contract context: `0.15`

Either:
- standardize to one value, or
- make the difference explicit as named profiles if the divergence is intentional

But do not leave it as silent drift.

## 4. Keep downstream consumers separate
Do **not** force one artifact shape.
The correct shape is:
- shared structure contract upstream
- SR zone derivation downstream
- Fib anchor selection downstream

## 5. Keep pivot fallback explicit and non-canonical
`detect_pivots(...)` fallback is useful for debugging, but it should remain visibly secondary to the Phase 1 contract path.

---

## Bottom line

The live branch is already much closer to Option C than older memory might suggest.

The true architecture is:
- **Phase 1 structure truth upstream**
- **family-fusion zone generation in the middle**
- **selector policy deciding operator truth downstream**

And the clean next step is not “rewrite everything.”
It is:
- **unify the Phase 1 structure adapter/config once**,
- then let SR and Fib keep consuming that shared truth for their different purposes.
