# Legacy Surfaces Status

Date: 2026-04-19, updated 2026-04-20  
Status: path-stable legacy surfaces identified in the first archive pass, selective artifact cleanup completed in the second pass, and first code relocation completed in pass 3

This note explains which non-core surfaces are still present in the repo even after the first archive PR, and why they were not moved yet.

---

## Why these surfaces were not moved yet

The first archive pass moved obvious legacy **docs** out of the top-level `docs/` surface.

It did **not** move several code and artifact directories yet, because live code, tests, or tooling still point at those paths directly. Moving them in the same pass would create unnecessary breakage.

So for now, these surfaces are treated as:
- legacy
- non-core to current product direction
- path-stable until a later dedicated migration pass

---

## Legacy code surfaces still present

### `liquidsniper/ingestor/`
Why still present:
- historical Telegram/Mobchart ingestion code still exists
- migrations and parser surfaces still reflect that origin

Why legacy:
- Telegram/Mobchart ingestion is no longer the center of the repo
- current active direction is canonical feed -> Surveyor packet -> Arbiter

Update on 2026-04-20:
- canonical implementation moved to `legacy/telegram_ingestor/`
- `liquidsniper/ingestor/` remains as a compatibility shim for existing entrypoints

### `tradingview/`
Why still present:
- tooling and historical parity work still refer to this path
- related scripts/docs/tests still exist

Why legacy:
- TradingView parity/automation is no longer a first-class product center

### `tools/strategy_sweep/`
Why still present:
- historical sweep/export tooling remains path-coupled to TradingView-era work

Why legacy:
- useful as historical reference, but not part of the core Surveyor / Arbiter architecture

### Paper-runtime surfaces in `liquidsniper/core/`, `liquidsniper/ops/`, and `liquidsniper/debug/`
Why still present:
- tests and modules still point to paper runtime state/artifact paths

Why legacy:
- paper-runtime behavior is no longer the repo’s center, even if some code remains recoverable or reference-worthy

---

## Legacy artifact surfaces still present

### `artifacts/paper_mvp/`
Still referenced by:
- paper artifact helpers
- paper daemon/debug code
- multiple tests and runbooks

### `artifacts/paper_soak/`
Historical-only paper-run evidence.

Update on 2026-04-20:
- moved to `artifacts/archive/2026-04-20-second-pass/paper-soak/`
- no live code-path dependency was kept on the original location

### `artifacts/tradingview/`
Still referenced by:
- TradingView snapshot/bootstrap tools
- TV artifact helpers/tests

Why still present:
- live helper/test/tool paths still point here directly

### `artifacts/validation/`
Still referenced by:
- validation sweep tooling and related runbooks

Why still present:
- current tooling defaults still write here

---

## What happened across passes 1 through 3

### First archive pass
Moved out of top-level `docs/`:
- Telegram/Mobchart legacy docs
- paper-runtime legacy docs
- TradingView legacy docs

### Second archive pass
Archived selected artifact surfaces that were safe to move without breaking path-coupled code:
- `artifacts/paper_soak/` -> `artifacts/archive/2026-04-20-second-pass/paper-soak/`
- historical `tools/strategy_sweep/outputs/*` -> `artifacts/archive/2026-04-20-second-pass/strategy-sweep-outputs/`
- top-level historical artifact notes -> `artifacts/archive/2026-04-20-second-pass/legacy-notes/`

### Third pass
Relocated the first legacy code surface behind a compatibility shim:
- implementation moved from `liquidsniper/ingestor/main.py` to `legacy/telegram_ingestor/main.py`
- compatibility kept at `liquidsniper/ingestor/`

Still left in place for later migration:
- legacy code dirs
- legacy artifact dirs with live path references

---

## Recommended next migration pass

A later code cleanup pass should:
1. inventory direct path dependencies in code/tests/tools
2. decide which legacy code remains worth keeping at all
3. either:
   - move those surfaces under explicit `legacy/` or `archive/` paths and update references, or
   - delete them if no longer justified
4. keep Surveyor / Arbiter imports and UI/feed paths green throughout
5. start with `liquidsniper/ingestor/`, `tradingview/`, `tools/strategy_sweep/`, and paper-runtime modules
