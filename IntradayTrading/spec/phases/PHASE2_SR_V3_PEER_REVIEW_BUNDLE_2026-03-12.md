# Phase 2 S/R V3 Peer Review Bundle — 2026-03-12

Branch: `phase2-zone-engine-v3`
Commit anchor: `c9a487d`

## Review objective

Assess whether the current Phase 2 shadow path is moving in the right doctrinal direction **without** collapsing back into selector hackery.

This is **not** a request for another generic tuning pass.

The key question is:

> After Fix A (role-aware nearest-four) and Fix B (base-family hardening + merge compatibility), is the remaining problem correctly identified as **provenance-aware Daily promotion** plus **still-incomplete structure-family truth**?

## Minimal required anchor files

Only anchor on these unless you truly need more:

1. `docs/phase2_zone_engine_v3_steering_packet.md`
   - architecture intent, migration/shadow-mode posture, explicit non-goals
2. `docs/zone_schema_v2.md`
   - zone contract and MAP vs LIVE semantics
3. `docs/selector_policy_v2.md`
   - Daily / 4H / nearest-four policy separation
4. `liquidsniper/core/zone_engine_v3.py`
   - current V3 shadow implementation and recent fixes
5. `liquidsniper/core/sr_engine_v2.py`
   - treat as reaction-family baseline, not final zone truth

## Files you should *not* need up front

Avoid pulling broad repo context unless necessary:
- `liquidsniper/web/app.py` (UI only)
- broad strategy docs unrelated to V3 shadow behavior
- full repo history

## Current implementation posture

### What is intentionally true
- `sr_engine_v2` is being treated as **reaction-family v1**.
- `zone_engine_v3.py` is the shadow seam for:
  - structure candidates
  - base/shelf candidates
  - reaction candidates
  - merge/arbitration
  - scoring
  - Daily / operational / nearest-four selection
- default path is still baseline; V3 remains shadow/observability-first.

### Fixes already applied

#### Fix A — shadow nearest-four role hygiene
Problem fixed:
- overlapping shadow zones with explicit `zone_kind` were being slotted as both supports and resistances because the generic baseline nearest selector was too role-agnostic.

Change made:
- V3 now uses a **role-aware nearest-four wrapper** before ranking.

Result:
- support/resistance slot crossing is fixed.

#### Fix B — base-family hardening
Problem addressed:
- the initial base detector overproduced narrow-window shelves and polluted Daily/near-price surfaces.

Changes made:
- base candidate generation now requires more than compression:
  - tighter compression limit
  - repeated overlap links
  - edge-touch participation
  - close-based breakout beyond the shelf
- merge compatibility now allows nearby base `support/resistance` zones to merge with reaction/structure `mixed` zones when they are actually compatible.

Result:
- fake shelf flood reduced materially
- some previously blocked confluence now appears in merged Daily majors

## Current live evidence (post Fix A + Fix B)

### BTCUSDT

Baseline:
- total zones: `15`
- 1D kept: `3`
- 4H kept: `12`

Shadow:
- total zones: `20`
- 1D kept: `8`
- 4H kept: `12`

Shadow candidate counts:
- 1D: `structure=17`, `base=34`, `reaction=17`, `merged=25`
- 4H: `structure=22`, `base=12`, `reaction=22`, `merged=22`

Shadow nearest-four:
- nearest support: `4H support 65,182.46 → 66,483.32` `['reaction','structure']`
- next support: `1D support 60,180.0 → 63,470.5` `['base']`
- nearest resistance: `4H mixed 72,413.96 → 72,791.84` `['reaction','structure']`
- next resistance: `4H resistance 92,160.1 → 93,400.0` `['base']`

Shadow 1D majors:
- still mixed quality
- several levels now show `['base','reaction','structure']`
- but some majors remain **pure base-only**

Representative majors:
- `BTCUSDT:1D:base:305:resistance` -> `['base','reaction','structure']`
- `BTCUSDT:1D:base:529:support` -> `['base']`
- `BTCUSDT:1D:base:587:resistance` -> `['base']`
- `BTCUSDT:1D:base:14:resistance` -> `['base','reaction','structure']`
- `BTCUSDT:1D:base:781:support` -> `['base','reaction','structure']`
- `BTCUSDT:1D:base:860:support` -> `['base']`

### ETHUSDT

Baseline:
- total zones: `17`
- 1D kept: `5`
- 4H kept: `12`

Shadow:
- total zones: `19`
- 1D kept: `7`
- 4H kept: `12`

Shadow candidate counts:
- 1D: `structure=16`, `base=18`, `reaction=16`, `merged=20`
- 4H: `structure=23`, `base=10`, `reaction=23`, `merged=25`

Shadow nearest-four:
- nearest support: `4H support 1,906.44 → 1,935.766` `['reaction','structure']`
- next support: `4H support 1,813.084 → 1,842.19` `['reaction','structure']`
- nearest resistance: `1D resistance 1,976.73 → 2,157.648` `['base','reaction','structure']`
- next resistance: `4H mixed 2,149.646 → 2,165.576` `['reaction','structure']`

Shadow 1D majors:
- healthier than BTC
- includes both reaction/structure and base+reaction+structure zones
- still has at least one pure base-only major

Representative majors:
- `ETHUSDT:1D:1:1023.199` -> `['reaction','structure']`
- `ETHUSDT:1D:base:1202:support` -> `['base','reaction','structure']`
- `ETHUSDT:1D:base:586:resistance` -> `['base']`
- `ETHUSDT:1D:base:1177:resistance` -> `['base','reaction','structure']`
- `ETHUSDT:1D:13:4157.315` -> `['reaction','structure']`

## What seems fixed vs still open

### Fixed enough for this review pass
- nearest-four role crossing bug
- gross base-candidate flood
- blocked merge confluence between base and nearby mixed reaction/structure zones

### Still open
- some **pure base-only Daily majors** still survive too easily
- structure family is still scaffolded / not fully doctrinally trustworthy
- Daily promotion logic may still need **generic provenance-aware preference** for corroborated zones over pure base-only shelves

## Review question

Please answer these specifically:

1. Is the current direction **architecturally correct enough to continue**, or is there still a conceptual misalignment that should be corrected before more implementation?
2. Is the remaining problem correctly framed as:
   - **provenance-aware Daily promotion**, and
   - **still-incomplete structure-family truth**
3. What is the **smallest next generic change** that would reduce pure base-only Daily winners without falling back into selector spaghetti or symbol-specific behavior?
4. Should the next implementation tranche be:
   - provenance-aware Daily promotion first,
   - or deeper structure-family work first,
   - or local ATR / lifecycle semantics first?

## Optional raw artifacts (only if needed)

If you need raw evidence beyond the summary above, inspect only these:
- baseline snapshot: `/data/artifacts/sr/bootstrap_snapshot.json`
- shadow snapshot: `/data/artifacts/sr/shadow/v3/bootstrap_snapshot.json`
- baseline nearest BTC: `/data/artifacts/sr/nearest_BTCUSDT.json`
- shadow nearest BTC: `/data/artifacts/sr/shadow/v3/nearest_BTCUSDT.json`
- baseline nearest ETH: `/data/artifacts/sr/nearest_ETHUSDT.json`
- shadow nearest ETH: `/data/artifacts/sr/shadow/v3/nearest_ETHUSDT.json`

Do not broaden the file set unless you can explain why it is necessary.
