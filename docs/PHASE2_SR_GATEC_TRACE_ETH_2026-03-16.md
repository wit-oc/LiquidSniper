# Gate C trace — ETH next-resistance truth (2026-03-16)

## Scope

Trace ETH resistance inventory through:
- raw candidates
- merged candidates
- Daily-major selection
- nearest ladder

Repo baseline:
- repo: `/Users/wit/.openclaw/workspace/LiquidSniper`
- branch: `phase2-zone-engine-v3`
- artifact basis: existing shadow snapshot plus direct reconstruction from `IntradayTrading/data/eth_1d_okx_ccxt_2022_to_now.csv`
- entry price used by shadow snapshot: `2024.86`

## Promotion Gate C answer

**ETH resistance truth is not primarily lost in candidate generation, merge, or Daily-major selection. The “missing next resistance” symptom appears at nearest-ladder interpretation/ranking.**

More specifically:
- 1D candidate generation produces multiple plausible above-price resistances.
- Merge preserves them as canonical confirmed zones.
- Daily-major selection still keeps several above-price 1D resistances.
- But the nearest ladder treats the large 1D resistance around `2047.17` as the active/nearest resistance because price is already inside it, then chooses a much closer 4H resistance as `next_resistance`.

So the ETH symptom is different from BTC:
- BTC lost truth in **Daily selection**.
- ETH keeps Daily resistance truth through selection, but the execution-facing **nearest ladder** surfaces a 4H next resistance instead of the next 1D major.

## Evidence chain

### 1) Raw candidate inventory exists

Direct reconstruction on ETH 1D produced:
- structure: `23`
- base: `18`
- reaction: `14`

This is not a “no ETH resistance candidates exist” situation.

### 2) Merge preserves above-price 1D resistance truth

Merged 1D confirmed zones above price included all of the following representative resistance candidates:

| zone_id | mid | kind | candidate_sources | selection_score |
|---|---:|---|---|---:|
| `ETHUSDT:1D:base:1177:resistance` | 2047.17 | resistance | base+reaction+structure | 131.7037 |
| `ETHUSDT:1D:structure:bos_anchor:1160:1164:resistance` | 2261.21 | resistance | structure | 120.4525 |
| `ETHUSDT:1D:structure:bos_anchor:11:20:resistance` | 3325.85 | resistance | structure | 121.6457 |
| `ETHUSDT:1D:structure:bos_anchor:933:946:resistance` | 3489.21 | resistance | reaction+structure | 123.8590 |
| `ETHUSDT:1D:structure:bos_anchor:3:4:resistance` | 3809.75 | resistance | structure | 121.4228 |
| `ETHUSDT:1D:structure:flip_anchor:801:864:resistance` | 4022.28 | resistance | resistance/reaction+structure | 124.2111 |
| `ETHUSDT:1D:structure:flip_anchor:1331:1405:resistance` | 4865.66 | resistance | resistance/reaction+structure | 121.0074 |

Key point:
- the “next resistance” truth clearly exists after merge;
- the important nearby resistance at `2047.17` is actually the strongest merged resistance, not a weak leftover.

### 3) Daily-major selection still keeps the 1D resistance map

The shadow-selected 1D majors for ETH include these above-price resistances:
- `ETHUSDT:1D:base:1177:resistance` @ `2047.17`
- `ETHUSDT:1D:structure:bos_anchor:933:946:resistance` @ `3489.21`
- `ETHUSDT:1D:structure:flip_anchor:801:864:resistance` @ `4022.28`
- `ETHUSDT:1D:structure:flip_anchor:1331:1405:resistance` @ `4865.66`

The full selected 1D major surface therefore still carries a valid ETH resistance ladder.

That means the Gate C trace answer for selection is:
- Did the level exist? **Yes.**
- Did merge remove it? **No.**
- Did Daily-major selection remove it? **No.**

### 4) Where the “missing next resistance” symptom actually appears

The shadow nearest ladder shows:
- nearest resistance: `ETHUSDT:1D:base:1177:resistance` @ `2047.17`
- next resistance: `ETHUSDT:4H:structure:bos_anchor:587:595:resistance` @ `2293.69`

This is the crucial distinction:
- the 1D major resistance at `2047.17` is not missing; it is being treated as the **active nearest resistance** because current price is already inside that zone;
- once that slot is consumed, the next closest aligned resistance across eligible surfaces is a **4H** zone near `2293.69`;
- therefore the ladder does **not** advance to the next 1D major resistance at `3489.21`.

So the user-observed “ETH missing next resistance” is really:
- “nearest ladder next slot is cross-timeframe and distance-first,”
- not “1D resistance truth vanished from the model.”

## What won instead

Nothing deleted the ETH 1D majors.

What happened instead is:
- the containing/nearby 1D resistance at `2047.17` took the `nearest_resistance` slot;
- the nearest ladder then picked the closer 4H resistance at `2293.69` as `next_resistance`;
- the higher 1D resistance at `3489.21` remained on the major surface, but no longer occupied the next ladder slot.

So the relevant doctrine issue is not candidate truth loss. It is **surface-to-ladder semantics**:
- active containing 1D bands
- cross-timeframe distance-first ranking
- operator expectation that “next resistance” may mean “next 1D major,” not merely “next closest aligned resistance from any eligible TF.”

## Nearest-ladder consequence

For ETH, the execution-facing ladder currently answers a different question than the operator likely intended:
- current implementation: **next closest aligned resistance across eligible TFs**
- operator expectation in this trace: **next 1D major resistance beyond the current 1D resistance band**

That is why the snapshot can look correct at the major-surface level while still feeling wrong at the nearest-ladder level.

## Closure statement for T2

ETH Gate C trace is closed enough to say:

> ETH resistance truth survives candidate generation, merge, and Daily-major selection. The apparent next-resistance gap appears in nearest-ladder semantics: the 1D resistance around 2047.17 becomes the active nearest resistance because price is already inside it, and the ladder then picks a closer 4H resistance as next instead of advancing to the next 1D major at 3489.21.

## Next implication (not executed here)

This points toward **targeted ladder/selector-surface semantics work** — especially how containing 1D resistance bands interact with cross-timeframe `next_resistance` ranking — rather than generic candidate-generation tuning.
