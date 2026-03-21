# HTF Fib + LTF CHoCH Strategy Plan

Status: DRAFT  
Date: 2026-03-15  
Base structure source: `IntradayTrading/pine/HTF_Phase1_Structure_v3_3.pine`

## Goal

Build a TradingView strategy that:
- uses **HTF structure** as directional and POI context,
- builds **retracement zones** from HTF structural legs,
- waits for **LTF reversal confirmation** inside those zones,
- can be backtested without obvious hindsight leakage.

This is practical to codify in Pine, but only if the strategy is treated as a
strict **state machine** and the first version is intentionally narrow.

## Core thesis

Trade only when all three layers agree:

1. **HTF permission**
   - the selected HTF structure timeframe defines allowed direction and where price should react.
2. **POI qualification**
   - price must enter a retracement zone built from an HTF structural leg.
3. **LTF trigger**
   - a local CHoCH in the intended direction must occur after the zone touch.

The strategy should not enter merely because price is in a fib band. The fib
band is a watch condition, not the trigger.

## What should come from the v3.3 structure engine

The existing indicator already gives the right foundation:
- `regimeDir`
- `regimeConf`
- structural anchors:
  - bullish anchor = `protectedLow`
  - bearish anchor = `protectedHigh`
- last structural continuation anchor:
  - `lastBosAnchorPrice`
  - `lastBosDir`
- flip events:
  - `evChoch`
  - `evBos`

For strategy use, the important interpretation is:

- **HTF CHoCH** = the active HTF directional thesis is broken
- **HTF BoS** = the active HTF trend continues
- **active HTF impulse leg** = the directional leg currently being measured for retracement

So the zone logic should be:

- choose one **HTF structure timeframe**
- track the active impulse leg on that timeframe
- project a user-defined fib retracement band from that leg
- when price enters that band, begin waiting for reversal confirmation on a separate LTF

That means fib zones should be derived from the **active HTF impulse leg**,
not from arbitrary recent highs/lows.

## Timeframe model

This strategy should use exactly two structure timeframes:

- **External Structure TF (HTF)**
  - defines external structure and the impulse leg used for the fib retracement zone
  - examples: `1W`, `1D`, `4H`
- **Internal Structure TF (LTF)**
  - defines internal reversal confirmation after price enters the HTF fib zone
  - examples: `15m`, `5m`, `1m`

The intended abstraction is:

- HTF external structure contains the internal structure of lower timeframes
- HTF selects the directional thesis and retracement zone
- LTF confirms reversal with the same structure semantics as the HTF engine

There should be no third decision timeframe in v1.

Recommended implementation anchor:
- chart timeframe = **Internal Structure TF (LTF)**
- request HTF structure through `request.security()`
- run the same v3.3 structure semantics for both HTF and LTF

This is the cleanest design because:
- entries and exits naturally execute on the LTF bar stream,
- the HTF only needs to provide external state and zone coordinates,
- state coordination is easier than trying to run an LTF engine from an HTF chart.

## Setup definition

### Bullish setup

1. The selected HTF structure is bullish.
2. A valid bullish fib zone exists from the current HTF impulse leg.
4. Price trades into the discount band.
5. After the touch, the Internal Structure TF prints bullish CHoCH.
6. Entry occurs on trigger confirmation.

### Bearish setup

Mirror logic:

1. The selected HTF structure is bearish.
2. Valid bearish fib zone exists from the current HTF impulse leg.
4. Price trades into the premium band.
5. After the touch, the Internal Structure TF prints bearish CHoCH.
6. Entry occurs on trigger confirmation.

## How to define the HTF impulse leg without hindsight

This is the critical part.

For the selected HTF, maintain a **current active impulse leg**:

- **Bullish leg**
  - `leg_low` = the bullish structural anchor low that underpins the current bullish regime
  - `leg_high` = the highest traded price achieved since that anchor while HTF structure remains bullish
- **Bearish leg**
  - `leg_high` = the bearish structural anchor high that underpins the current bearish regime
  - `leg_low` = the lowest traded price achieved since that anchor while HTF structure remains bearish

Then derive the retracement zone:

- bullish discount zone:
  - `fib_618 = leg_high - (leg_high - leg_low) * 0.618`
  - `fib_786 = leg_high - (leg_high - leg_low) * 0.786`
- bearish premium zone:
  - `fib_618 = leg_low + (leg_high - leg_low) * 0.618`
  - `fib_786 = leg_low + (leg_high - leg_low) * 0.786`

Important rule:
- only use the leg that was known **at that time**
- never rebuild a zone from a future extreme
- keep extending the active leg while the HTF thesis remains valid

Operationally:
- maintain one active bullish leg and one active bearish leg framework on the selected HTF
- extend the active directional extreme while the HTF regime remains intact
- invalidate the active directional zone when opposite HTF CHoCH occurs
- start watching the opposite directional leg after the regime flips

## Practical POI rules for v1

The first version should avoid “any touch means valid”.

Use:
- one primary zone source: the selected `structure_tf`
- entry allowed only if price is inside the active retracement band from that HTF
- optional confluence bonus if a higher macro timeframe agrees

Optional filters:
- max zone age in HTF bars
- first-touch only
- reject if approach is already impulsively reversing before entry trigger

## LTF trigger definition

There are two realistic options.

Use the exact v3.3 structure semantics on the Internal Structure TF.

That means the reversal trigger should not be a proxy. It should be the same
structure model producing a genuine internal CHoCH after price has entered the
HTF retracement band.

Design consequence:
- only two structure engines exist in the strategy:
  - one on the External Structure TF
  - one on the Internal Structure TF

This keeps the model semantically consistent even if it makes the first
implementation heavier.

## Entry policy

Recommended v1:

- long entry when:
  - bullish HTF permission is true
  - price has entered an active bullish zone
  - bullish CHoCH occurs on the Internal Structure TF after the touch
    - same-bar zone entry and CHoCH confirmation is valid
    - CHoCH is only valid on the close of that Internal Structure TF candle
  - no open long is active

- short entry when:
  - bearish HTF permission is true
  - price has entered an active bearish zone
  - bearish CHoCH occurs on the Internal Structure TF after the touch
    - same-bar zone entry and CHoCH confirmation is valid
    - CHoCH is only valid on the close of that Internal Structure TF candle
  - no open short is active

Trigger freshness rules:
- the CHoCH must happen within `N` LTF bars of the zone touch
- only one trade per zone-touch cycle
- reset watch state if price leaves the zone and no trigger occurs

## Stop and exit design

Use two invalidation layers.

### Hard stop

For longs:
- below the zone low or below the local trigger swing low, whichever is wider

For shorts:
- above the zone high or above the local trigger swing high, whichever is wider

Add:
- minimum ATR floor so stops are not unrealistically tight

### Management

Recommended v1:
- TP1, TP2, TP3 each have user-defined:
  - position percentage
  - target in `R`
- after TP1 fills, stop moves to break-even for the remaining position
- TP2 and TP3 continue managing the remaining size

### Forced exits

Exit early if:
- opposite LTF CHoCH prints soon after entry
- HTF setup invalidates
- time stop expires

## Strategy state machine

Minimum states:

1. `idle`
2. `watch_long`
3. `watch_short`
4. `armed_long`
5. `armed_short`
6. `in_long`
7. `in_short`

Transitions:

- `idle -> watch_long`
  - bullish HTF permission and active bullish zone exists
- `watch_long -> armed_long`
  - price enters bullish zone
- `armed_long -> in_long`
  - bullish LTF CHoCH fires
- `armed_long -> idle`
  - timeout, invalidation, or opposite HTF shift

Mirror for shorts.

This is the right mental model for Pine. Do not treat this as a collection of
independent booleans.

## Backtest integrity rules

These are non-negotiable:

- all HTF values must use `request.security(..., lookahead = barmerge.lookahead_off)`
- zones must be built only from the currently-known HTF leg
- LTF trigger is only valid on the close of the Internal Structure TF candle
- same-bar zone touch and LTF CHoCH confirmation is valid as long as the zone condition and CHoCH condition are both true at bar close
- only act on completed HTF bars unless deliberately using live-forming HTF state

Recommendation for v1:
- use only **confirmed HTF bars**
- use only **confirmed reversal timeframe bars**
- use only **bar close entries**
- disable intrabar assumptions

That will be slower, but the test will be honest.

## Practical implementation approach in Pine

### Phase A: build a prototype strategy with approximated LTF trigger

1. Clone the v3.3 structure engine into reusable computation helpers.
2. Run that logic for the selected External Structure TF.
3. Run that same logic for the selected Internal Structure TF.
4. Track the current HTF impulse leg.
5. Build a user-configured fib retracement zone from that leg.
6. Add touch-watch state after price enters the zone.
7. Trigger entries only from a true Internal Structure TF CHoCH after the touch.
8. Add stop, TP1, TP2, TP3, and mandatory break-even migration after TP1.

## Recommended v1 scope

Keep the first backtest narrow:

- chart timeframe = selected Internal Structure TF
- one selected External Structure TF
- zone source:
  - use the current active leg from the selected HTF
- trigger:
  - true v3.3 CHoCH on the selected Internal Structure TF
- entry:
  - bar close only
- risk:
  - 1 position at a time
  - fixed fractional risk or fixed percent sizing

If this version cannot produce sensible distributions, there is no reason to
build the more complex variant yet.

## Suggested input set

### HTF structure
- `external_structure_tf`
- `structure_require_confirmed`

### Fib zone
- `fib_retrace_a`
- `fib_retrace_b`
- `max_zone_age_htf_bars`
- `require_first_touch`

### Trigger
- `internal_structure_tf`
- `max_bars_after_touch`

### Risk
- `atr_stop_mult`
- `min_stop_pct`
- `tp1_r`
- `tp2_r`
- `tp3_r`
- `tp1_qty_pct`
- `tp2_qty_pct`
- `tp3_qty_pct`

## Recommended build order

1. Prove HTF impulse-leg extraction is stable and point-in-time.
2. Plot the fib zones without trading.
3. Add watch state when price enters the zone.
4. Add Internal Structure TF CHoCH markers.
5. Add entries/exits.
6. Only then optimize thresholds.

If you optimize before validating leg and zone construction, the backtest will
look precise while being structurally wrong.

## Decision

Yes, this is practical to codify in Pine.

The practical path is:
- reuse the **v3.3 structure semantics for HTF context**,
- reuse the **same v3.3 structure semantics for LTF reversal confirmation**,
- keep **fib zones tied to the active HTF impulse leg**,
- coordinate only two timeframes in the strategy.

## Proposed next implementation target

Create a first strategy file that does the following only:

- runs on the selected Internal Structure TF,
- computes HTF structure context for the selected External Structure TF,
- computes LTF structure context for the selected Internal Structure TF,
- tracks one active bullish leg and one active bearish leg for that HTF,
- plots a user-defined retracement band,
- arms a watch when price enters the active band,
- enters only on a true Internal Structure TF CHoCH,
- exits with fixed stop, TP1/TP2/TP3, and break-even migration after TP1.

That is the smallest version likely to produce meaningful backtest evidence.
