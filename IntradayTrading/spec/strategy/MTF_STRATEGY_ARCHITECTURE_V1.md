# MTF Strategy Architecture v1 (Post S/R Foundation)

Status: ACTIVE DESIGN REFERENCE  
Date: 2026-03-07  
Context: Incorporates external strategy review synthesis (GPT-5.4 Pro) into program specs.

## Core thesis

The system is a structured MTF trend-retest model:
- **1D** = directional permission
- **1D/4H zones** = where to care
- **15m** = trigger confirmation
- **5m** = optional execution refinement only (not primary trigger)

This is treated as a **state-machine strategy**, not a loose signal stack.

---

## Timeframe responsibilities (locked intent)

- **1D (Bias Layer):**
  - Determines whether longs/shorts are allowed.
  - If regime is unresolved/transitional, avoid normal-risk entries.
- **4H (Setup Context Layer):**
  - Validates context into zones.
  - Prevents blindly taking 15m flips while 4H is still impulsively opposing.
- **15m (Trigger Layer):**
  - Primary trigger (CHoCH / LTF shift evidence).
- **5m (Refinement Layer):**
  - Optional, only after 15m trigger is already valid.

---

## Staged decision process

1. **Directional permission**
   - 1D confirmed bullish -> long-only
   - 1D confirmed bearish -> short-only
   - unresolved/transitional -> skip or reduced-risk lane (execution policy)

2. **Setup qualification**
   - Price enters qualified 1D or 4H zone.
   - Prefer fresh/early retest.
   - Boost score for zone confluence with structural anchors and dynamic context.

3. **Reaction evidence**
   - Stall/rejection/displacement or opposing momentum loss at zone.

4. **Trigger**
   - 15m structure flip in bias direction.

This separation is critical for scale and noise control.

---

## Watch/trigger architecture implications

Phase 2 Watch Engine should certify setup state independently from triggers:
- WATCH should require directional permission + setup qualification.
- WATCH should incorporate 4H context gate (not fresh impulsive opposition).
- Trigger execution remains Phase 3 scope.

---

## Stop/invalidation design (for later phases)

Maintain two invalidation concepts:
- **Setup invalidation:** HTF zone/structural boundary failure
- **Trigger invalidation:** local LTF trigger failure

Execution stop selection should be structurally correct for setup class,
not purely closest LTF candle invalidation.

---

## Dynamic levels policy

Dynamic levels are **confluence/ranking inputs**, not primary setup reason.
Use to increase/decrease setup quality confidence only when aligned with:
- HTF zone,
- structural anchors,
- retracement context.

---

## No-trade / filter policy (must be explicit)

Skip when:
- 1D regime unresolved/transitional (normal lane)
- price is mid-range and not near qualified zone
- 4H is strongly opposing and unstalled
- zone quality degraded (excessive retests)
- approach is too violent without stabilization
- symbol quality is poor (spread/wick/liquidity abnormalities)

---

## Universe scaling rules

Top-100 market-cap is insufficient alone. Add liquidity-quality filters:
- notional volume
- spread quality
- OI/perp participation
- wick abnormality / volatility quality
- exchange/data cleanliness

---

## Backtest integrity requirement (hard)

All zone/state reconstruction must be **point-in-time**:
- no hindsight zone map leakage,
- no future-aware anchor significance,
- per-bar rebuild using only then-available data.

This is mandatory for certifiable forward transfer.

---

## Canonical strategy state machine (target)

1. Bias allowed
2. Setup watch
3. Reaction observed
4. Trigger armed
5. Execute
6. Manage

Each phase certifies only its relevant subset.

---

## Relationship to current phase plan

- Phase 1 (HTF structure): certified.
- Phase 2 (watch engine): should absorb Setup Qualification + Reaction gate + 4H context checks.
- Phase 3 (trigger): should focus on 15m quality and signal discrimination.
