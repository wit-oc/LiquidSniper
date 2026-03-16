# Phase 2 S/R Operator Guide — 2026-03-16

## Purpose

This guide translates the current Phase 2 / V3 language into plain trading terms and explains:

1. what each layer of the system is actually doing,
2. which outputs are authoritative vs diagnostic,
3. how to validate 1D and 4H levels against a chart,
4. what is currently a UI problem versus a real model problem.

This is an operator-facing guide, not a design-spec replacement.

---

## First: the short truth

We are **not** dealing with a UI-only issue.

We are dealing with **two separate things at once**:

### A. Surface / interpretation issue
The UI has been mixing:
- baseline vs shadow
- raw vs selected
- origin kind vs current role

That has made the page harder to interpret than it should be.

### B. Real model-truth issue
Even after semantics were improved, the latest trace work says the remaining BTC/ETH problems are mostly at the **selection stage**:
- BTC sparse upside Daily majors
- ETH missing next resistance

So:
- **not just UI**, and
- **not pure architecture either**.

We now mostly need:
1. better operator surfaces for validation, and
2. targeted selection-truth work after the surfaces are clear.

---

## Glossary: what the project terms actually mean

### 1) Baseline vs Shadow

#### Baseline
The older, currently-live/legacy path.
Think:
- the incumbent map
- the current DB-driven SR path
- the thing we preserve while experimenting

#### Shadow
The newer V3 path under evaluation.
Think:
- the candidate replacement model
- the architecture we are trying to validate
- the thing we compare against baseline before any cutover

**Operator meaning:**
If you are trying to decide whether the new logic is sane, shadow is the important review surface.

---

### 2) Raw candidates
Potential levels/zones before heavier selection.

Trading translation:
- these are the engine saying “I think these zones might matter”
- not all of them are supposed to reach the final map

Raw candidates are useful for debugging why a final level is missing.
They are **not** the main operator-facing truth surface.

---

### 3) Merged candidates / arbitration
The step where nearby/overlapping evidence families are fused.

Trading translation:
- if structure, reaction, and shelf/base evidence all point to roughly the same area,
  we do not want three duplicate zones cluttering the chart
- we want one zone with combined evidence

This is the “fuse overlapping ideas into one tradable region” stage.

---

### 4) Selected majors
This is the final **1D macro map**.

Trading translation:
- the important higher-timeframe zones
- the top-down context levels
- the map you compare to a Daily chart

This should be:
- sparse
- meaningful
- not cluttered
- not hyper-local execution noise

---

### 5) Operational surface
This is the final **4H context/execution map**.

Trading translation:
- the closer-in levels
- the levels you would actually expect to matter for current price navigation
- more detailed than 1D, but not micro-noise

This is the thing you compare to your 4H chart.

---

### 6) Nearest / next ladder
This is the execution-oriented summary:
- nearest support
- next support
- nearest resistance
- next resistance

Trading translation:
- “what matters first from here?”

This is a summary layer, not the full map.
It should not be used by itself to judge whether the full 1D/4H level map is correct.

---

### 7) Structure family
Zones/anchors derived from market structure.

Trading translation:
- BoS anchors
- flip anchors
- higher-timeframe structure zones

This is not supposed to be just pivot clustering with a nicer name.
It is meant to reflect actual structural logic.

---

### 8) Reaction family
Zones justified by repeated reaction behavior.

Trading translation:
- repeated touches
- carry
- body respect
- reaction quality
- retest-ish behavior

This is closer to classic “price clearly reacts here” reasoning.

---

### 9) Base / shelf family
Zones justified by compression / shelf / battle-range logic.

Trading translation:
- shelf
- battle range
- compression before displacement
- range edge behavior

This is the family most likely to overproduce if not controlled.

---

### 10) Origin kind
How the zone was formed historically.

Examples:
- support-born
- resistance-born
- mixed
- flip-derived

**Important:**
This is **not** always the same as what the zone means now.

---

### 11) Current role
What the zone means **right now relative to current price**.

For operator/review surfaces this should be interpreted simply:
- below price => support
- above price => resistance
- containing price => active / containing band

This is the field you should care about most when validating the level map.

---

### 12) Relative position
Where the zone sits relative to current price.

Human interpretation should be:
- below price
- contains price
- above price

If the internal code uses a more technical/indirect convention, the operator-facing surface should still translate it back into the above three human buckets.

---

### 13) Selector doctrine / selector-stage truth
This phrase has been too abstract.

What it really means:

> Once candidates already exist, are we choosing the right final levels to keep?

Trading translation:
- if the engine *found* a good 1D resistance but it disappears from the final map,
  that is a selection-stage problem
- if ETH should clearly have a next resistance and it vanishes after ranking/capping,
  that is a selection-stage problem

So “Selector Doctrine Tranche” basically means:
- investigate/fix how final levels are chosen,
- not how raw zones are first generated.

---

### 14) Model-truth tranche
Also abstract.

What it means in plain English:

> Figure out whether the model is actually discovering the right levels, and if not, exactly where the truth is getting lost.

That usually means tracing:
- raw candidates
- merged candidates
- selected majors
- nearest ladder

and finding where the good level disappeared.

---

## What is authoritative right now?

If your goal is:
> “Show me the actual levels I should compare against my chart”

then here is the recommended hierarchy.

### Authoritative for 1D validation
Use:
- **Selected Daily majors from the shadow path**
- grouped by:
  - below current price
  - contains current price
  - above current price
- sorted **lowest to highest** inside each group

This is the thing you should compare against a Daily chart.

### Authoritative for 4H validation
Use:
- **Selected 4H operational surface from the shadow path**
- grouped by:
  - below current price
  - contains current price
  - above current price
- sorted **lowest to highest** inside each group

This is the thing you should compare against a 4H chart.

### Useful, but secondary
- nearest / next ladder
- provenance details
- raw candidate tables
- merge diagnostics

These are excellent debugging surfaces.
They are **not** the first thing you should use to judge whether the map itself is good.

---

## What operator view do we actually need?

The best operator-validation view is not the current mixed page.

We need a dedicated **Authoritative Levels View** with these sections:

# 1D Authoritative Levels
## Below current price (support)
- sorted lowest -> highest

## Contains current price (active band)
- sorted lowest -> highest

## Above current price (resistance)
- sorted lowest -> highest

# 4H Authoritative Levels
## Below current price (support)
- sorted lowest -> highest

## Contains current price (active band)
- sorted lowest -> highest

## Above current price (resistance)
- sorted lowest -> highest

For each level, show compact fields only:
- bounds
- midpoint
- current_role
- timeframe
- candidate_families
- selection_score
- origin_kind (secondary, muted)

Optional expandable details:
- family_provenance
- merge diagnostics
- generator/source versions

That should be either:
- a dedicated page, or
- a dedicated tab, or
- a mode toggle in the current review UI

But it should be clearly separate from the mixed diagnostic/debug surface.

---

## Recommended validation workflow

If you want to validate whether the algorithmic levels make sense against your chart, use this flow:

### For Daily
1. open the **1D Authoritative Levels** list
2. look only at selected Daily majors
3. compare them lowest -> highest against your Daily chart
4. ask:
   - are these meaningful macro reaction zones?
   - are obvious shelves missing?
   - are nonsense shelves present?

### For 4H
1. open the **4H Authoritative Levels** list
2. compare selected 4H operational levels lowest -> highest against your 4H chart
3. ask:
   - do these feel like the actual nearby navigation levels?
   - do the supports below and resistances above make practical sense?

### Only after that, use diagnostics
If something looks wrong:
- inspect nearest/next ladder
- inspect raw candidates
- inspect merged candidates
- inspect provenance

That keeps operator review clean.

---

## What is likely happening right now

### Not just UI-only
We do still have a real model-truth issue.

Latest internal conclusion:
- BTC sparse upside Daily majors
- ETH missing next resistance

look mostly like **selection-stage truth issues**, not primary candidate-generation failures.

### But UI/representation is still making review harder than it should be
So we should not pretend the page is already giving you the best operator view.

The practical reality is:
- the backend has improved a lot
- the debug UI is useful
- but the system still needs a **clean authoritative-levels view** for human chart validation

---

## Recommended next order of work

### Next
1. Build the **Authoritative Levels View**
   - 1D and 4H separated
   - grouped by below / contains / above
   - sorted lowest -> highest
   - current_role as the primary label

### After that
2. Use that view to validate BTC and ETH against charts
3. Then continue the selection-truth work with much clearer operator feedback

### Not next
- generic weight tuning
- broad calibration before the authoritative view exists
- more architecture invention

---

## Bottom line

If your goal is:
> “I want to quickly affirm the data on Daily and 4H against my chart”

then the right answer is:

> We need a dedicated, authoritative level view from the shadow path,
> split by timeframe,
> grouped by side of price,
> sorted lowest to highest,
> and labeled by **current role**, not origin kind.

That is the cleanest operator surface for the next phase.
