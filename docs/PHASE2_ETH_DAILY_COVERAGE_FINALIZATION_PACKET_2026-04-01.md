# Phase 2 ETH Daily Coverage Finalization Packet — 2026-04-01

Status: proposed finalization packet  
Branch: `phase2-zone-engine-v3`

## 1) Purpose

This is a **small finish-line tranche**.

The Phase 2 map is now substantially closer to target:
- BTC improved materially after Daily-major cleanup
- 4H selector decluttering is holding
- the remaining visible issues are narrow and ETH-focused

This tranche exists to address the strongest remaining review complaint:
- **ETH Daily is missing the ~2800 regime** even though credible 1D structure exists there

Secondary / optional review item:
- ETH 4H below-price supports around ~1800 and ~1900 may still feel a bit tight, but this is lower priority and should only be revisited after the Daily fix is rerun

## 2) Current observations driving the tranche

## A) ETH Daily ~2800 is likely a selector miss, not a generation miss

The current selected ETH 1D surface is too sparse on the upside:
- below price: 1
- contains price: 1
- above price: 2

Manual review flagged the absence of the ~2800 regime as suspicious / too reactive.

Candidate-pool inspection found credible ETH 1D candidates in the `2400–3200` region, including:
- a structure-backed zone around `2711 -> 2889 -> 2993`
- a higher zone around `3033 -> 3116 -> 3190`

Interpretation:
- the engine can already generate credible 1D upside anchors there
- the current Daily-major selector is pruning that regime too aggressively

## B) ETH 4H ~1800 / ~1900 is a softer issue

Current kept ETH 4H supports below price are approximately:
- `1813 -> 1828 -> 1842`
- `1935 -> 1972 -> 2015`

This can look a little tight in review, but pool inspection suggests these may still represent two distinct support neighborhoods:
- a lower support neighborhood
- a near-price support neighborhood

Interpretation:
- this is worth watching
- but it is **not the primary target** of this tranche

## 3) Scope

In scope:
1. ETH Daily upside coverage refinement
2. ETH-specific Daily selector trace clarity where needed
3. BTC/ETH rerun after the ETH Daily change is complete
4. optional post-rerun check on ETH 4H ~1800 / ~1900 proximity
5. refreshed checkpoint summary

Out of scope:
- broad Daily selector redesign
- 4H selector redesign
- nearest-four changes
- cross-symbol tuning sweep
- architecture changes

## 4) Problem statement

The current Daily-major selector still has one likely over-pruning behavior on ETH:
- it can preserve the containing band near current price and the much higher upside anchors,
- while skipping a credible **intermediate upside Daily regime** around ~2800

That makes the ETH Daily map feel too sparse and under-reactive in the mid-upside regime.

## 5) Proposed implementation changes

## P1) Add ETH-relevant intermediate-upside Daily coverage logic

Target:
- `liquidsniper/core/zone_selectors.py`
- Daily-major coverage logic introduced in the recent Daily-major tranche

Implementation goal:
- when the selected Daily-major surface has:
  - a containing / near-current regime,
  - then a large upside jump,
  - and the candidate pool contains a credible 1D intermediate upside anchor,
- allow that intermediate regime to survive as a Daily-major anchor instead of being pruned away

Guardrail:
- do **not** turn this into symbol-specific special-casing
- implement it as a general selector behavior that ETH currently exposes most clearly

## P2) Keep the rule narrow

This should not become:
- “always fill the middle”
- “always keep three upside Daily anchors”
- “always reward nearest-above levels”

This should behave more like:
- preserve an intermediate upside regime **only when**
  - the gap is large,
  - the intermediate candidate is credible,
  - and keeping it improves the macro map more than the extra-high anchor set alone

## P3) Keep Daily trace reasons explicit

If a mid-upside Daily zone survives because of this finalization logic, the selector trace should say so clearly.

Examples:
- `kept: daily intermediate upside coverage anchor`
- `kept: daily current-regime coverage anchor`
- `dropped: weaker extra-high anchor after intermediate coverage preservation`

## P4) Defer 4H compression unless still needed after rerun

Do not proactively merge the ETH 4H ~1800 / ~1900 pair in this tranche.

Instead:
- rerun after the Daily change
- inspect whether that pair still looks awkward in context
- only then decide whether a tiny 4H polish pass is justified

## 6) Execution sequence

## T1) ETH Daily selector audit

Deliverable:
- short note or inline implementation comments confirming which Daily coverage rule currently causes the intermediate ~2800 regime to be lost

Exit condition:
- exact selector seam is known before edits begin

## T2) Implement intermediate-upside Daily coverage refinement

Deliverable:
- Daily-major selector can preserve a credible intermediate upside regime when the map would otherwise jump too far upward

Exit condition:
- ETH Daily no longer jumps too abruptly from the containing region to the much higher upside anchors if ~2800-level structure is credible

## T3) Preserve trace clarity

Deliverable:
- kept ETH Daily zone can explicitly show why it survived

Exit condition:
- review output makes the fix legible, not just numerically present

## T4) Rerun BTC/ETH shadow artifacts

Deliverable:
- refreshed `bootstrap_snapshot.json`
- refreshed authoritative review surface

Exit condition:
- we can directly compare whether the ETH Daily ~2800 region is now represented

## T5) Optional 4H decision point

Deliverable:
- explicit judgment after rerun:
  - leave ETH 4H ~1800 / ~1900 as-is
  - or queue a micro-polish pass

Exit condition:
- we do not change 4H unless the rerun still shows a meaningful review problem

## T6) Refresh final checkpoint summary

Deliverable:
- concise note stating:
  - whether ETH Daily ~2800 was restored
  - whether 4H remained unchanged or needs a micro-pass
  - whether the map now feels finish-line ready

## 7) Acceptance criteria

## A) Primary acceptance

1. **ETH Daily regains an intermediate upside regime when justified**
- the selected ETH 1D map should no longer skip the ~2800 region if the candidate pool contains a credible anchor there

2. **Daily does not become noisy again**
- fixing ETH ~2800 must not reopen the earlier clutter problems on BTC or ETH

3. **BTC remains stable**
- BTC improvements from the prior tranche must hold

## B) ETH-specific acceptance gates

### ETH Daily gate
Pass target:
- a credible Daily anchor around the ~2800 regime survives if supported by the candidate pool
- the selected ETH Daily map feels less under-reactive on the upside

### ETH 4H gate
Pass target:
- after the Daily rerun, decide explicitly whether the ~1800 / ~1900 pair still feels too tight
- no change required if they still read as genuinely distinct neighborhoods

## C) Non-regression gates

- 4H decluttering remains intact
- BTC Daily does not regress into historical clutter or current-regime voids
- tests remain green

## 8) Validation plan

Automated validation after the tranche completes:
- `tests/test_pair_analytics.py`
- `tests/test_zone_engine_v3.py`
- `tests/test_sr_authoritative_levels_ui.py`
- `tests/test_sr_shadow_authoritative_view.py`
- any new ETH Daily selector tests added in this pass

Artifact refresh:
- `python3 -m liquidsniper.ops.sr_bootstrap --shadow-v3 --symbols BTCUSDT,ETHUSDT`

## 9) Deliverables

Required deliverables:
1. ETH Daily selector refinement in `liquidsniper/core/zone_selectors.py`
2. any supporting trace/review-surface updates
3. refreshed BTC/ETH artifacts
4. refreshed checkpoint note
5. concise final recommendation on whether the ETH 4H pair needs any extra polish

## 10) Final recommendation

Treat this as a **tiny finalization tranche**.

Priority order:
1. restore ETH Daily ~2800 regime if justified
2. rerun and review
3. only then decide whether ETH 4H ~1800 / ~1900 needs a micro-pass

That is the cleanest path to the finish line without reopening solved problems.
