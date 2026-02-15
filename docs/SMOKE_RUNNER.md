# One-command Smoke Runner

Run end-to-end dry validation:
- Telegram ingest (`@MobChartBot` by default)
- latest symbol extraction
- chartability classification via watchlists
- TradingView multi-timeframe snapshots (15m/1h/4h/1D/1W)

```bash
python3 tools/smoke_runner.py --source @MobChartBot --limit 20
```

Output includes:
- ingest summary (`raw_messages`, `parsed_events`, `parse_errors`, `ignored_lines`)
- latest symbol
- `chartability` state:
  - `charted_primary`
  - `supported_blofin_uncharted`
  - `unsupported_or_unknown`
- snapshot artifact statuses

Watchlist config path:
- `config/watchlists.json`
