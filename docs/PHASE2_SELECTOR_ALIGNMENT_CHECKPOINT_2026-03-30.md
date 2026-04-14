# Phase 2 Selector Alignment Checkpoint — 2026-03-30

Status: post-implementation checkpoint for the selector-alignment stream

## Scope completed

- T1 selector doctrine audit -> code mapping
- T2 shared interval/neighborhood primitives
- T3 4H same-side representative rewrite
- T4 provenance-aware competition bias
- T5 authoritative-view naming cleanup
- T6 selector trace enrichment
- T7 BTC/ETH rerun + refreshed artifacts

## Validation

```bash
python3 -m pytest -q tests/test_pair_analytics.py tests/test_zone_engine_v3.py tests/test_sr_authoritative_levels_ui.py tests/test_sr_shadow_authoritative_view.py
```

- result: **28 passed**

## Artifact refresh

```bash
python3 -m liquidsniper.ops.sr_bootstrap --shadow-v3 --symbols BTCUSDT,ETHUSDT
```

- result: `{"ok": true, "symbols": ["BTCUSDT", "ETHUSDT"]}`

## Key behavioral outcome

- Daily behavior was preserved.
- 4H same-side ladders were materially decluttered by interval-aware neighborhood competition.
- Surviving 4H representatives now carry demotion traces for nearby same-side levels.

## Before vs after: 4H authoritative counts

| Symbol | 4H group | 2026-03-25 | 2026-03-30 | Delta |
| --- | --- | ---: | ---: | ---: |
| BTCUSDT | below_price | 3 | 2 | -1 |
| BTCUSDT | contains_price | 0 | 0 | +0 |
| BTCUSDT | above_price | 9 | 4 | -5 |
| ETHUSDT | below_price | 2 | 2 | +0 |
| ETHUSDT | contains_price | 0 | 0 | +0 |
| ETHUSDT | above_price | 10 | 4 | -6 |

## BTCUSDT current state

- last price: `69,679`
- **1D** selector surface: `daily_major`
  - `below_price` count: **6**
    - `BTCUSDT:1D:base:371:support` | role=`support` | rank=`6` | bounds `17,618 -> 17,809 -> 18,000` | reason=`kept: daily major anchor after local-band selection`
    - `BTCUSDT:1D:base:305:resistance` | role=`support` | rank=`3` | bounds `20,399.1 -> 20,937.5 -> 21,475.9` | reason=`kept: daily major anchor after local-band selection`
    - `BTCUSDT:1D:base:223:resistance` | role=`support` | rank=`7` | bounds `24,095.2 -> 24,650.1 -> 25,205` | reason=`kept: daily major anchor after local-band selection`
  - `contains_price` count: **0**
  - `above_price` count: **2**
    - `BTCUSDT:1D:base:1201:support` | role=`resistance` | rank=`5` | bounds `83,957.96 -> 84,809.48 -> 85,661` | reason=`kept: daily major anchor after local-band selection`
    - `BTCUSDT:1D:base:1280:support` | role=`resistance` | rank=`4` | bounds `107,255.7 -> 108,516.75 -> 109,777.8` | reason=`kept: daily major anchor after local-band selection`

- **4H** selector surface: `operational_4h`
  - `below_price` count: **2**
    - `BTCUSDT:4H:2:62760.15` | role=`support` | rank=`3` | bounds `62,595.27 -> 62,760.15 -> 62,925.03` | cluster=`1` | reason=`kept: representative of same-side local neighborhood`
    - `BTCUSDT:4H:base:696:resistance` | role=`support` | rank=`4` | bounds `67,187.8 -> 67,881.76 -> 68,451.18` | cluster=`2` | demoted=`BTCUSDT:4H:3:65832.89` | reason=`kept: representative of same-side local neighborhood`
  - `contains_price` count: **0**
  - `above_price` count: **4**
    - `BTCUSDT:4H:6:72602.9` | role=`resistance` | rank=`5` | bounds `72,413.96 -> 72,602.9 -> 72,791.84` | cluster=`3` | demoted=`BTCUSDT:4H:5:70716.79, BTCUSDT:4H:7:74777.0` | reason=`kept: representative of same-side local neighborhood`
    - `BTCUSDT:4H:structure:flip_anchor:141:215:support` | role=`resistance` | rank=`6` | bounds `79,855.82 -> 81,344.79 -> 82,938.3` | cluster=`1` | reason=`kept: representative of same-side local neighborhood`
    - `BTCUSDT:4H:base:485:resistance` | role=`resistance` | rank=`1` | bounds `93,206.8 -> 95,033.68 -> 96,559.72` | cluster=`9` | demoted=`BTCUSDT:4H:10:85820.37, BTCUSDT:4H:base:359:support, BTCUSDT:4H:structure:bos_anchor:429:461:support, BTCUSDT:4H:structure:bos_anchor:550:555:resistance` | reason=`kept: representative of same-side local neighborhood`

## ETHUSDT current state

- last price: `2,024.86`
- **1D** selector surface: `daily_major`
  - `below_price` count: **2**
    - `ETHUSDT:1D:structure:flip_anchor:168:468:support` | role=`support` | rank=`6` | bounds `881 -> 983.81 -> 1,086.62` | reason=`kept: daily major anchor after local-band selection`
    - `ETHUSDT:1D:base:1202:support` | role=`support` | rank=`3` | bounds `1,562.87 -> 1,610.85 -> 1,658.83` | reason=`kept: daily major anchor after local-band selection`
  - `contains_price` count: **2**
    - `ETHUSDT:1D:base:1216:support` | role=`containing` | rank=`1` | bounds `1,781.42 -> 1,827.63 -> 1,873.85` | reason=`kept: daily major anchor after local-band selection`
    - `ETHUSDT:1D:base:1177:resistance` | role=`containing` | rank=`2` | bounds `2,006.02 -> 2,011.01 -> 2,016` | reason=`kept: daily major anchor after local-band selection`
  - `above_price` count: **4**
    - `ETHUSDT:1D:structure:bos_anchor:933:946:resistance` | role=`resistance` | rank=`5` | bounds `3,439.6 -> 3,501.3 -> 3,563` | reason=`kept: daily major anchor after local-band selection`
    - `ETHUSDT:1D:structure:bos_anchor:1067:1068:support` | role=`resistance` | rank=`7` | bounds `3,500.22 -> 3,572.01 -> 3,643.8` | reason=`kept: daily major anchor after local-band selection`
    - `ETHUSDT:1D:structure:flip_anchor:801:864:resistance` | role=`resistance` | rank=`4` | bounds `3,980.39 -> 4,036.53 -> 4,092.66` | reason=`kept: daily major anchor after local-band selection`

- **4H** selector surface: `operational_4h`
  - `below_price` count: **2**
    - `ETHUSDT:4H:2:1827.637` | role=`support` | rank=`3` | bounds `1,813.08 -> 1,827.64 -> 1,842.19` | cluster=`1` | reason=`kept: representative of same-side local neighborhood`
    - `ETHUSDT:4H:base:696:resistance` | role=`support` | rank=`5` | bounds `1,935.03 -> 1,972.06 -> 2,014.91` | cluster=`2` | demoted=`ETHUSDT:4H:3:1921.103` | reason=`kept: representative of same-side local neighborhood`
  - `contains_price` count: **0**
  - `above_price` count: **4**
    - `ETHUSDT:4H:structure:bos_anchor:587:595:resistance` | role=`resistance` | rank=`4` | bounds `2,149.65 -> 2,293.69 -> 2,402.4` | cluster=`3` | demoted=`ETHUSDT:4H:5:2084.94, ETHUSDT:4H:7:2240.2` | reason=`kept: representative of same-side local neighborhood`
    - `ETHUSDT:4H:structure:flip_anchor:141:215:support` | role=`resistance` | rank=`6` | bounds `2,622.87 -> 2,665.36 -> 2,713.35` | cluster=`2` | demoted=`ETHUSDT:4H:12:2779.169` | reason=`kept: representative of same-side local neighborhood`
    - `ETHUSDT:4H:base:525:resistance` | role=`resistance` | rank=`2` | bounds `2,920.7 -> 2,960.84 -> 3,015.74` | cluster=`11` | demoted=`ETHUSDT:4H:13:2892.824, ETHUSDT:4H:base:385:support, ETHUSDT:4H:base:232:support, ETHUSDT:4H:base:359:support` | reason=`kept: representative of same-side local neighborhood`

## Interpretation

- **BTC 4H:** the above-price ladder is no longer a nine-level staircase; it now resolves to four primary resistance neighborhoods, with subordinate same-side levels retained as demotion metadata.
- **ETH 4H:** the above-price ladder is reduced from ten visible levels to four primary resistance neighborhoods, again with subordinate members preserved in cluster metadata.
- **1D:** Daily macro/core presentation remains intact; this tranche did not flatten Daily into a proximity-driven surface.

## Human test recommendation

This is the correct point for chart validation to resume.
Review against the live UI / refreshed authoritative snapshot and focus on:
- whether the surviving 4H representatives feel like real tactical neighborhoods
- whether any merged same-side neighborhoods now look over-collapsed
- whether Daily remains stable and non-noisy while 4H becomes more readable

## Artifacts

- `docs/PHASE2_SELECTOR_ALIGNMENT_IMPLEMENTATION_PACKET_2026-03-30.md`
- `docs/PHASE2_SELECTOR_ALIGNMENT_AUDIT_2026-03-30.md`
- `data/artifacts/sr/shadow/v3/bootstrap_snapshot.json`
- `data/artifacts/sr/shadow/v3/nearest_BTCUSDT.json`
- `data/artifacts/sr/shadow/v3/nearest_ETHUSDT.json`
- `data/artifacts/sr/shadow/v3/run_status.json`
