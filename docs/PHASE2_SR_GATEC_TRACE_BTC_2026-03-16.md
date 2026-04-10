# Gate C trace — BTC Daily selector truth (2026-03-16)

## Scope

Trace BTC upside Daily inventory through:
- raw candidates
- merged candidates
- Daily-major selection
- nearest ladder

Repo baseline:
- repo: `/Users/wit/.openclaw/workspace/LiquidSniper`
- branch: `phase2-zone-engine-v3`
- artifact basis: existing shadow snapshot plus direct reconstruction from `IntradayTrading/data/btc_1d_okx_ccxt_2022_to_now.csv`
- entry price used by shadow snapshot: `69679.0`

## Promotion Gate C answer

**BTC upside Daily truth is not primarily lost in candidate generation or merge. It is lost in Daily-major selection.**

More specifically:
- Daily candidate generation produces multiple plausible **above-price resistance** candidates.
- Merge preserves them as canonical confirmed zones.
- The Daily selector then keeps only **above-price support** zones and drops the above-price resistances.
- As a result, the nearest ladder ends up sourcing the next resistance from **4H**, not from the Daily major surface.

That satisfies the required Gate C question set:
- Did the level exist? **Yes.**
- Did merge remove it? **No.**
- Did selection remove it? **Yes.**
- What won instead, and why? **Higher-scoring above-price support zones won because the Daily selector is spatial/score driven and not role-aware for the above-price side.**

## Evidence chain

### 1) Raw candidate inventory exists

Direct reconstruction on BTC 1D produced:
- structure: `23`
- base: `34`
- reaction: `15`

This is not a “no upside candidates exist” situation.

### 2) Merge preserves upside Daily resistance truth

Merged 1D confirmed zones above price included all of the following:

| zone_id | mid | kind | candidate_sources | selection_score |
|---|---:|---|---|---:|
| `BTCUSDT:1D:structure:flip_anchor:1192:1237:support` | 76653.01 | support | reaction+structure | 121.6146 |
| `BTCUSDT:1D:base:1201:support` | 85360.48 | support | base+reaction | 126.5635 |
| `BTCUSDT:1D:structure:bos_anchor:1268:1286:support` | 97151.80 | support | structure | 120.1523 |
| `BTCUSDT:1D:structure:bos_anchor:1474:1491:resistance` | 98634.82 | resistance | reaction+structure | 123.2177 |
| `BTCUSDT:1D:structure:flip_anchor:1115:1151:resistance` | 105567.00 | resistance | structure | 118.6031 |
| `BTCUSDT:1D:base:1280:support` | 109585.40 | support | base+reaction | 127.7869 |
| `BTCUSDT:1D:structure:flip_anchor:1374:1413:resistance` | 124316.08 | resistance | reaction+structure | 123.0353 |

Key point:
- the missing-looking Daily upside resistances are **present after merge**;
- several are structure-backed and score competitively.

### 3) Selector stages remove the resistances

Above-price zones by selector stage:

#### Prefilter (`strength >= 70`)
All seven meaningful above-price Daily zones remain, including three resistances.

#### Local-band representative stage
Survivors above price:
- `76653.01` support
- `85360.48` support
- `97151.80` support
- `109585.40` support
- `124316.08` resistance

Dropped here:
- `98634.82` resistance
- `105567.00` resistance

This already shows a doctrine issue: resistance truth is being compressed away during band representation.

#### Collapse-by-distance stage
Survivors above price:
- `85360.48` support
- `109585.40` support

Dropped here:
- `76653.01` support
- `97151.80` support
- `124316.08` resistance

At this point **all above-price resistances are gone**.

#### Final spatially-diverse selector output
Selected above-price Daily majors:
- `BTCUSDT:1D:base:1201:support` @ `85360.48`
- `BTCUSDT:1D:base:1280:support` @ `109585.40`

Selected above-price Daily resistances:
- **none**

## What won instead

The winners were not stronger Daily resistances. The winners were two **above-price support** zones:
- `BTCUSDT:1D:base:1201:support` (`selection_score 126.5635`)
- `BTCUSDT:1D:base:1280:support` (`selection_score 127.7869`)

Both are base+reaction fused zones with very high scores, so a score-first / distance-collapse path naturally preserves them.

The problem is doctrinal, not arithmetic:
- the selector is not adequately separating **above-price resistance-map duty** from generic high-score zone retention;
- so above-price support zones can occupy the scarce Daily-major slots that operators intuitively expect to be resistance inventory.

## Nearest ladder consequence

The shadow nearest ladder for BTC shows:
- nearest resistance: `BTCUSDT:4H:6:72602.9`
- next resistance: `BTCUSDT:4H:structure:bos_anchor:550:555:resistance` @ `90542.43333333`

That is the practical downstream consequence:
- because Daily selection emitted **no above-price Daily resistances**, the execution-facing nearest ladder pulls resistance truth from **4H** instead.

So the “BTC sparse upside Daily majors” symptom is real, but the trace says:
- **generation: not the main loss point**
- **merge: not the loss point**
- **selection: yes, this is the loss point**

## Closure statement for T1

BTC Gate C trace is closed enough to say:

> BTC upside Daily resistance truth survives into the merged canonical set, but the Daily-major selector drops it during band/collapse selection because above-price support zones win the generic score-and-distance competition. The nearest ladder then falls back to 4H resistance inventory.

## Next implication (not executed here)

This points toward **targeted selector-model work**, specifically role-aware / surface-aware Daily selection, rather than generic candidate-generator tuning.
