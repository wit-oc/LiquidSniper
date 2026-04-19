# Phase 1 contract basket comparison, 2026-04-14

- Scope: validation basket comparison of legacy `BoS 0.20 / CHoCH 0.15` vs canonical `BoS 0.15 / CHoCH 0.15`
- Operator-facing measure: selected SR surfaces on `1D` and `4H`
- Supporting measure: market-structure state diffs from pair analytics

## Topline
- Validation basket size: 15 symbols
- Basket covered by available candle sources: 14 symbols
- Missing source coverage: BNBUSDT
- 1D selected surface changed on 4 symbols: ETHUSDT, BCHUSDT, HBARUSDT, DOTUSDT
- 4H selected surface changed on 4 symbols: BTCUSDT, XRPUSDT, SOLUSDT, XLMUSDT
- 4H market-structure state changed on 9 symbols: BTCUSDT, XRPUSDT, SOLUSDT, DOGEUSDT, BCHUSDT, XLMUSDT, AVAXUSDT, HBARUSDT, DOTUSDT
- 1D market-structure state changed on 6 symbols: ETHUSDT, ADAUSDT, BCHUSDT, LINKUSDT, HBARUSDT, DOTUSDT
- No selected-surface change on either 1D or 4H for 6 symbols: DOGEUSDT, ADAUSDT, LINKUSDT, LTCUSDT, AVAXUSDT, TONUSDT

## Priority manual review set
- Focus first on: BTCUSDT, ETHUSDT, XRPUSDT, SOLUSDT, BCHUSDT, XLMUSDT, HBARUSDT, DOTUSDT
- Reason: these are the symbols where the operator-facing selected SR surfaces actually moved under the unified contract.

## Symbol notes
- **BTCUSDT**: 4H: selected changed (delta +0; added 1, removed 1); 4H structure changed (confidence, last_transition_reason, active_choch_level, protected_high)
- **ETHUSDT**: 1D: selected changed (delta +0; added 1, removed 1); 1D structure changed (event-count-only)
- **XRPUSDT**: 4H: selected changed (delta -1; added 0, removed 1); 4H structure changed (event-count-only)
- **SOLUSDT**: 4H: selected changed (delta +1; added 1, removed 0); 4H structure changed (event-count-only)
- **DOGEUSDT**: 4H structure changed (event-count-only)
- **ADAUSDT**: 1D structure changed (event-count-only)
- **BCHUSDT**: 1D: selected changed (delta +0; added 2, removed 2); 4H structure changed (event-count-only); 1D structure changed (trend, active_choch_level, protected_high, protected_low)
- **LINKUSDT**: 1D structure changed (event-count-only)
- **XLMUSDT**: 4H: selected changed (delta -1; added 1, removed 2); 4H structure changed (event-count-only)
- **AVAXUSDT**: 4H structure changed (event-count-only)
- **HBARUSDT**: 1D: selected changed (delta +0; added 1, removed 1); 4H structure changed (event-count-only); 1D structure changed (trend, confidence, last_transition_reason, active_choch_level)
- **DOTUSDT**: 1D: selected changed (delta +1; added 2, removed 1); 4H structure changed (event-count-only); 1D structure changed (protected_low)
