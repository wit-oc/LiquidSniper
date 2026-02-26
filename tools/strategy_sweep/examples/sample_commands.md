# Sample commands

```bash
# 1) Run sweep (CSV)
python tools/strategy_sweep/run_sweep.py \
  --data data/sample_ohlcv.csv \
  --profiles tools/strategy_sweep/profiles.yaml \
  --samples 60 \
  --seed 42 \
  --out tools/strategy_sweep/outputs

# 2) Build TradingView shortlist
python tools/strategy_sweep/export_tv_shortlist.py \
  --in-dir tools/strategy_sweep/outputs \
  --out tools/strategy_sweep/outputs/tv_shortlist.csv

# 3) quick inspect
head -n 20 tools/strategy_sweep/outputs/leaderboard_I.csv
head -n 20 tools/strategy_sweep/outputs/tv_shortlist.csv
```
