# Phase 2 Daily-Major Coverage Implementation Packet — 2026-03-30

Status: proposed follow-up implementation packet  
Branch: `phase2-zone-engine-v3`

## 1) Executive summary

The Phase 2 selector-alignment tranche materially improved the **4H operational** surface.

What remains now is concentrated on the **Daily-major** surface, specifically on BTC:
- too many selected 1D anchors survive in the **20k–28k** historical pocket
- the selected 1D map leaves a visually strange **50k–83k void** even though valid 1D candidates exist in that regime

This means the next move should be a **narrow Daily-major selector follow-up**, not a new architecture pass and not a broad tuning sweep.

Primary goal:
- clean up **overlapping / nested historical Daily pockets**
- prevent Daily-major from leaving a large active-regime vacuum when credible 1D candidates already exist there

## 2) Architecture stance for this tranche

This packet assumes the following remain accepted:
- Zone Schema V2 remains the canonical model
- `zone_engine_v3` remains the shadow-first seam
- Daily-major, 4H operational, and nearest-four remain distinct surfaces
- Daily macro/core refinement stays in place
- the 4H selector-alignment tranche is treated as complete enough to build on

This is therefore:
- **Daily-major selector refinement**

This is not:
- a new architecture rewrite
- a general parameter sweep
- a 4H rework
- a nearest-four redesign

## 3) Evidence driving this packet

## A) Selected BTC 1D surface currently over-preserves the 20k–28k pocket

Current selected BTC 1D anchors below price include:
- `20.4k -> 21.5k`
- `24.1k -> 25.2k`
- `24.2k -> 28.7k`

Interpretation:
- multiple Daily anchors are surviving inside what reads like one broader historical pocket
- the final two are especially close / nested and should likely be competing more directly for one macro slot

## B) Selected BTC 1D surface under-represents the active 50k–83k regime

Selected BTC 1D below-price anchors currently include:
- `42.6k -> 43.5k`
- `50.5k -> 51.3k`

Then the next selected 1D zone above price is:
- `84.0k -> 85.7k`

That creates a large apparent Daily-major void from roughly **50k to 83k**.

## C) The 50k–83k void is not mainly a generation gap

Inspection of the BTC 1D confirmed candidate pool showed credible candidates in that regime, including examples around:
- `56.3k -> 65.0k`
- `60.2k -> 63.5k`
- `65.6k -> 72.3k`
- `74.5k -> 79.2k`

Interpretation:
- valid 1D candidates exist in the current macro regime
- they are being generated and scored
- the selected Daily-major surface is failing to preserve enough of them

So the 50k–83k problem is primarily a **Daily-major selection / coverage problem**, not a raw candidate-generation failure.

## 4) Problem statement

The Daily-major selector still has two specific failure modes:

### M1) Historical pocket over-fragmentation
The selector can preserve multiple overlapping or nested 1D anchors inside one historical pocket when they should mostly compete for one macro slot.

### M2) Current-regime under-coverage
The selector can leave a large active-regime gap even when credible 1D candidates exist inside that gap.

In plain English:
- it is still slightly too willing to keep extra distant historical anchors
- and still too willing to under-represent the current macro regime once one nearby anchor survives

## 5) Scope of this tranche

In scope:
1. Daily-major pocket consolidation for overlapping / nested macro anchors
2. Daily-major current-regime coverage guardrail
3. Daily-major trace enrichment where needed
4. BTC/ETH rerun after the full Daily tranche is complete
5. refreshed checkpoint / artifact summary

Out of scope:
- 4H operational redesign
- nearest-four redesign
- deeper structure-family generator redesign
- broad basket sweeps before BTC/ETH re-check

## 6) Proposed implementation changes

## P1) Add Daily pocket-overlap competition logic

Target area:
- `liquidsniper/core/zone_selectors.py`
- specifically Daily-major path around:
  - `select_daily_local_band_representatives(...)`
  - `collapse_zones_by_distance(...)`
  - `select_daily_majors(...)`

Implementation goal:
- make Daily-major treat overlapping / nested 1D macro pockets as direct competitors more often
- avoid surfacing multiple co-equal Daily majors from one historical pocket unless they are truly distinct doctrinal ideas

Preferred logic:
- interval overlap / edge-gap reasoning, not just midpoint spacing
- allow one pocket to keep multiple representatives only when:
  - overlap is limited enough
  - provenance meaning is materially different
  - both anchors improve the macro map rather than clutter it

## P2) Add Daily current-regime coverage guardrail

New selector behavior:
- after primary Daily-major pruning, inspect the distance / gap structure of the selected 1D map relative to current price
- if a very large price-region void exists between selected Daily anchors,
- and confirmed credible 1D candidates already exist inside that gap,
- allow a current-regime candidate to displace a weaker extra-distant historical survivor

Important guardrail:
- this is **not** a general “fill empty chart space” rule
- it is a **coverage sanity rule** only when:
  1. the gap is unusually large,
  2. the candidate pool already contains credible 1D anchors in that gap,
  3. the current map is under-representing the active macro regime

## P3) Preserve Daily doctrine while doing this

The Daily-major surface must still prefer:
- macro structure
- durable anchors
- anti-clutter behavior
- non-proximity-chasing behavior

So the new coverage rule must not turn Daily into:
- “nearest useful Daily levels”
- “fill every large interval”
- “favor current price just because current price is there”

Instead it should behave like:
- macro truth, with enough representation of the active regime to remain useful

## P4) Add Daily selector traces for pocket and coverage decisions

For kept Daily zones, preserve or enrich compact trace fields like:
- `selector_surface = daily_major`
- `selector_status = kept`
- `selector_reason`
- `selector_rank`

When a zone is kept because it preserved current-regime coverage or won a pocket-competition decision, the reason string should say so explicitly.

Examples:
- `kept: daily macro anchor after pocket consolidation`
- `kept: daily current-regime coverage anchor`
- `dropped: overlapped stronger daily pocket representative`

## 7) Single-stream execution sequence

This should again run as one ordered stream.

## T1) Daily-major mismatch audit

Deliverable:
- short note mapping the current Daily-major implementation to the two observed problems:
  - 20k–28k pocket over-fragmentation
  - 50k–83k active-regime under-coverage

Exit condition:
- exact Daily selector seams are documented before edits begin

## T2) Implement Daily pocket consolidation

Deliverable:
- overlapping / nested Daily macro pockets compete more directly
- clustered historical pocket survivors are reduced when they represent one broad macro idea

Exit condition:
- BTC 20k–28k no longer surfaces as too many co-equal Daily anchors unless the distinctions are clearly justified

## T3) Implement Daily current-regime coverage guardrail

Deliverable:
- Daily-major can preserve a credible current-regime anchor inside a large active-regime void when the candidate pool already supports it

Exit condition:
- BTC no longer has a weird hollow Daily-major map from ~50k to ~83k if valid 1D candidates exist inside that region

## T4) Preserve / enrich Daily selector traces

Deliverable:
- review outputs can explain whether a Daily zone survived because of:
  - pocket win
  - macro priority
  - current-regime coverage preservation

Exit condition:
- the post-run review surface can explain Daily-major keep/drop behavior without guesswork

## T5) Full integrated rerun

Deliverable:
- rerun BTC/ETH shadow artifacts after the Daily tranche is complete
- inspect both selected Daily surfaces and candidate coverage behavior

Exit condition:
- the new Daily surface can be evaluated against the old two complaints directly

## T6) Refresh checkpoint doc

Deliverable:
- short checkpoint summarizing:
  - what changed in Daily-major
  - whether the 20k–28k cluster reduced
  - whether the 50k–83k void is improved
  - whether any new regressions appeared

Exit condition:
- the human can test with a clean summary of the intended improvements

## 8) Acceptance criteria

## A) Behavioral acceptance

1. **Daily remains Daily**
- do not collapse Daily-major into a proximity surface
- do not regress the existing macro/core doctrine

2. **Pocket consolidation improves**
- overlapping or nested Daily anchors in the same historical pocket no longer survive as multiple co-equal majors unless they are truly distinct macro ideas

3. **Current-regime coverage improves**
- when credible 1D candidates exist in the current macro regime, the selected Daily-major map should not leave a visibly strange large void without a good reason

4. **Review trace quality improves**
- kept Daily zones can explain whether they survived through pocket competition or current-regime coverage logic

## B) BTC-specific acceptance gates

### BTC 1D historical pocket gate
Pass target:
- the current 20k–28k pocket is cleaner than the present multiple-survivor state
- nested / overlapping anchors in that area are reduced or better justified

### BTC 1D active-regime coverage gate
Pass target:
- the selected Daily-major map no longer jumps so abruptly from ~50k directly to ~84k if the candidate pool contains credible 1D anchors in between
- at least one reasonable current-regime Daily anchor survives in the upper-mid regime if the evidence supports it

### BTC 4H non-regression gate
Pass target:
- the 4H decluttering improvements from the previous tranche are preserved
- this Daily follow-up should not reintroduce 4H staircase clutter indirectly

## C) ETH guardrail

ETH should be checked for regressions, but this tranche is primarily BTC-driven.

Pass target:
- ETH Daily does not become noisier or more proximity-chasing
- no obvious regression in the existing 1D macro/core presentation

## 9) Validation plan

Automated validation to run after the full Daily tranche completes:
- `tests/test_pair_analytics.py`
- `tests/test_zone_engine_v3.py`
- `tests/test_sr_authoritative_levels_ui.py`
- `tests/test_sr_shadow_authoritative_view.py`
- new Daily-major selector tests added by this tranche

Artifact refresh after full implementation:
- `python3 -m liquidsniper.ops.sr_bootstrap --shadow-v3 --symbols BTCUSDT,ETHUSDT`

Human validation policy:
- keep this as a single stream
- resume manual chart validation only after the tranche is fully implemented and rerun

## 10) Deliverables

Required deliverables for this stream:
1. Daily-major selector changes in `liquidsniper/core/zone_selectors.py`
2. any necessary trace/review-surface propagation changes
3. new or updated tests covering Daily pocket consolidation and current-regime coverage
4. refreshed BTC/ETH artifacts
5. refreshed checkpoint doc
6. concise final summary of:
   - what Daily changed
   - whether the two complaints improved
   - what still looks weird if anything

## 11) Final recommendation

Treat this as the next narrow refinement tranche:
- **Daily-major pocket consolidation + current-regime coverage refinement**

That is the cleanest follow-up to the now-improved 4H surface, and it addresses exactly the two remaining issues that stood out in manual review.
