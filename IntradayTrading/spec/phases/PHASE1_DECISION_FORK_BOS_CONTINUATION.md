# Phase 1 Decision Fork — BoS Strictness vs Practical Continuation

Status: **OPEN** (codified for review)
Owner: Redact + Wit
Scope: `HTF_Phase1_Structure_v3.pine` Phase-1 structure semantics only

---

## Why this fork exists

Current v3 logic is faithful to the strict mapping rule:

- In-trend swing is only **validated** after opposite-end sweep (`create + future sweep without new extreme`).
- With strict gating enabled, **BoS/CHoCH are blocked** while that in-trend swing is pending.

Observed edge case (from live chart review):

- Price breaks a prior swing high, first attempt behaves like an SFP/failed hold,
- then the very next candle closes through and trend continues strongly upward,
- no meaningful retracement happens,
- strict model still says "not BoS yet" because candidate validation sequence has not completed.

This is internally consistent, but can feel operationally too rigid.

---

## Fork options

## Option A — Keep strict model (current)

- BoS only after fully validated in-trend swing cycle.
- No intermediate continuation label.

Pros:
- Maximum rule purity and consistency with the strict interpretation.

Cons:
- Can under-report obvious continuation in fast trends.
- Feels late/non-intuitive in strong impulse legs.

---

## Option B — Add Continuation Break (CB) layer (**recommended**)

Keep strict BoS unchanged, but add a separate interim state/event:

- `CB` fires when price convincingly closes through continuation reference while strict gate is still closed.
- `CB` is **not** a confirmed BoS.
- `CB` later resolves to:
  - `BoS confirmed` after required validation sequence, or
  - invalidated if structure fails.

Pros:
- Preserves strict doctrine while surfacing practical continuation information.
- Avoids re-labeling strict BoS semantics.

Cons:
- Adds one more state/event to maintain/test.

---

## Option C — Relax strict gate for BoS

- Allow BoS before full candidate sweep validation under specific conditions.

Pros:
- Fewer "missed continuation" moments.

Cons:
- Blurs the strict framework and increases subjectivity.
- Harder to keep deterministic over time.

---

## Decision intent (proposed)

Adopt **Option B**:

1. Keep strict BoS definition unchanged.
2. Introduce `Continuation Break (CB)` as a separate, explicitly non-final event.
3. Use panel fields to show progression:
   - `Continuation: none|active`
   - `BoS state: pending|confirmed`

---

## CHoCH work (next after this fork)

Before BoS visual polish, fix CHoCH determinism/diagnostics:

- Add explicit CHoCH eval fields:
  - `CHoCH check: true/false`
  - `CHoCH blocked reason: gate_closed | weak_close | deduped | none`
- Keep CHoCH and BoS thresholds independently configurable if needed.

---

## Acceptance checks for this fork

1. In the "two-candle continuation after SFP-like first attempt" scenario:
   - strict BoS remains pending,
   - `CB` appears,
   - later BoS confirms when validation completes.
2. No false CHoCH flips during same sequence.
3. Panel text remains directionally consistent (no stale ancient anchors).

---

## Notes

This fork does **not** change the core market-structure doctrine in `MarketStructure.md`; it adds a deterministic observational layer to better map live continuation behavior without diluting strict confirmation semantics.
