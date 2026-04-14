# Phase 0 — Wave Engine Spec (Draft v1)

Status: locked-phase1.1-contract
Owner: Wit + Redact
Scope: foundational wave/state logic only (no entries/risk)

## Locked Contract — Phase 1.1 (frozen)
1. Initialization is deterministic: EMA12 over first `N_INIT=25` candles sets initial trend direction; initial swing high/low are extrema over that window.
2. Accepted break requires close beyond structural level by at least `break_min_frac_of_candle` (default `0.20 * candle_range`), tunable.
3. Wick/SFP re-anchor is allowed only in current trend direction; opposite-direction sweeps are log-only.
4. Retracement validation is 2-step: candidate extreme validates only when opposite end of candidate candle is swept without creating a new extreme first.
5. CHoCH tentative has no timeout: detected CHoCH is a real bias change; confidence remains transitional until same-direction BoS confirms.
6. Back-to-back CHoCH is valid: tentative direction updates immediately and remains transitional until BoS confirms.
7. CHoCH is one-shot per protected level/wave: repeated accepted closes through same level are deduped until a new protected level is locked.

## 1) Core worldview
Price alternates between:
- Impulsive waves
- Retracement/Corrective waves

Each wave has direction:
- bullish
- bearish

Bullish/bearish logic is symmetric/inverted around high/low roles.

## 2) State model
Primary state fields:
- `wave_mode`: `impulsive` | `corrective`
- `direction`: `bullish` | `bearish`
- `confidence`: `confirmed` | `transitional`
- `protected_high` / `protected_low`
- `candidate_extreme` (high or low depending on current role)
- `candidate_opposite_sweep_level`
- `last_event`

Derived/event states:
- `bos_confirmed`
- `choch_detected`
- `choch_reverted`
- `sfp_detected`

## 3) Initialization
- Use first `N_INIT` candles (default 25) to initialize direction bias.
- Initial bias heuristic (v1): EMA12 slope and close-vs-EMA12 majority.
- Initialization is allowed to be imperfect; system should self-correct quickly via event logic.

## 4) Event rules (direction-agnostic contract)
### 4.1 Candidate confirmation rule
A candidate extreme is confirmed only when:
- opposite side is swept,
- without creating a new extreme first.

### 4.2 BoS
- BoS confirms continuation of current directional structure.
- In bullish context, BoS is close-through above relevant confirmed high with displacement threshold.
- In bearish context, mirrored below relevant confirmed low.
- On BoS, lock opposite swing from bounded interval between anchor and BoS candle.

### 4.3 CHoCH
- CHoCH is first accepted close-through against protected opposite level.
- CHoCH is one-shot per protected level/wave.
- CHoCH flips direction to transitional (not neutral).
- BoS in new direction upgrades confidence to confirmed.

### 4.4 SFP
- SFP is liquidity sweep event, not BoS/CHoCH by itself.
- Directional SFP may re-anchor trend-side level (per rules).
- Opposite-side SFP logs signal but does not auto-shift regime.

### 4.5 Equal levels
- Equal highs/lows count as sweeps.

### 4.6 Gap-through note
- In crypto 24/7 context, "open beyond level" is treated as continuation, not valid retracement start if it creates new extreme first.

## 5) Displacement threshold (accepted breaks)
Use tunable accepted-break threshold:
- `break_min_frac_of_candle` (default 0.20 of candle range) beyond level
- optional future blend: max(percent, ATR-based)

## 6) One-shot / dedupe constraints
- CHoCH emits once per protected level.
- Repeated closes through same level do not re-emit CHoCH.
- Re-arm only after new protected level is locked.

## 7) Output schema (must log per bar)
- `index, timestamp`
- `wave_mode, direction, confidence`
- `protected_high, protected_low`
- `candidate_extreme`
- `event` (+ reason)
- `anchor_update_reason`

## 8) Out of scope
- Watch/trigger entry logic
- Fib/candle filters
- Position sizing / risk / exits

## 9) Acceptance gates for Phase 0
- Deterministic rerun on same data yields identical events.
- CHoCH/BoS ratio on 1D no longer pathological.
- Swing-high and swing-low lock events appear symmetrically over long sample.
