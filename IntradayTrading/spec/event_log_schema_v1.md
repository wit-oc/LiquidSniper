# Event Log Schema v1

Per-bar JSONL record fields:
- `index` (int): bar index
- `timestamp` (optional int)
- `symbol` (str)
- `tf` (str): expected `1h`
- `structure_bias` (str): bullish|bearish|neutral
- `zone_id` (str|null)
- `zone_kind` (str|null): support|resistance
- `zone_touched` (bool)
- `reclaim_confirmed` (bool)
- `filters_passed` (bool)
- `at_risk_count` (int)
- `breaker_open` (bool)
- `action` (str): none|enter_long|enter_short|exit|breaker_lock
- `reason` (str)

Determinism requirements:
- One record per processed bar.
- Stable key order in serializer.
- Identical input + config must produce byte-identical JSONL.
