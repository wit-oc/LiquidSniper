# SR Engine V2 Spec (Pivot-Zone, HTF-Anchored)

Status: Proposed (implementation wave queued)  
Scope: Paper mode first; deterministic and replay-auditable; no live execution authority.

## 1) Why V2

Current S/R heuristics are too coarse (recent-window extrema), causing poor lane differentiation and weak first-retest semantics.

V2 aligns with mentorship guidance in `docs/support_resistance.md` + `docs/condensed_topics/02_support_resistance_core.md`:
- zones over lines,
- top-down timeframe relevance,
- level persistence and reaction quality,
- first-retest/deviation behavior,
- clutter reduction and explicit invalidation.

## 2) Core design

Three-layer model:
1. **Zone Engine** (structural): pivot detection + clustering into zones.
2. **Event Engine** (behavior): first-retest and deviation-retest classification.
3. **Quality Engine** (ranking): deterministic score now; probabilistic extension later.

## 3) Timeframe policy (hard)

Supported zone TFs now: `1W, 1D, 4H, 1H`.

Profile eligibility:
- **Swing (S, anchor 1D)**: primary zones from `1D,1W`; lower TFs context-only.
- **Intraday (I, anchor 4H)**: primary zones from `4H,1D,1W`; `1H` context-only.
- **Scalp (C, anchor 1H)**: primary zones from `1H,4H,1D,1W`.

Rule: if zone TF is below profile anchor eligibility, it cannot be promoted as primary S/R gate input.

## 4) Zone algorithm

### 4.1 Pivot extraction
For window `k_tf`:
- swing high at `t` if `H_t = max(H_{t-k..t+k})`
- swing low at `t` if `L_t = min(L_{t-k..t+k})`

### 4.2 Clustering
Normalize by ATR on same TF:
- `d(i,j) = |p_i - p_j| / ATR_tf`
- same cluster if `d <= eps_tf`

Cluster -> zone bounds:
- `zone_low = q20(cluster_prices)`
- `zone_high = q80(cluster_prices)`
- enforce minimum width floor (`max(pct_floor, atr_floor)`)

### 4.3 Confirmation
A zone is **confirmed** only when:
- `meaningful_touch_count >= 3`

Meaningful touch:
- candle intersects zone and
- reaction magnitude within next 1-3 candles exceeds `reaction_atr_min_tf`.

## 5) Event engine

### 5.1 First retest
After zone confirmation, first return to zone is tagged `first_retest`.
Result classification:
- `reject`
- `accept`
- `deviation`

### 5.2 Deviation-retest
Sequence:
1) breach through zone,
2) reclaim across zone edge,
3) retest reclaimed side,
4) rejection with displacement.

## 6) Data model

### 6.1 `sr_zones`
- `zone_id`, `symbol`, `tf`
- `zone_low`, `zone_high`, `zone_mid`
- `status` (`candidate|confirmed|broken|retired`)
- `touch_count`, `meaningful_touch_count`
- `first_retest_pending`, `first_retest_ts`, `first_retest_result`
- `strength_score`, `reaction_score`
- `created_ts`, `updated_ts`, `source_version`

### 6.2 `sr_zone_touches`
- `touch_id`, `zone_id`, `symbol`, `tf`, `candle_ts`
- `touch_type`, `reaction_type`, `reaction_magnitude_atr`, `is_meaningful`

### 6.3 optional snapshots
- `sr_zone_snapshots` for replay/debug.

## 7) Trade-time query contract

Input: `(symbol, profile_id, side, now_ts)`

Output:
- `nearest_support` and `nearest_resistance` from eligible TF set
- each with: `zone_id, tf, bounds, strength, touch_count, first_retest_status, distance_bps`
- `gate_eligible` boolean and deterministic reason codes

## 8) Gate integration (replacing current SR heuristic)

Primary gate order:
1. bias permission
2. SR eligibility from V2 (`confirmed`, timeframe-eligible, event-eligible)
3. secondary confluence threshold
4. throttle/risk

BoS/CHoCH remains bias mechanism, not direct entry hard gate.

## 9) Cadence

Recompute on TF close:
- 1H hourly
- 4H every 4h
- 1D daily
- 1W weekly

Incremental updates per `symbol+tf` only; no full rebuild each cycle.

## 10) Observability

Run artifacts must include:
- `sr_anchor_tf`, `sr_eligible_tfs`
- nearest support/resistance with TF + zone IDs
- touch/retest state
- SR gate trail reasons

Debug UI must show per-lane SR context side-by-side.

## 11) Safety / anti-regression

Before any non-paper discussion:
- deterministic replay fixtures for zone generation pass,
- no lower-TF override of anchor policy,
- touch/retest state stable across restarts,
- reject reasons deterministic and auditable,
- bounded frequency still holds.

## 12) Task breakdown (implementation)

- **SRV2-T0**: Docs contract alignment (runbook/glossary references)
- **SRV2-T1**: DB schema migrations (`sr_zones`, `sr_zone_touches`, indexes)
- **SRV2-T2**: Pivot extraction + ATR-normalized clustering engine
- **SRV2-T3**: Zone lifecycle + meaningful touch logic (`>=3` confirmation)
- **SRV2-T4**: First-retest/deviation-retest event classifier
- **SRV2-T5**: Trade-time query service with profile eligibility enforcement
- **SRV2-T6**: Gate integration into daemon (replace current SR heuristic)
- **SRV2-T7**: Artifact/UI diagnostics upgrades (lane comparison)
- **SRV2-T8**: Deterministic tests + smoke validation + rollout runbook
