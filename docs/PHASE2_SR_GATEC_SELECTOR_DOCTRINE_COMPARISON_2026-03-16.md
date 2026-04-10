# Gate C comparison — BTC/ETH selector doctrine synthesis (2026-03-16)

## Question

Do BTC and ETH point to a common selector-stage doctrine issue?

## Short answer

**Yes — but not because both symbols fail at the same literal pipeline stage.**

The common doctrine issue is that the engine's execution-facing selection/ranking path answers a **generic proximity/score question** instead of preserving an explicit **role-aware major-surface truth** for the operator.

That shared doctrine leak appears at different points:
- **BTC:** the leak happens inside **Daily-major selection** itself.
- **ETH:** the Daily-major surface survives, but the leak reappears in **nearest-ladder ranking/interpretation**.

So the common issue is **not** "candidate generation is weak" or "merge is broken." The common issue is:

> The selector stack is insufficiently explicit about above-price resistance-map duty versus generic high-score / nearest-zone retention.

## Side-by-side findings

| Symbol | Raw candidates | Merge | Daily-major selection | Nearest ladder | Actual loss point |
|---|---|---|---|---|---|
| BTC | upside resistance truth exists | preserved | **drops above-price Daily resistances** | falls back to 4H resistance inventory | **Daily selector doctrine** |
| ETH | upside resistance truth exists | preserved | preserves 1D resistance ladder | **uses containing 1D band as nearest, then picks closer 4H as next** | **ladder semantics doctrine** |

## What is common

### 1) Candidate generation is not the blocker
Both traces show plenty of valid above-price resistance inventory at the raw-candidate stage.

### 2) Merge is not the blocker
Both traces preserve the relevant 1D resistance truth into the merged canonical zone set.

### 3) The doctrine problem begins once the engine must answer an operator-facing question
In both cases, the failure begins when the system transitions from:
- "what valid zones exist?"

to:
- "which ones should occupy the operator-facing major/nearest slots?"

That transition currently behaves too much like:
- keep strongest generic zones,
- then keep nearest eligible zones,
- regardless of whether those slots are supposed to express **resistance-map truth** on a particular surface.

## BTC-specific manifestation

BTC shows the stronger/foundational failure:
- above-price Daily resistance truth survives merge,
- but Daily selection allows above-price **support** zones to consume scarce above-price Daily-major slots,
- so the Daily resistance map is already damaged before laddering.

That means BTC is a **selector-surface doctrine** problem first.

## ETH-specific manifestation

ETH shows the downstream/semantic failure:
- Daily selection still preserves the 1D resistance map,
- but nearest-ladder semantics treat the containing 1D resistance as the active nearest zone,
- then choose a closer 4H resistance as `next_resistance`,
- which diverges from the operator expectation of "next 1D major resistance beyond the current 1D band."

That means ETH is a **surface-to-ladder semantics** problem first.

## Doctrine synthesis

The clean synthesis is:

> The engine lacks a hard distinction between **truth-preserving major-surface inventory** and **execution-oriented nearest-zone convenience ranking**.

Because that distinction is weak:
- BTC loses resistance truth too early, during Daily-major slot arbitration.
- ETH keeps the truth longer, but the ladder layer answers a different question than the operator intended.

## Promotion Gate C conclusion

Gate C is satisfied because we can now answer the required questions concretely:
- Did the relevant levels exist? **Yes, for both BTC and ETH.**
- Did merge remove them? **No.**
- Did selection remove them? **BTC yes, ETH no.**
- What won instead, and why? **Generic score/proximity doctrine beat explicit resistance-surface duty.**

## Recommendation direction for T4

The next move should be framed as **targeted selector/ladder semantics work**, not generic calibration:
1. protect above-price resistance-map duty on the Daily major surface,
2. separate major-surface truth from nearest-ladder convenience,
3. make `next_resistance` semantics explicit when price is already inside a containing 1D resistance band.

Calibration/weight nudging should wait until those semantics are explicit, because otherwise tuning will only hide a doctrine mismatch.
