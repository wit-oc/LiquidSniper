# Updating the Top100 universe

LiquidSniper Phase 1 uses a **Top 100 (non-stablecoin) by market cap** universe with **USDT pairs**.

This repo provides a helper script to fetch the list from CoinMarketCap.

## Prereqs

- A CoinMarketCap Pro API key
- Put it in `.env` (repo root) **without committing it**:

```bash
cd LiquidSniper
cat > .env <<'EOF'
CMC_API_KEY=YOUR_KEY_HERE
EOF
```

The repo `.gitignore` already excludes `.env`.

## Run

```bash
cd LiquidSniper
set -a && source ./.env && set +a
python3 tools/fetch_cmc_top100.py --debug
```

Outputs:
- `data/universe/top100.json` (ranked assets + metadata)
- `data/universe/top100_usdt_pairs.txt` (one pair per line, e.g. `ETHUSDT`)

## Mobchart whitelist

Paste the contents of `data/universe/top100_usdt_pairs.txt` into Mobchart’s pair whitelist.

## Notes

- Stablecoins are excluded by default (see script). If a stable-like symbol still sneaks in, add it via `--exclude`.
- Wrapped/staked assets may still appear; we can add them to `--exclude` if needed.
- If an exchange uses special symbols (e.g., `1000PEPEUSDT`), we will handle those via overrides as we observe them.
