# Second Archive Pass, Code and Artifact Triage

Date: 2026-04-20  
Status: first code/artifact-focused cleanup pass after the doc archive pass

This note records the actual keep/archive posture used for the second archive pass.

---

## Goal

Make the repo surface tell the truth more clearly without breaking live Surveyor / Arbiter paths.

This pass therefore splits legacy surfaces into three buckets:
- **Keep as core**
- **Keep in place, but explicitly legacy/path-stable**
- **Archive now**

---

## 1) Keep as core

These remain part of the active repo center:

### Surveyor / feed / packet core
- `liquidsniper/core/surveyor_snapshot.py`
- `liquidsniper/ops/surveyor_feed_refresh.py`
- `liquidsniper/web/app.py`
- `liquidsniper/core/db.py`
- `liquidsniper/core/market_data.py`
- `liquidsniper/core/market_scheduler.py`
- `IntradayTrading/engine/surveyor_packet.py`
- `IntradayTrading/engine/phase1_contract.py`
- `IntradayTrading/engine/fib_anchors.py`
- `IntradayTrading/engine/fib_context.py`
- `IntradayTrading/engine/dynamic_levels.py`

### Current architecture / refocus docs
- `docs/INTRADAY_REVISIT_SURVEYOR_ARBITER_ARCHITECTURE_V1.md`
- `docs/SURVEYOR_ARBITER_REPO_REFOCUS_PLAN_2026-04-19.md`
- `docs/LEGACY_SURFACES_STATUS_2026-04-19.md`

---

## 2) Keep in place, but explicitly legacy/path-stable

These are not part of the desired long-term center, but moving them now would create unnecessary breakage.

### `liquidsniper/ingestor/`
Why still in place:
- migrations and parser/test surfaces still reference the Telegram-era origin
- existing entrypoints still targeted this package path during the second pass

Current posture during pass 2:
- legacy, non-core, path-stable for now

Update after pass 3:
- implementation moved to `legacy/telegram_ingestor/`
- `liquidsniper/ingestor/` now remains only as a compatibility shim

### `tradingview/`
Why still in place:
- historical parity work, tests, and tooling still refer to this path

Current posture:
- legacy, non-core, path-stable for now

### `tools/strategy_sweep/`
Why still in place:
- tests still import the sweep engine directly
- scripts still default to this path

Current posture:
- legacy, non-core, path-stable for now

### Paper-runtime code in `liquidsniper/core`, `liquidsniper/ops`, `liquidsniper/debug`
Why still in place:
- many tests and artifact helpers still reference these modules and paths

Current posture:
- legacy, non-core, path-stable for now

### `artifacts/paper_mvp/`, `artifacts/tradingview/`, `artifacts/validation/`
Why still in place:
- still referenced by tests, helpers, or active tooling defaults

Current posture:
- legacy artifact buckets retained in place pending a later migration pass

---

## 3) Archived now in this pass

These were judged safe to move immediately.

### Historical paper soak artifacts
Moved from:
- `artifacts/paper_soak/`

Moved to:
- `artifacts/archive/2026-04-20-second-pass/paper-soak/`

Reason:
- historical evidence only
- no live code-path dependency found during this pass

### Historical strategy-sweep generated outputs
Moved from:
- `tools/strategy_sweep/outputs/*`

Moved to:
- `artifacts/archive/2026-04-20-second-pass/strategy-sweep-outputs/`

Reason:
- generated historical output, not required for tests/imports
- active tool default can keep writing to `tools/strategy_sweep/outputs/`

### Historical top-level artifact notes
Moved from:
- `artifacts/daily_swing_v1_tv_alpha_scaffold_2026-02-26.md`
- `artifacts/swing_sr_zone_engine_pass1_pass2_2026-02-27.md`

Moved to:
- `artifacts/archive/2026-04-20-second-pass/legacy-notes/`

Reason:
- historical notes, not active runtime inputs

---

## 4) Recommended next pass

The next cleanup pass should focus on **code relocation or deletion**, not more docs.

Priority order after the first pass-3 relocation:
1. `tradingview/`
2. `tools/strategy_sweep/`
3. paper-runtime modules under `liquidsniper/core`, `liquidsniper/ops`, `liquidsniper/debug`

That pass should decide, directory by directory:
- keep
- move under explicit `legacy/`
- delete
- or shim temporarily

without regressing Surveyor UI/feed paths.
