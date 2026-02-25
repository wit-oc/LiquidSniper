# TradingView Mentorship Fidelity Mapping (v1)

Versioned artifacts:
- `tradingview/indicator/liquidsniper_confluence_indicator_v1_fidelity.pine`
- `tradingview/strategy/liquidsniper_confluence_strategy_v1_fidelity.pine`

Scope: Rule-by-rule mapping from Foxian mentorship intent into Pine behavior, with alignment status and explicit gaps.

## Source references used (foxian-ingest final 2026-02-15)

1. `content/059-4th-confluence-trading-how-it-helps-foxian-org.md`
   - “a confluence is simply just your edge in the market” (around 00:07:38–00:08:16)
2. `content/021-42th-market-structure-rules-defining-swing-high-lows-major-boundaries-and-differ.md`
   - BoS/CHoCH definitions (around 00:01:20–00:01:42)
   - major swing high/low framing (around 00:06:35–00:07:06)
3. `content/022-41th-market-structure-essentials-break-of-structure-change-of-character-and-exte.md`
   - impulsive vs corrective wave behavior; highs/lows as SR (around 00:01:49–00:02:24)
4. `content/028-35th-practical-application-and-strategy-development-using-multi-timeframe-expone.md`
   - first retest emphasis; reaction uncertainty; early capture + candle-close option (around 00:03:51–00:05:26)
5. `content/030-33th-limitation-of-exponential-moving-averages-emas-in-sideways-markets-foxian-o.md`
   - avoid choppy/sideways regimes (around 00:07:18–00:07:55)
6. `content/003-60th-risk-focused-fibonacci-use-fib-levels-mainly-to-frame-entries-and-invalidat.md`
   - fixed invalidation/stop discipline; TP should be deliberate, not arbitrary (around 00:03:07–00:04:59)

---

## Rule-by-rule mapping

| # | Mentorship intent | Pine v1 implementation | Status |
|---|---|---|---|
| R1 | Confluence = stacked edge, not one signal | 7-component weighted confluence score (trend, structure, first retest, EMA stack, chop filter, candle close, SR side). Trigger is score-gated. | **Aligned** |
| R2 | Use MTF context for decisions | Profile-based TF map (`entry/itf/htf`) retained from v0; ITF+HTF EMA alignment drives directional context. | **Aligned** |
| R3 | Structure matters (BoS/CHoCH) | Swing-based structure engine (`ta.pivothigh/ta.pivotlow` + break logic) computes BoS and CHoCH proxy state. | **Aligned** |
| R4 | Prioritize first retest after displacement | Retest arming on BoS; only first zone touch inside configurable post-BoS window contributes as valid retest. | **Aligned** |
| R5 | First retest reaction is uncertain; confirmations can be stricter | Optional candle-close requirement (`require_candle_close`) preserved and integrated in score/trigger gates. | **Aligned** |
| R6 | Avoid sideways/choppy EMA traps | HTF chop gate using CI threshold + ADX minimum; trigger requires `chop_ok`. | **Aligned** |
| R7 | Trend + structure should agree | Trend direction (ITF/HTF EMA) and structure events (BoS/CHoCH) both required for high score; contradictory states reduce score. | **Aligned** |
| R8 | Risk should respect invalidation logic | Strategy uses explicit invalidation anchor from latest structural swing (fallback ATR), single full TP at defined RR. | **Partial** |
| R9 | TP selection should be deliberate (not arbitrary RR-only laddering) | Strategy removed partial TP laddering and uses one full TP; still parameterized by RR multiplier due to Pine constraints. | **Partial** |
| R10 | Manual SR zones and discretionary context remain central in mentorship | Pine uses ITF EMA50 dynamic SR proxy + retest band, not hand-drawn discretionary SR/OB/Fib map. | **Missing** |

---

## Misalignments by priority

### P0 (must-fix before claiming full mentorship parity)
1. **Manual discretionary SR/OB/Fib map not natively represented**
   - Current: EMA50-based dynamic SR proxy + retest zone.
   - Impact: misses nuanced hand-drawn horizontal zones/flip levels emphasized in mentorship.

### P1 (important for fidelity quality)
1. **Risk model still RR-parameterized**
   - Current: fixed invalidation + single TP, but TP derived by RR multiplier.
   - Impact: mentorship prefers context-derived target placement from structure/confluence, then RR as consequence.
2. **Structure abstraction uses local pivot heuristic**
   - Current: Pine pivot-based BoS/CHoCH proxy.
   - Impact: does not capture all discretionary major/minor structure interpretations taught in sessions.

### P2 (nice-to-have improvements)
1. **No explicit confluence families beyond implemented stack**
   - Missing direct OB/Fib/VWAP/index-context overlays in v1 script.
2. **No qualitative trade annotation layer**
   - Mentorship includes scenario commentary and discretion difficult to encode in Pine-only deterministic logic.

---

## Net assessment

- **Operationally aligned** with mentorship backbone on confluence stacking, MTF context, structure framing, first-retest focus, and chop avoidance.
- **Not yet full discretionary parity** due to Pine-only constraints around hand-drawn SR/OB/Fib and context-driven TP selection.
