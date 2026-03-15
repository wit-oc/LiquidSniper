> **Status:** Historical checkpoint / superseded for next-step planning. This bundle captured the post-provenance state and asked whether architecture was complete enough for calibration mode. Subsequent review concluded a targeted redesign pass is still needed around role semantics, review-surface separation, and then structure/promotion follow-through. Use `PHASE2_SR_V3_REDESIGN_PROPOSAL_2026-03-15.md` as the current proposal.

# Phase 2 S/R V3 Peer Review Bundle — 2026-03-14

Branch: `phase2-zone-engine-v3`
Commit anchor: `0bb5bff`

## Review objective

Assess whether Phase 2 V3 has now achieved the intended **architecture and evidence model** strongly enough that work should move primarily into **validation / calibration** rather than more architecture invention.

This is **not** a request for another generic tuning pass.

The core question now is:

> Given native structure candidates, provenance-aware Daily promotion, role-aware nearest-four, and canonical family provenance surviving into shadow outputs, has the architecture vision effectively been achieved — with the remaining work now mainly calibration / validation rather than design correction?

## Minimal anchor files

Only anchor on these unless you truly need more:

1. `docs/phase2_zone_engine_v3_steering_packet.md`
   - target architecture, migration stance, non-goals
2. `docs/zone_schema_v2.md`
   - canonical zone contract and MAP vs LIVE separation
3. `docs/selector_policy_v2.md`
   - Daily / 4H / nearest-four selector separation
4. `liquidsniper/core/zone_engine_v3.py`
   - current V3 shadow implementation, including structure/base/reaction generation, merge/arbitration, nearest-four wrapper, and provenance stamping
5. `liquidsniper/core/zone_selectors.py`
   - provenance-aware Daily promotion logic
6. `liquidsniper/core/pair_analytics.py`
   - downstream preservation/summarization of canonical provenance fields
7. `liquidsniper/core/sr_engine_v2.py`
   - reaction-family baseline/reference, not final truth engine

## Files you should *not* need up front

Avoid broad repo sprawl unless necessary:
- `liquidsniper/web/app.py` (UI only)
- old strategy docs unrelated to V3 shadow behavior
- full repo history
- unrelated paper/soak docs

## What has changed since the last bundle

### Earlier review state (2026-03-12 bundle)
At that point we had:
- shadow-first architecture in place
- role-aware nearest-four fixed
- base-family flood reduced
- merge compatibility improved
- but architecture still lacked:
  - native structure-family truth strong enough to trust
  - canonical family provenance surviving meaningfully into outputs

### New work since then

#### 1) Native structure-family tranche
Landed in:
- `liquidsniper/core/zone_engine_v3.py`
- `liquidsniper/core/zone_selectors.py`

What changed:
- native structure candidates now exist (not just reaction-family surrogates)
- provenance-aware Daily promotion added
- selector behavior now generically prefers corroborated structure-involved majors over pure base-only shelves where appropriate

Commit anchor:
- `c02bf41` — `phase2(v3): add native structure candidates and daily provenance weighting`

#### 2) Canonical provenance-stamping tranche
Landed in:
- `liquidsniper/core/zone_engine_v3.py`
- `liquidsniper/core/pair_analytics.py`
- tests

What changed:
- canonical `family_stamp_contract` now survives into shadow outputs
- non-empty `family_provenance` bundles now exist for:
  - `base`
  - `reaction`
  - `structure`
- merged zones preserve per-family provenance instead of degrading to label-only family sets
- nearest ladders and pair analytics now surface the same canonical family evidence bundle

Commit anchor:
- `0bb5bff` — `phase2(v3): stamp canonical family provenance in shadow outputs`

## Current implementation posture

### What is intentionally true now
- `sr_engine_v2` is treated as **reaction-family v1**, not final zone truth
- `zone_engine_v3.py` hosts:
  - structure candidates
  - base candidates
  - reaction candidates
  - merge/arbitration
  - scoring
  - Daily / operational / nearest-four shadow selection
- baseline path remains intact
- V3 remains shadow-first / observability-first
- outputs now carry explicit evidence, not mostly label-level family inference

## Current live evidence (post structure + provenance tranches)

### BTCUSDT

Shadow snapshot summary:
- total zones: `20`
- 1D kept: `8`
- 4H kept: `12`

Candidate counts:
- 1D: `structure=23`, `base=34`, `reaction=17`, `merged=26`
- 4H: `structure=11`, `base=12`, `reaction=22`, `merged=23`

Current 1D majors:
- `BTCUSDT:1D:base:371:support` -> `['base','structure']`
- `BTCUSDT:1D:base:305:resistance` -> `['base','reaction','structure']`
- `BTCUSDT:1D:base:223:resistance` -> `['base','structure']`
- `BTCUSDT:1D:structure:bos_anchor:593:660:support` -> `['base','reaction','structure']`
- `BTCUSDT:1D:base:14:resistance` -> `['base','reaction','structure']`
- `BTCUSDT:1D:base:781:support` -> `['base','reaction','structure']`
- `BTCUSDT:1D:base:1201:support` -> `['base','reaction']`
- `BTCUSDT:1D:base:1280:support` -> `['base','reaction']`

Current nearest-four:
- nearest support: `4H support 65,182.46 → 66,483.32` with `reaction` provenance
- next support: `4H support 62,595.27 → 62,925.03` with `reaction` provenance
- nearest resistance: `4H mixed 72,413.96 → 72,791.84` with `reaction` provenance
- next resistance: `4H resistance 89,397.2 → 91,900.0` with `reaction + structure` provenance

Interpretation:
- BTC is no longer dominated by pure base-only Daily winners
- Daily still feels somewhat base-led / long-history heavy
- near-price ladder is materially saner and mostly 4H reaction-led, which is directionally good
- BTC remains the hardest diagnostic case

### ETHUSDT

Shadow snapshot summary:
- total zones: `20`
- 1D kept: `8`
- 4H kept: `12`

Candidate counts:
- 1D: `structure=23`, `base=18`, `reaction=16`, `merged=23`
- 4H: `structure=9`, `base=10`, `reaction=23`, `merged=22`

Current 1D majors:
- `ETHUSDT:1D:structure:flip_anchor:168:468:support` -> `['reaction','structure']`
- `ETHUSDT:1D:base:1202:support` -> `['base','reaction','structure']`
- `ETHUSDT:1D:base:1216:support` -> `['base','reaction','structure']`
- `ETHUSDT:1D:base:1177:resistance` -> `['base','reaction','structure']`
- `ETHUSDT:1D:structure:bos_anchor:752:774:support` -> `['structure']`
- `ETHUSDT:1D:structure:bos_anchor:933:946:resistance` -> `['reaction','structure']`
- `ETHUSDT:1D:13:4157.315` -> `['reaction','structure']`
- `ETHUSDT:1D:structure:flip_anchor:1331:1405:resistance` -> `['reaction','structure']`

Current nearest-four:
- nearest support: `1D support 1,751.45 → 2,689.15` with `base + reaction + structure` provenance
- next support: `4H support 1,906.44 → 1,935.766` with `reaction` provenance
- nearest resistance: `1D resistance 1,941.86 → 2,157.648` with `base + reaction + structure` provenance
- next resistance: `4H resistance 2,149.646 → 2,402.403` with `reaction + structure` provenance

Interpretation:
- ETH looks structurally healthier than BTC
- multiple native structure winners exist on Daily
- confluence appears real rather than decorative
- current macro map is plausible, though some 1D bands remain broad

## What appears achieved now

### Architecture-level wins
1. **Shadow-first migration posture exists and is working**
2. **Canonical zone schema exists**
3. **Daily / 4H / nearest-four selector separation exists**
4. **Nearest-four role hygiene exists**
5. **Native structure candidates exist**
6. **Base/reaction/structure families all exist and can merge coherently**
7. **Canonical family provenance now survives into nearest ladders, merged majors, and pair analytics**

### Behavioral wins
1. gross base-candidate flood is no longer the main story
2. support/resistance slot crossing is fixed
3. pure base-only Daily winners are no longer the dominant failure mode
4. ETH now looks like a plausibly good case, not a blind-luck one

## What still looks imperfect

1. **BTC Daily remains somewhat base-led / deep-history-heavy**
   - not pure-base broken, but still not as clean as ETH
2. **Some 1D bands remain broad**
   - architecture supports future `core_*` refinement, but that is not the main current blocker
3. **ATR/lifecycle refinement is still support work, not fully matured**
4. **Certification/validation is not finished**
   - architecture exists; calibration still needed

## Review question

Please answer these specifically:

1. Has the architecture vision now been achieved strongly enough that the project should move primarily into **validation/calibration mode** rather than more architectural redesign?
2. Is BTC now best understood as:
   - a still-useful but harder diagnostic case,
   - or evidence that the architecture is still materially wrong?
3. What is the **smallest next generic calibration step** you would recommend now that structure truth and provenance truth both exist?
4. Do you agree that the remaining work should now center on:
   - validation basket review,
   - core-band / breadth refinement if needed,
   - ATR/lifecycle refinement as support work,
   - and calibration rather than architecture invention?

## Optional raw artifacts (only if needed)

If you need raw evidence beyond the summary above, inspect only these:
- baseline snapshot: `/data/artifacts/sr/bootstrap_snapshot.json`
- shadow snapshot: `/data/artifacts/sr/shadow/v3/bootstrap_snapshot.json`
- shadow nearest BTC: `/data/artifacts/sr/shadow/v3/nearest_BTCUSDT.json`
- shadow nearest ETH: `/data/artifacts/sr/shadow/v3/nearest_ETHUSDT.json`

Use additional files only if you can explain why they are necessary.
