# Phase 2 S/R Timeframe Refinement Matrix — 2026-03-24

## Purpose

Translate the current validation read into concrete next-step work by timeframe.

This document is not another architecture proposal. It assumes:
- shadow path exists
- role semantics exist
- authoritative review surface exists or is being finished
- remaining work is now primarily about making the 1D and 4H outputs more operator-useful and chart-faithful

## Current diagnosis

The engine is no longer failing in a catastrophic way.

The remaining issues now differ by timeframe:
- **1D** tends to produce zones that are directionally plausible but too broad to feel like clean operator-facing levels.
- **4H** tends to produce levels that are directionally plausible but too stacked / crowded near each other.

So the next work should be **timeframe-specific**, not one mushy “tune everything” pass.

---

## Matrix

| Timeframe | What looks good | What looks borderline | What looks wrong | Likely fix category | What not to do |
|---|---|---|---|---|---|
| **1D** | Macro regions often look directionally believable; supports/resistances are no longer semantically inverted; provenance and current-role labeling are much clearer | Bands are often too wide to be satisfying as reviewable levels; broad macro zones may still be valid but not sharp enough for operator validation | Some Daily levels feel more like entire battle ranges than levels/zones you would anchor to cleanly on a chart | **Core-band refinement / narrower operator-facing extraction inside broader macro zones** | Do not respond by just dropping Daily levels globally or by generic weight nudging |
| **4H** | Near-price levels feel much more believable than before; current-role semantics now make practical sense | Several nearby levels are separated by very small gaps; multiple bands may be individually defensible but collectively too noisy | Same-side operational levels can stack on top of each other enough that a human would treat them as one cluster | **Local consolidation / representative-level selection / de-duplication** | Do not solve by bluntly reducing all 4H counts or by removing useful nearby structure indiscriminately |

---

## Plain-English interpretation

### 1D
The question is no longer:
- “Is the engine finding anything real?”

The question is now:
- “How do we preserve the macro truth while surfacing a cleaner, narrower operator-facing level inside the broader zone?”

That suggests:
- broad zone can remain as macro context
- but operator validation may need a **core band** / **core midpoint** / **narrowed active core**

### 4H
The question is no longer:
- “Is the engine totally missing the nearby map?”

The question is now:
- “How do we collapse nearby same-side bands into cleaner operational clusters without deleting useful structure?”

That suggests:
- preserve the underlying evidence
- choose a better operator-facing representative level or cluster presentation

---

## Proposed next work order

### Step 1 — 1D core-band refinement
Goal:
- keep the broad macro zone for context
- derive a narrower operator-facing core for review/use

Possible directions:
- inner-core extraction from overlapping family evidence
- midpoint-centered narrower core using strongest evidence density
- explicit `macro_bounds` vs `core_bounds`

### Step 2 — 4H local consolidation
Goal:
- reduce stacked same-side levels that read like one cluster to a human

Possible directions:
- cluster nearby same-role operational bands
- choose representative winner per local cluster
- preserve subordinate bands as secondary/debug detail rather than co-equal operator-facing levels

### Step 3 — re-review BTC/ETH with the refined surfaces
Questions:
- does 1D now read as meaningful macro zones with usable anchor cores?
- does 4H now read as practical nearby navigation levels instead of a pileup?

### Step 4 — only then consider config/weight tuning
If the map is still off after 1D core-band and 4H consolidation work, then move into targeted config/threshold tuning.

---

## Recommended implementation split

### Lane 1 — 1D refinement
Primary focus:
- operator-facing core extraction for Daily zones

Relevant files:
- `liquidsniper/core/zone_engine_v3.py`
- `liquidsniper/core/pair_analytics.py`
- `docs/zone_schema_v2.md`
- `liquidsniper/web/app.py`

### Lane 2 — 4H refinement
Primary focus:
- local-band consolidation / cluster representative selection for operational levels

Relevant files:
- `liquidsniper/core/zone_selectors.py`
- `liquidsniper/core/pair_analytics.py`
- `docs/selector_policy_v2.md`
- `liquidsniper/web/app.py`

---

## Success criteria for this tranche

We should call this tranche successful if:
- 1D still preserves macro context, but levels are visibly narrower / more chart-usable
- 4H still preserves meaningful nearby structure, but stacked same-side clutter is reduced
- BTC and ETH both become easier to evaluate as “good / borderline / wrong” without needing a long explanation for every band
- no generic broad tuning pass was required to get there

---

## Bottom line

The next refinement should be split by timeframe:
- **1D = sharpen broad macro zones into cleaner operator-facing cores**
- **4H = consolidate nearby operational clutter into cleaner local representatives**

That is the cleanest next step before generic config tweaking.
