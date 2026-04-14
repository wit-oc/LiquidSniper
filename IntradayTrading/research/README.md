# Intraday Revisit Research Harness (Wave 2 prep)

## End-to-end run script
`run_dataset.py` expects 1H OHLCV CSVs with columns:
- `timestamp` (epoch seconds)
- `open`, `high`, `low`, `close`

Example:

```bash
python3 intraday_revisit/research/run_dataset.py \
  --btc data/btc_1h.csv \
  --eth data/eth_1h.csv \
  --out intraday_revisit/artifacts/initial_run
```

Artifacts produced per symbol:
- `<symbol>_events.jsonl`
- `<symbol>_barlogs.jsonl`

## Adapter scaffolds
- `vectorbt_adapter.py`: validates and exposes long/short signal columns.
- `backtestingpy_adapter.py`: injects event-derived columns onto bar DataFrames.
