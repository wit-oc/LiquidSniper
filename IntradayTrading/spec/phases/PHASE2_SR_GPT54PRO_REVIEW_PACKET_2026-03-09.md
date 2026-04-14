# Phase 2 S/R — GPT 5.4 Pro Review Packet (2026-03-09)

Status: Ready for external design review  
Branch: `phase2-v7-zone-first-20260307`  
Current head: `c8c8780`  
Repo: `wit-oc/LiquidSniper`

## Review goal
We want a **design-level review** of the current Python S/R engine for Daily major zones and 4H operational zones.

This is **not** a Pine problem anymore.
The current system is:
- Python S/R engine (`liquidsniper/core/sr_engine_v2.py`)
- bootstrap/orchestration (`liquidsniper/ops/sr_bootstrap.py`)
- SQLite + JSON artifacts
- Streamlit verification UI (`liquidsniper/web/app.py`)

## Hard constraints / doctrine
- **No operator-bias mode** in the production path
- **No symbol-specific hardcoding**
- **Daily majors use all available history**
- **No global aging decay** for Daily majors
- 4H is operational context, not the source of macro majors
- Goal is to generalize to **100s of pairs**, not hand-fit BTC/ETH

## Files to inspect
Primary:
- `liquidsniper/core/sr_engine_v2.py`
- `liquidsniper/ops/sr_bootstrap.py`
- `liquidsniper/web/app.py`
- `liquidsniper/config/sr_bootstrap.default.json`

Relevant migrations/tests:
- `liquidsniper/core/migrations/009_sr_zone_diagnostics.sql`
- `liquidsniper/core/migrations/010_sr_zone_behavior_diagnostics.sql`
- `tests/test_sr_bootstrap_daily_selection.py`
- `tests/test_db_migrations.py`

## Exact logic areas that currently drive behavior
### In `liquidsniper/core/sr_engine_v2.py`
- `_is_meaningful_touch(...)`
  - reaction magnitude
  - carry / follow-through
  - body/close behavior diagnostics
- `evaluate_zone_lifecycle(...)`
  - touch/retest lifecycle + behavior summaries
- `_zone_scores(...)`
  - strength / reaction / efficiency / spent penalties
- `build_zones_for_tf(...)`
  - per-zone score assignment and persisted fields
- `persist_sr_state(...)`
  - writes SR diagnostics into SQLite
- `_zone_fmt_with_distance(...)`
  - includes diagnostics in nearest payloads

### In `liquidsniper/ops/sr_bootstrap.py`
- `_zone_rank_key(...)`
- `_daily_retest_weight(...)`
- `_apply_daily_soft_retest_weights(...)`
- `_collapse_zones_by_distance(...)`
- `_select_daily_local_band_representatives(...)`
- `_select_spatially_diverse_zones(...)`
- `run_bootstrap(...)`

These functions now decide which Daily zones survive.

## What changed recently
### `03b0ce0`
Persisted and surfaced selection diagnostics:
- `reaction_efficiency_score`
- `spent_zone_penalty`
- `retest_weight`
- `selection_score`
- `zone_width_bps`

### `c181917`
Added:
- `carry_score`
- `body_respect_score`
- close/body behavior diagnostics
- softer Daily accept weighting
- stronger band arbitration

### `c8c8780`
Micro-fix:
- unsaturated carry
- rebalanced Daily selection away from over-dominant carry

## Current live artifact bundle
See:
- `data/artifacts/sr/gpt54pro_review_snapshot_2026-03-09.json`
- `data/artifacts/sr/bootstrap_snapshot.json`
- `data/artifacts/sr/nearest_BTCUSDT.json`
- `data/artifacts/sr/nearest_ETHUSDT.json`
- `data/artifacts/sr/run_status.json`

## What we believe is working
- The architecture is now sane: engine / bootstrap / persistence / UI are separated.
- Diagnostics are observable end-to-end.
- `74k` became competitive and survives over `70k` in BTC Daily.
- Carry is no longer obviously pegged at 100 for everything.
- ETH is definitely running the same latest logic path as BTC.

## Remaining disagreements / failure modes
### BTC Daily
Current live majors are still not fully satisfactory:
- `59.1`
- `65.1`
- `74.5`
- `80.5`
- `87.3`
- `104.9`
- `115.6`
- `124.7`

The unresolved questions are:
1. Why does `65k` still survive too close to `60k`?
2. Why does `80.5k` still survive instead of a cleaner `74k`-only representative?
3. Why is the upper band still not clean between `98k / 104k / 108k / 115k`?
4. Is `124.7k` over-selected due to current upper-band logic?

### ETH Daily
We intentionally do **not** want ETH-specific hand-fitting yet.
ETH should be used as a blind validation case for whether the metrics generalize.

## What we want from GPT 5.4 Pro
Please review the current design and answer:
1. Are the current scoring and selection layers conceptually correct for multi-pair Daily-major S/R?
2. Are we missing a more principled representation of:
   - band competition,
   - shelf carry / excursion,
   - close/body respect,
   - zone fragmentation/chop?
3. Is the current separation between:
   - per-zone scoring,
   - retest weighting,
   - local-band arbitration,
   - final display selection
   the right architecture?
4. What generic rule changes would you propose **without introducing symbol-specific bias**?
5. If you were redesigning this for scale across 100s of pairs, what would you simplify or restructure now before more tuning?

## Strong preference for the review
Please do **not** answer with pair-specific overrides or manual level curation.
We want:
- generic rule changes,
- architecture changes,
- metric design fixes,
- or validation methodology improvements.

## Suggested review framing
Treat BTC only as a **diagnostic failure-mode case**, not as an answer key.
Treat ETH as a **blind sanity case**.
The goal is to avoid a whack-a-mole tuning process across dozens of charts.
