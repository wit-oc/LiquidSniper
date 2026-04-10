# Phase 2 ETH Daily Coverage Finalization Checkpoint — 2026-04-01

Status: post-finalization local checkpoint  
Branch: `phase2-zone-engine-v3`

## Scope completed

- Added a final Daily-major coverage refinement so intermediate upside regimes can survive when the Daily map would otherwise jump too far upward from the containing / near-current region.
- Fixed the Daily coverage seam to classify coverage gaps using the **macro envelope** rather than the narrowed display core.
- Re-ran BTC/ETH shadow artifacts and refreshed the live SR container.

## Key implementation note

The initial ETH-focused patch did not change the live map because the coverage hook was evaluating selected Daily zones by `core_*` display bounds. That caused ETH's containing Daily band to be seen as `below_price`, so the intermediate-upside branch never executed.

This checkpoint fixes that by using the macro interval (`zone_low/zone_high/zone_mid`) for Daily coverage-gap classification while still preserving the narrowed display core for operator rendering.

## Validation

```bash
python3 -m pytest -q tests/test_zone_engine_v3.py tests/test_pair_analytics.py tests/test_sr_authoritative_levels_ui.py tests/test_sr_shadow_authoritative_view.py
```

Result: targeted suite passed.

## Artifact refresh

```bash
python3 -m liquidsniper.ops.sr_bootstrap --shadow-v3 --symbols BTCUSDT,ETHUSDT
```

Result:

```json
{"ok": true, "symbols": ["BTCUSDT", "ETHUSDT"]}
```

## Live container refresh

```bash
docker compose -f docker-compose.sr.yml up -d --build
```

Verification:
- `liquidsniper-sr-web` up
- `http://127.0.0.1:8501/` -> `HTTP/1.1 200 OK`
- `liquidsniper-sr-worker` -> `Exited (0)` after bootstrap

## Outcome summary

## BTC

BTC remained stable through the ETH finalization pass:
- 1D below price: 5
- 1D contains price: 1
- 1D above price: 2
- 4H structure remained unchanged

Notable point:
- the BTC Daily current-regime coverage anchor around `68.4k -> 68.7k` remains present
- no regression back into the earlier `50k–83k` Daily void

## ETH

ETH Daily now includes the previously missing intermediate upside regime:
- `ETHUSDT:1D:structure:bos_anchor:1288:1291:support`
- displayed around `2906.0 -> 2932.02 -> 2958.04`
- selector reason: `kept: daily intermediate upside coverage anchor`

Current ETH 1D surface:
- below price: 1
- contains price: 1
- above price: 3

This restores the missing ~2800 / low-2900 regime without reopening the earlier Daily clutter problems.

## ETH 4H decision

ETH 4H below-price supports still surface around:
- `1813 -> 1828 -> 1842`
- `1935 -> 1972 -> 2015`

Decision for this checkpoint:
- **leave them as-is for now**

Reason:
- they still read as two distinct support neighborhoods
- the stronger remaining defect was the missing Daily intermediate upside regime, which is now resolved
- further compression here would be a polish pass, not a finish-line blocker

## Final recommendation

This looks finish-line close.

Recommended next step:
- do human review on the updated live map
- if no new issues appear, checkpoint / commit this finalization tranche and treat the ETH 4H pair as acceptable pending any last subjective objections
