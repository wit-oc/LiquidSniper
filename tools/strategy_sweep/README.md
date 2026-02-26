# Strategy Sweep (Pine v1 scaffold)

This folder ports the **high-level LiquidSniper Pine strategy v1 structure** into Python to run parameter sweeps before pushing shortlisted settings back to TradingView.

## Scope / fidelity

`engine_v1.py` models these Pine-v1 concepts:
- trend alignment via EMA stack (entry + ITF + HTF proxies)
- structure via swing highs/lows with BoS/CHoCH proxies
- retest window + first-retest gating
- chop filters (CI + ADX proxy)
- trigger score + gate pass/fail
- deterministic exits with BE activation + RR TP
- sizing modes:
  - `percent_of_equity`
  - `risk_based` with confluence-tier risk and profile caps

This is intentionally a **sweep scaffold**, not a full brokerage-grade simulator.

## Files

- `profiles.yaml` - profile-specific grids and constraints for C/I/S
- `run_sweep.py` - executes profile sweeps and writes leaderboards + manifest
- `export_tv_shortlist.py` - exports top10/profile plus 3 safe picks/profile
- `engine_v1.py` - strategy logic + basic deterministic backtest executor
- `data_loader.py` - CSV loader; parquet supported when pandas is present
- `score.py` - composite scoring function used for ranking
- `optimization_governance.md` - sweep governance and anti-overfit guardrails

## Run

```bash
cd /Users/wit/.openclaw/workspace/LiquidSniper
python tools/strategy_sweep/run_sweep.py \
  --data data/sample_ohlcv.csv \
  --samples 80 \
  --seed 42 \
  --out tools/strategy_sweep/outputs

python tools/strategy_sweep/export_tv_shortlist.py \
  --in-dir tools/strategy_sweep/outputs \
  --out tools/strategy_sweep/outputs/tv_shortlist.csv
```

Outputs:
- `leaderboard_C.csv`
- `leaderboard_I.csv`
- `leaderboard_S.csv`
- `tv_shortlist.csv`
- `run_manifest.json`

See `examples/` for quick commands and sample config.
