# Phase 2 — Zone Engine V3 Execution Packet (2026-03-10)

Status: APPROVED TO START  
Branch: `phase2-zone-engine-v3`

## Why this exists
`sr_engine_v2` is useful, but it is still fundamentally a **reaction-weighted pivot-cluster engine**.  
We are no longer going to keep tuning it as if it were already the intended Foxian-style zone-first model.

Instead:
- keep `sr_engine_v2` as the **reaction family** baseline,
- build a new layered engine (`zone_engine_v3`) that separates:
  1. zone generation
  2. selection policy
  3. execution-oriented nearest-4 outputs

---

## Doctrine / constraints
These are hard requirements for V3:
- No operator-bias mode in production path
- No symbol-specific hardcoding
- Daily majors use **all available history**
- No global aging decay for Daily majors
- 4H is operational context, not macro source
- BTC is a failure-mode diagnostic case, not an answer key
- ETH is a blind sanity case
- The goal is to generalize across **100s of pairs**

---

## Primary design steering (from GPT 5.4 Pro review)
We are building toward three evidence families:
1. **Structure family**
   - HTF BoS / CHoCH / flip anchors
2. **Base family**
   - shelf / compression / overlap / breakout ranges
3. **Reaction family**
   - current `sr_engine_v2` style pivot-cluster + reaction behavior scoring

These families feed a shared candidate-zone layer.
Selection is a separate layer.

---

## Immediate technical priorities
### V3-A — Scaffolding and contract split
Create new engine/selector contract:
- `zone_engine_v3.py`
- `zone_candidates_from_structure(...)`
- `zone_candidates_from_base(...)`
- `zone_candidates_from_reaction(...)`
- `merge_candidate_zones(...)`
- `score_zone(...)`
- `select_daily_majors(...)`
- `select_operational_zones(...)`
- `nearest_four_levels(...)`

Also:
- re-scope current `sr_engine_v2` as **reaction family v1**
- keep the current app/bootstrapping flow usable while V3 is under construction

### V3-B — Fix core design flaws
1. **Local ATR instead of one global ATR scalar**
2. **Side-aware interaction logic**
   - interaction approach from above/below
   - reject / accept / deviation conditioned on interaction context

### V3-C — Add real base/shelf geometry
A real base detector must use some combination of:
- compression
- overlap persistence
- edge touches
- breakout confirmation

This should produce candidate zones directly, not hope shelves emerge from pivot clusters.

### V3-D — Selection and output contracts
Formalize:
- Daily majors (map truth)
- 4H operational zones (execution context)
- nearest-4 output contract for downstream systems

---

## Keep vs change
### Keep
- `liquidsniper/core/sr_engine_v2.py` as reaction-family logic
- bootstrap / persistence / UI architecture
- current diagnostics work
- nearest-4 concept and payload direction

### Change
- stop deriving all geometry from pivots
- stop keeping selection policy buried in bootstrap-only logic
- stop using a single ATR scalar across full timeframe history
- stop using blunt side-agnostic touch/retest classification

---

## Validation basket
Use the tracked blind basket:
- `IntradayTrading/spec/phases/PHASE2_ZONE_ENGINE_V3_VALIDATION_BASKET_2026-03-10.json`

Purpose:
- BTC / ETH sanity
- blind regression across top 15 non-stable market-cap coins
- reduce chart-by-chart whack-a-mole

---

## Validation methodology
### Diagnostic cases
Use BTC only to test known failure modes:
- `60 vs 65`
- `74 vs 80`
- `98 / 104 / 108 / 115`

Use ETH as a blind sanity case.

### Blind basket checks
Across the validation basket, inspect for:
- dense-band overfire
- score saturation
- wick-only phantom levels
- over-preserved spent zones
- failure to produce clean nearest-4 outputs

---

## Deliverables for the first V3 pass
1. New V3 engine/selector module scaffold
2. reaction family adapter calling/reusing `sr_engine_v2`
3. local-ATR utilities
4. side-aware interaction primitive
5. base/shelf candidate detector stub or first implementation
6. selector contract for Daily / 4H / nearest-4
7. regression harness using BTC, ETH, and validation basket

---

## Recommended implementation order
1. Scaffold `zone_engine_v3`
2. Move selection logic into a dedicated selector layer
3. Implement local ATR + side-aware interaction first
4. Add base/shelf candidate family
5. Hook reaction family into candidate merge
6. Re-run BTC / ETH / blind basket
7. Then do another GPT 5.4 Pro review if needed

---

## Notes for future review
This branch is intentionally a redesign branch, not another micro-tune of `sr_engine_v2`.
The purpose is to converge the codebase toward the actual doctrinal model instead of continuing to patch around a narrower pivot-cluster engine.
