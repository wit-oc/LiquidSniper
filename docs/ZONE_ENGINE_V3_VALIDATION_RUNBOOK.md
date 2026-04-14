# Zone Engine V3 Validation Runbook

Purpose: anchor the next zoom-out phase after the current UI/transparency pass.

## Goal
Validate whether V3 SR dynamics are operator-trustworthy across the in-scope pair set before another major tuning pass.

## Sweep order
1. Generate a pair sweep across in-scope symbols using the current V3 analytics payload.
2. For each symbol, record:
   - nearest/next support and resistance
   - majors vs operational split
   - source family / candidate family mix
   - arbitration winner + cluster members
   - structure coverage by timeframe (1H/4H/1D)
3. Flag symbols where coverage is missing or arbitration looks suspicious.
4. Run human chart validation on the flagged set first, then on a clean sample of non-flagged symbols.
5. Decide branch direction:
   - if chart validation is broadly clean -> one final GPT 5.4 Pro accuracy pass
   - if not clean -> targeted tuning on the failed dynamics only

## Checklist
- [ ] Produce pair sweep artifact for current in-scope universe
- [ ] Confirm every row includes nearest/next ladder plus family badges
- [ ] Confirm structure availability explicitly reports ready vs missing_source vs load_failed
- [ ] Sample at least 10 symbols for human chart review
- [ ] Record false-positive / false-negative patterns by family
- [ ] Record arbitration disputes where the kept zone looks wrong
- [ ] Decide: final pro pass or targeted tuning

## Suggested artifact shape
- `artifacts/validation/zone_engine_v3_pair_sweep_<timestamp>.json`
- `artifacts/validation/zone_engine_v3_chart_review_<timestamp>.md`

## Review prompts
- Are majors actually acting like majors, or just highest-score dailies?
- Are operational levels meaningfully closer/tactically useful?
- Do family badges explain why the zone exists, or just label noise?
- When a merged zone survives, is the winning source obvious from the audit payload?
- Are missing structure timeframes explicit enough to prevent false confidence?
