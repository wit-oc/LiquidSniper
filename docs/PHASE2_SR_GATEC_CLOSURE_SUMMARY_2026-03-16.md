# Phase 2 Gate C closure summary — selector truth (2026-03-16)

## Gate C decision

**Promotion Gate C is satisfied.**

For both BTC and ETH, the trace now answers the required truth-path questions across:
- raw candidates
- merged candidates
- selected majors
- nearest ladders

## What the trace proved

### BTC
- The relevant upside Daily resistance levels **exist** in raw candidates.
- They **survive merge** into canonical confirmed zones.
- They are **lost in Daily-major selection**.
- The selector keeps high-score above-price **support** zones instead, so the execution-facing ladder falls back to **4H** resistance inventory.

**Loss point:** Daily selector doctrine.

### ETH
- The relevant 1D resistance levels **exist** in raw candidates.
- They **survive merge**.
- They **survive Daily-major selection**.
- The apparent "missing next resistance" appears when the nearest ladder treats the containing 1D resistance at `2047.17` as `nearest_resistance`, then chooses the closer **4H** resistance at `2293.69` as `next_resistance` instead of advancing to the next 1D major at `3489.21`.

**Loss point:** nearest-ladder semantics, not Daily selection.

## Shared doctrine issue

The common problem is not candidate generation or merge.

The common problem is that the selector stack is not explicit enough about the difference between:
- **truth-preserving major-surface inventory**, and
- **execution-oriented nearest/proximity ranking**.

That doctrine leak surfaces differently by symbol:
- **BTC:** too early, inside Daily-major selection.
- **ETH:** later, in cross-timeframe nearest-ladder interpretation.

## Recommendation for the next post-gate step

The next move should be **targeted selector/ladder semantics work**, not generic calibration.

### Recommended order
1. **Protect above-price resistance-map duty on the Daily major surface** so above-price supports cannot consume scarce Daily-major resistance slots when the operator is asking for resistance truth.
2. **Separate major-surface truth from nearest-ladder convenience** so the engine can expose both without forcing one to overwrite the other.
3. **Make `next_resistance` semantics explicit when price is already inside a containing 1D resistance band** (for example: nearest aligned resistance vs next 1D major beyond containing band).

## What should wait

Do **not** start with generic threshold, weight, or score nudging.

Why:
- BTC shows a doctrine/selection problem, not a raw-inventory shortage.
- ETH shows a semantics/ranking problem, not missing Daily truth.
- Calibration before semantic cleanup would mostly hide the mismatch instead of resolving it.

## Bottom line

**Post-Gate-C work should be a narrow selector-model / ladder-semantics pass, followed by human chart validation, and only then calibration if needed.**
