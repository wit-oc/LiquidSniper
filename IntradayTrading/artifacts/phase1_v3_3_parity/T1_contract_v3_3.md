# T1 — HTF Phase1 v3.3 Parity Contract (Pine → Python)

Source of truth: `intraday_revisit/pine/HTF_Phase1_Structure_v3_3.pine`

## Baseline knobs (locked for parity)

- `strictGating = false`
- `breakMinFrac = 0.15`
- `chochBreakMinFrac = 0.15`
- `bosRequireFreshCross = true`

## Core state model

- Regime state:
  - `regimeDir ∈ {bullish, bearish}`
  - `regimeConf ∈ {confirmed, transitional}`
  - `regimeReason ∈ {bootstrap, choch_detected, bos_confirmed}`
- Structural anchors (CHoCH checks + BoS writes):
  - bullish side protected anchor: `protectedLow`, `protectedLowIdx`
  - bearish side protected anchor: `protectedHigh`, `protectedHighIdx`
- Validated in-trend references:
  - bullish continuation reference: `validatedHigh`, `validatedHighIdx`
  - bearish continuation reference: `validatedLow`, `validatedLowIdx`
- Candidate gates:
  - bullish candidate: `candHigh`, `candHighIdx` + creator-candle opposite end (`candHighLow`, `candHighLowIdx`)
  - bearish candidate: `candLow`, `candLowIdx` + creator-candle opposite end (`candLowHigh`, `candLowHighIdx`)
- Dedup latches:
  - CHoCH one-shot per protected index: `lastChochProtectedLowIdx`, `lastChochProtectedHighIdx`
  - BoS one-shot per validated reference index: `lastBosBullRefIdx`, `lastBosBearRefIdx`
- Optional continuation-break fork state (only meaningful when strict gate closed):
  - `cbActive`, `cbDir`, `cbLevel`, `cbFromIdx`

## Lifecycle contract (event/state transitions)

### 1) Candidate build + validation gate

Bull regime:
1. New higher high extends candidate (`high > candHigh` → update `candHigh*`).
2. Candidate validates **only** when a future candle sweeps creator low without making a new high:
   - `bar_index > candHighIdx`
   - `low <= candHighLow`
   - `high <= candHigh`
3. On validation: set `validatedHigh = candHigh`, `validatedHighIdx = candHighIdx` and raise `evSwingValidated`.

Bear regime mirrors with low/high swapped:
- Build on `low < candLow`.
- Validate on future candle with:
  - `bar_index > candLowIdx`
  - `high >= candLowHigh`
  - `low >= candLow`
- On validation write `validatedLow*` and `evSwingValidated`.

Gate-open condition:
- Bull: `bullGateOpen = not (na(validatedHighIdx) or candHighIdx != validatedHighIdx)`
- Bear: `bearGateOpen = not (na(validatedLowIdx) or candLowIdx != validatedLowIdx)`
- Structural eval allowed when `strictGating ? gateOpen : true`.

### 2) BoS continuation detection + dedupe

Bull BoS signal from validated high:
- Attempt: `close > validatedHigh`
- Conviction: `(close - validatedHigh) >= breakMinFrac * (high-low)`
- Fresh-cross (if enabled): `close > validatedHigh` and `close[1] <= validatedHigh`
- Signal: conviction AND (fresh-cross if required)
- Dedupe block: `lastBosBullRefIdx == validatedHighIdx`

Bear BoS mirrors off `validatedLow` with below-side conditions.

Blocked-reason priority for diagnostics:
1. `weak_close`
2. `no_fresh_cross`
3. `deduped`
4. `gate_closed` (only if strict gating active)
5. else `none`

### 3) BoS anchor writes (structure-first)

When BoS fires (direct or promoted):
- Set `evBos = true`, record `bosFromPrice/bosFromIdx` from active reference.
- **Bull BoS write point:**
  - write opposite structural anchor to lowest low since validatedHigh index:
  - `protectedLow = bullLockLow`, `protectedLowIdx = bar_index + bullLockOff`
  - update latches: `lastBosBullRefIdx = bosRefIdx`
- **Bear BoS write point:**
  - write opposite structural anchor to highest high since validatedLow index:
  - `protectedHigh = bearLockHigh`, `protectedHighIdx = bar_index + bearLockOff`
  - update latches: `lastBosBearRefIdx = bosRefIdx`
- Set regime confirmation:
  - `regimeConf = confirmed`
  - `regimeReason = bos_confirmed`
  - `activeChochLevel = na`

### 4) CHoCH detection + flip-anchor write

Bull regime CHoCH↓ (break protected low):
- Attempt: `close < activeBullAnchor` where `activeBullAnchor = protectedLow`
- Conviction: `(activeBullAnchor - close) >= chochBreakMinFrac * (high-low)`
- Dedupe block: `lastChochProtectedLowIdx == activeBullAnchorIdx`
- On fire:
  - set `lastChochProtectedLowIdx = activeBullAnchorIdx`
  - `evChoch = true`, `chochFrom* = activeBullAnchor*`
  - flip regime: `regimeDir = bearish`, `regimeConf = transitional`, `regimeReason = choch_detected`
  - set `activeChochLevel = activeBullAnchor`
  - **flip-anchor write point:** `protectedHigh = highest(high, window from protectedLowIdx..now)`

Bear regime CHoCH↑ mirrors (break protected high, flip to bullish, write `protectedLow` as lowest low over flip window).

CHoCH blocked-reason priority:
1. `weak_close`
2. `gate_closed` (only if strict gating active)
3. `deduped`
4. else `none`

### 5) Transitional reset after CHoCH

Immediately after CHoCH:
- Reset opposite-direction candidate stream to current bar start.
- Clear opposite validated ref (`validatedLow/validatedHigh = na` respectively).
- This enforces retracement→validation→BoS flow before next confirmation.

### 6) Continuation-break (CB) fork semantics

Only active when `enableContinuationBreak && strictGating && !gateOpen`.
- If continuation signal exists while gate closed, emit/refresh `evCb` and store pending reference (`cb*`).
- Promotion condition once gate unlocks at same ref index:
  - bullish: `cbActive && cbDir==bullish && cbFromIdx==validatedHighIdx && !deduped`
  - bearish mirror.
- Promotion executes full BoS path, including structural anchor writes and BoS latches.
- CHoCH invalidates same-direction pending CB.

## Dedupe contract (must match exactly)

- CHoCH can trigger once per protected anchor index.
- BoS can trigger once per validated reference index.
- With `bosRequireFreshCross=true`, repeat closes beyond same level do not retrigger without new fresh cross on a new validated reference.

## Parity-critical implementation notes for Python

1. Keep index-based windows for lock/flip anchors (not time-only).
2. Preserve event ordering in each bar: candidate updates/validation → BoS checks/promotions → CHoCH checks → post-CHoCH resets.
3. Preserve transitional semantics (`regimeConf=transitional` on CHoCH, `confirmed` only on BoS).
4. Keep diagnostics fields (`bosBlockedReason`, `chochBlockedReason`, `bosCheck`, `chochCheck`) for parity tracing.
5. Under locked baseline (`strictGating=false`), CB path should stay dormant but code-compatible for future strict runs.
