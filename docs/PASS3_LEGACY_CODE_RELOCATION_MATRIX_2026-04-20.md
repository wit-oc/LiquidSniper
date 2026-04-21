# Pass 3, Legacy Code Relocation Matrix

Date: 2026-04-20  
Status: first real code relocation pass after the doc and artifact cleanup passes

This pass moves the smallest legacy implementation that could be relocated
without breaking existing entrypoints: the Telegram / Mobchart ingestor.

---

## What changed in this pass

### Completed relocation

Moved implementation from:
- `liquidsniper/ingestor/main.py`

Moved implementation to:
- `legacy/telegram_ingestor/main.py`

Compatibility kept at:
- `liquidsniper/ingestor/main.py`
- `liquidsniper/ingestor/__init__.py`

Compatibility rule:
- old entrypoint remains valid: `python -m liquidsniper.ingestor.main ...`
- the old package now acts as a thin shim, not the canonical implementation home

Why this was the right first move:
- only a few live references still target the old path directly
- the functionality is clearly legacy relative to Surveyor / Arbiter
- a shim preserves `Makefile`, `docker-compose`, and `tools/smoke_runner.py`

---

## Current matrix

### Keep as core now
- `liquidsniper/core/surveyor_snapshot.py`
- `liquidsniper/ops/surveyor_feed_refresh.py`
- `liquidsniper/web/app.py`
- `IntradayTrading/engine/surveyor_packet.py`
- current Surveyor / Arbiter architecture docs and feed paths

### Relocated to explicit legacy now
- Telegram / Mobchart ingestor implementation
  - canonical implementation home: `legacy/telegram_ingestor/`
  - compatibility shim left at: `liquidsniper/ingestor/`

### Relocated to explicit legacy now
- Telegram / Mobchart ingestor implementation
  - canonical implementation home: `legacy/telegram_ingestor/`
  - compatibility shim left at: `liquidsniper/ingestor/`
- TradingView surface
  - canonical implementation home: `legacy/tradingview/`
  - compatibility kept through repo-root symlink `tradingview -> legacy/tradingview`
- Strategy sweep tooling
  - canonical implementation home: `legacy/strategy_sweep/`
  - compatibility kept through symlink `tools/strategy_sweep -> ../legacy/strategy_sweep`

### Keep path-stable for a later relocation pass
- paper-runtime modules under `liquidsniper/core`, `liquidsniper/ops`, `liquidsniper/debug`
  - still heavily referenced by tests, helpers, and artifact persistence logic
- `artifacts/paper_mvp/`, `artifacts/tradingview/`, `artifacts/validation/`
  - still referenced by current code or tooling defaults

### Delete candidate, but only after proof
- duplicated or obsolete wrapper surfaces inside `tradingview/` and `tools/strategy_sweep/`
- paper-runtime docs/tests/helpers that no longer back any retained operator path

No delete happened in this pass because the remaining candidates are still too path-coupled.

---

## Recommended next pass

1. decide whether any of the now-relocated legacy surfaces should eventually become:
   - a separate repo/tooling package,
   - a frozen archive,
   - or be retired outright
2. split paper-runtime surfaces into:
   - retained reusable primitives
   - operator-only legacy surfaces
   - delete candidates

The key rule remains: do not break Surveyor UI/feed paths just to make the tree prettier.
