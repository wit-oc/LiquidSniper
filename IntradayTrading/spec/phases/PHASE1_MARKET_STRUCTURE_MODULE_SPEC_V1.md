# Phase 1 Market Structure Module Spec v1

Status: CERTIFIED BASELINE WITH REVALIDATION NOTE  
Date: 2026-04-09  
Phase: Phase 1  
Owners: Redact + Wit

## Purpose
This document is the canonical Phase 1 module spec for the **market structure / directional permission engine**.

It records what the module is responsible for, what logic is already considered locked, what artifacts exist in the repo, and what downstream phases are allowed to assume.

This spec is intentionally narrower than a full trading strategy document.
It defines the **structure engine**, not the watcher, trigger, or execution system.

## Repo evidence already present
Current repo artifacts already covering this phase include:
- `IntradayTrading/spec/phases/PHASE0_WAVE_ENGINE_SPEC.md`
- `IntradayTrading/spec/phases/PHASE1_HTF_STRUCTURE_CERT_PLAN.md`
- `IntradayTrading/spec/phases/PHASE1_HTF_STRUCTURE_DONE.md`
- `IntradayTrading/pine/HTF_Phase1_Structure_v3_3.pine`
- `IntradayTrading/pine/HTF_Phase1_Structure_v3_3_USER_GUIDE.md`
- `IntradayTrading/engine/htf_phase1.py`
- `IntradayTrading/tests/test_htf_phase1.py`
- `IntradayTrading/artifacts/phase1_v3_3_parity/*`

## Validation status note
The current repo documentation says Phase 1 was certified with accepted TradingView/Python parity on BTC/ETH 1D windows.

That is the current working assumption for downstream specs.

If operator confidence in the Pine -> Python conversion is low, the right follow-up is **revalidation**, not rewriting the Phase 1 contract from memory.

## Scope
Phase 1 owns:
- HTF directional structure interpretation
- BoS / CHoCH / protected-level semantics
- confirmed vs transitional directional state
- structural event tape and anchor updates
- directional permission for downstream phases

Phase 1 does **not** own:
- S/R zone discovery
- Fib context
- dynamic-level confluence
- `WATCH / INVALID / EXPIRED`
- 15m trigger confirmation
- trade execution or risk logic

## Module role in the broader architecture
Phase 1 is the **source-of-truth structure layer**.

Downstream modules may consume Phase 1 outputs, but should not silently redefine its semantics.

The intended hierarchy is:
1. Phase 1 Market Structure Module = directional and structural truth
2. Phase 2 Watcher Engine = setup-context and zone-tracking truth
3. Phase 3 Analyst Engine = trigger truth
4. Phase 4 Risk/Execution Simulation = backtest trade truth

## Core worldview
Price alternates between impulsive and corrective movement.
The module's job is to map that movement into a deterministic state model that can answer:
- what direction is currently favored?
- is that direction confirmed or transitional?
- what structural levels are protected?
- what event just occurred?

## State model
The structure engine should maintain, at minimum:
- `wave_mode`: `impulsive | corrective`
- `direction`: `bullish | bearish`
- `confidence`: `confirmed | transitional`
- `protected_high`
- `protected_low`
- candidate extreme fields needed for swing confirmation
- `last_event`

Derived/event states may include:
- `bos_confirmed`
- `choch_detected`
- `choch_reverted`
- `sfp_detected`

## Locked logic contract
The following points are already treated as the certified Phase 1 contract unless explicitly superseded.

### 1) Deterministic initialization
Initialization is deterministic.
The initial direction is seeded from the first `N_INIT` candles, using EMA12-based bias and swing extrema logic.

Current locked baseline from the certified packet:
- `n_init = 25`
- `strictGating = false`
- `bosRequireFreshCross = true`
- `breakMinFrac = 0.15`
- `chochBreakMinFrac = 0.15`
- `enableContinuationBreak = true`

### 2) Accepted break logic
A break is only accepted when price closes beyond the structural level with at least the configured minimum displacement threshold.

This prevents wick-only or trivial pierces from being mistaken for true structural breaks.

### 3) Candidate confirmation logic
A candidate extreme is only confirmed when the opposite side of the candidate candle is swept **without a newer extreme forming first**.

This is one of the main anti-noise guards in the structure engine.

### 4) BoS semantics
BoS confirms continuation of the current directional structure.

In bullish context:
- BoS is a close-through above the relevant confirmed high with accepted displacement.

In bearish context:
- mirrored logic applies below the relevant confirmed low.

On BoS, the bounded interval logic is used to lock the relevant opposite swing / protected level.

### 5) CHoCH semantics
CHoCH is the first accepted close-through against the protected opposite level.

Locked expectations:
- CHoCH is one-shot per protected level / wave
- CHoCH flips direction immediately to the new side
- confidence becomes `transitional`, not neutral
- a same-direction BoS after CHoCH upgrades confidence to `confirmed`
- back-to-back CHoCH events are valid if the structural rules permit them

### 6) SFP semantics
SFP is a liquidity sweep event, not automatically a BoS or CHoCH.

Directional SFP may re-anchor the trend-side level if allowed by the contract.
Opposite-side SFP should remain informational unless the broader structural rules confirm a true shift.

### 7) Equal-level handling
Equal highs and equal lows count as valid sweeps for structural purposes.

### 8) Dedupe / one-shot discipline
Repeated closes through the same protected level should not keep emitting new CHoCH events until the protected-level contract has actually re-armed.

This is necessary for clean event tapes and downstream determinism.

## Output contract
At minimum, the structure engine should expose enough per-bar information for downstream replay and auditing:
- timestamp / bar index
- `wave_mode`
- `direction`
- `confidence`
- protected levels
- current candidate extreme info
- emitted event type
- anchor update reason

A downstream module must be able to answer:
- what structure state existed at this moment?
- why did it change?
- what protected level or anchor changed?

## Workflow behind the Phase 1 module

### Step A: price input
The engine consumes ordered candle data for the active HTF context.

### Step B: initialize state
The initialization window seeds the first directional hypothesis and starting extrema.

### Step C: update candidate extremes
As candles print, candidate extremes are updated subject to the confirmation rules.

### Step D: detect structural events
The engine checks for:
- accepted continuation break
- first accepted break against protected level
- sweep-only behavior

### Step E: update protected levels and confidence
After each accepted event, the engine updates:
- protected high / low
- direction
- confidence
- event tape output

### Step F: emit downstream structure state
That state then becomes the structural input to the watcher and later modules.

## What downstream phases may assume
Phase 2 and beyond may assume that Phase 1 can provide:
- current directional permission
- current confirmed vs transitional state
- BoS / CHoCH event lineage
- protected levels / structural boundaries
- anchor references needed for downstream POI, Fib, and gating work

They should **not** assume that Phase 1 already solves setup qualification, zone ranking, or trigger confirmation.

## Known caveats / boundaries
- The TradingView indicator computes on the active chart timeframe rather than a fixed `request.security()` HTF pin.
- Phase 1 certification was documented on BTC/ETH 1D windows. Any broader universe expansion should be treated as new validation work, not implied certification.
- If Pine and Python are later found to disagree materially, the resolution path is a parity review packet, not silent divergence.

## Revalidation placeholder
If needed later, answer these before changing the Phase 1 contract:
- `TBD-P1-REVAL-001`: Do we need a fresh Pine/Python parity rerun for BTC/ETH 1D?
- `TBD-P1-REVAL-002`: Do we need explicit 4H parity artifacts under the v3.3 contract?
- `TBD-P1-REVAL-003`: Does any newer Python refactor change the certified event tape or only implementation shape?

## Non-goals for this spec
This spec does not attempt to settle:
- how S/R zones are built
- how Fib anchors are ranked
- how dynamic levels change setup quality
- how watcher lifecycle should expire or re-arm
- how trigger entries should be scored

Those belong to later phase specs.

## Bottom line
Phase 1 is the structural truth layer.

The repo already contains the baseline contract, code, tests, Pine indicator, user guide, and parity artifacts needed to treat it as the current upstream market-structure module, with revalidation available if confidence later requires it.
