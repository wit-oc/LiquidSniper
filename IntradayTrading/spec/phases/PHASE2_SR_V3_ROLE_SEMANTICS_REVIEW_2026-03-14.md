# Phase 2 S/R V3 Role Semantics Review — 2026-03-14

Branch: `phase2-zone-engine-v3`
Commit anchor: `043ec35`
Repo: <https://github.com/wit-oc/LiquidSniper>

## Why this review exists

The V3 architecture is now substantially in place:
- shadow-first
- schema-first
- selector separation
- native structure candidates
- role-aware nearest-four
- canonical family provenance in shadow outputs

But the **diagnostic interpretation layer still looks wrong** in an important way:

> the UI/backend can still surface zones labeled as **"resistance" below current price** and **"support" above current price** in the Daily major map.

For execution/review surfaces, that is semantically wrong.

Any level:
- **below current price** should be treated as **support**
- **above current price** should be treated as **resistance**
- **containing current price** should be treated as an **active band / containing zone**

So the question is no longer "is the architecture missing?"
It is now:

> Are we leaking **origin/formation kind** into **current execution-facing role**, and what is the smallest correct contract change to fix that without destroying provenance?

## Direct assessment of where we are

### What seems true now
- The engine is no longer obviously broken in the earlier ways.
- BTC/ETH shadow outputs are materially more coherent than before.
- Canonical provenance now survives into shadow outputs.
- ETH looks reasonably interpretable.
- BTC remains the hardest diagnostic case.

### What now looks wrong
The main remaining confusion appears to be **semantic role modeling and presentation**, not raw zone generation.

In other words:
- the system knows how a zone was formed
- but it is still exposing that formation kind directly in surfaces where the user really needs the zone's **current role relative to price**

That means we may be conflating:
1. **origin / formation kind**
2. **current execution-facing role**

That distinction now seems like a foundational gap in the contract.

## Concrete live example that triggered this review

### BTCUSDT live shadow
Current price:
- `69,679`

Current 1D shadow majors include:
- `BTCUSDT:1D:base:371:support` -> `16.9k–20.5k` -> below price
- `BTCUSDT:1D:base:305:resistance` -> `17.0k–23.0k` -> below price
- `BTCUSDT:1D:base:223:resistance` -> `23.6k–25.2k` -> below price
- `BTCUSDT:1D:structure:bos_anchor:593:660:support` -> `24.2k–30.4k` -> below price
- `BTCUSDT:1D:base:14:resistance` -> `39.4k–45.5k` -> below price
- `BTCUSDT:1D:base:781:support` -> `48.9k–58.2k` -> below price
- `BTCUSDT:1D:base:1201:support` -> `80.7k–85.7k` -> above price
- `BTCUSDT:1D:base:1280:support` -> `106.6k–113.4k` -> above price

That is the core semantic failure mode.

Even if a zone **originated** as a resistance-born shelf or flip, once it sits below current price in a review/execution surface, showing it as plain `resistance` is wrong and deeply confusing.

### ETHUSDT live shadow
Current price:
- `2,024.86`

ETH majors show a similar but less alarming issue because some zones contain price and the structure picture is healthier.
Still, the same contract ambiguity exists.

## Backend / UI diagnosis

### 1) Backend engine / nearest-four path
In `liquidsniper/core/zone_engine_v3.py`, `nearest_four_levels(...)` is already more role-aware than the rest of the system:
- it uses `side_aware_interaction(...)`
- it slots supports vs resistances by aligned side

But the formatted payload still sets:
- `payload["kind"] = zone.get("zone_kind")`

So even here, the surfaced `kind` is still rooted in the stored/origin kind, not an explicit current role field.

### 2) Pair analytics layer
In `liquidsniper/core/pair_analytics.py`:
- `build_pair_analytics_snapshot(...)` currently builds:
  - `majors` by `tf == 1D`
  - `operational` by `tf == 4H`
- those are sorted by score and summarized via `summarize_zone_for_pair_analytics(...)`

But there is no explicit split between:
- `origin_kind`
- `current_role`
- `relative_position` (`below` / `contains` / `above`)

So the analytics contract is still semantically under-specified for review/execution interpretation.

### 3) Diagnostic UI
In `liquidsniper/web/app.py`, the main SR section still renders:
- a flat **Nearest / next ladder**
- a flat **Majors vs operational** panel
- `majors[:4]`
- `operational[:4]`

Problems:
1. majors are truncated to 4
2. majors are not grouped by side of price
3. the surface mixes compact legacy-style analytics with the shadow compare block
4. the visible labels still lean on `kind`/`zone_kind` language that can contradict current price position

This means the UI may be amplifying the semantic defect, but the defect is not purely UI.

## Current hypothesis

The remaining foundational issue is:

> The system still lacks a clean separation between a zone's **origin/formation identity** and its **current execution-facing role**.

### Put more bluntly
We likely need something like:
- `origin_kind` or `formation_kind`
- `current_role`
- `relative_position`

Where:
- `origin_kind` preserves how the zone was formed historically
- `current_role` answers what the zone means **now** relative to current price
- `relative_position` makes the side-of-price relation explicit

Without that split, the user will keep seeing absurd-but-technically-explainable outputs like:
- resistance below price
- support above price

## Why this matters
This is not just cosmetic.

If the diagnostic surfaces are semantically wrong, then:
- operator trust degrades
- model review becomes harder
- calibration discussions mix up true model issues with display-contract issues
- we risk tuning the engine to compensate for what is actually a role-semantics bug

## Minimal files to anchor on
Only anchor on these unless you truly need more:

1. `IntradayTrading/spec/phases/PHASE2_SR_V3_PEER_REVIEW_BUNDLE_2026-03-14.md`
   - current post-provenance architecture state
2. `docs/zone_schema_v2.md`
   - current canonical zone contract
3. `docs/selector_policy_v2.md`
   - separation between Daily / 4H / nearest-four
4. `liquidsniper/core/zone_engine_v3.py`
   - current V3 engine + nearest-four semantics
5. `liquidsniper/core/pair_analytics.py`
   - current analytics summary contract
6. `liquidsniper/web/app.py`
   - current diagnostic rendering path

## Optional raw evidence (only if needed)
If you need raw evidence, use only:
- `/data/artifacts/sr/shadow/v3/bootstrap_snapshot.json`
- `/data/artifacts/sr/shadow/v3/nearest_BTCUSDT.json`
- `/data/artifacts/sr/shadow/v3/nearest_ETHUSDT.json`

## What I want reviewed
Please answer these directly:

1. Is the current issue best understood as a **semantic contract problem** (origin kind vs current role), rather than a primarily weighting/tuning problem?
2. Is the right next fix to explicitly add something like:
   - `origin_kind`
   - `current_role`
   - `relative_position`
   to the canonical or surfaced contract?
3. For review/execution-facing surfaces, should the system always present:
   - below-price zones as support
   - above-price zones as resistance
   - containing-price zones as active/containing bands
   even if the origin/formation kind differs?
4. Should the diagnostic UI be changed to group Daily majors into:
   - below current price
   - contains current price
   - above current price
   instead of showing a flat top-4 major list?
5. Is there any reason this role-semantics correction should wait until after more calibration, or is it the correct immediate next fix before further tuning?

## My working recommendation

Unless code evidence strongly contradicts it, my recommendation is:

1. treat this as a **role-semantics / contract-layer issue**
2. introduce explicit separation between:
   - origin kind
   - current role
   - relative position
3. update pair analytics and the UI to use **current role** for all primary review/execution-facing labels
4. keep origin kind as a secondary diagnostic/provenance field
5. only then continue deeper calibration on BTC/ETH

That feels like the smallest principled next move.
