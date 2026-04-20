# Universe selection (Phase 1 design)

## Goal

Improve signal quality and reduce manipulation risk (and preserve the Mobchart 100/day notification budget) by restricting alerts to a curated trading universe.

For the first iteration:

- **Universe = Top 100 *non-stablecoin* coins by market cap (CMC-style)**
- **Pairs = `*USDT`** only (spot and/or perps depending on venue feed)

This should bias the signal stream toward higher-liquidity, more widely-followed assets.

---

## Definitions

- **Universe asset**: a base asset symbol like `ETH`, `SOL`, `DOGE`.
- **Tradable pair**: `<BASE>USDT` (e.g., `ETHUSDT`).

Notes:
- Some exchanges use alternate symbols or prefixes/suffixes (e.g., `1000PEPEUSDT`). Those require mapping rules.
- Stablecoins may appear in top lists; we should exclude them by default.
- Wrapped assets may appear; we can include or exclude them explicitly depending on how Mobchart symbols them.

---

## How we source “Top 100 by market cap”

### Preferred: configurable universe provider

We should treat market-cap ranking as a *data dependency*, not hard-coded logic.

Proposed interface:

- `UniverseProvider.getUniverse()` → returns:
  - `base_assets: string[]` (e.g., `["BTC", "ETH", "SOL", ...]`)
  - metadata (rank, market cap, timestamp, source)

Implementations:

1) **Static snapshot (MVP-friendly)**
   - Store a checked-in file: `data/universe/top100.json`
   - Update manually (or via a scheduled job later)
   - Pros: no API keys; deterministic
   - Cons: can go stale

2) **CoinMarketCap API (CMC)**
   - Accurate “CMC-style” list
   - Requires API key + rate limits
   - Security note: keep keys out of analytics container if possible; or use a separate fetcher with least privilege.

3) **Alternative public sources** (if we want no paid API)
   - CoinGecko (free-ish; rate limited)
   - CoinPaprika (often easier; rate limited)

In all cases, the downstream logic should be identical.

---

## Enforcement points

### A) Upstream (preferred): Mobchart pair whitelist

Best option to preserve the 100/day alert budget:

- Configure Mobchart screener to whitelist only `Top100 ∩ USDT` pairs.

This avoids spending notifications on out-of-universe pairs.

### B) Ingest-time filtering (secondary)

Even with a Mobchart whitelist, ingestion should apply universe filtering as a safety net:

- Parse `symbol` (e.g., `DOTUSDT` → base `DOT`)
- Drop events where base asset not in universe
- Store dropped events optionally (for audit) with `filtered_reason="universe_excluded"`

---

## Edge cases / symbol normalization

We need a symbol normalization layer:

- `BASEUSDT` → base `BASE`
- `1000PEPEUSDT` → base `PEPE` (rule: strip leading multiplier tokens like `1000` when known)

Design choice:
- Start conservative: allow only plain `^[A-Z0-9]+USDT$` and require exact base match.
- Add mapping overrides as we observe real-world cases.

---

## Config (proposed)

```json
{
  "universe": {
    "provider": "static",
    "staticFile": "data/universe/top100.json",
    "quoteAsset": "USDT",
    "maxRank": 100,
    "excludeBases": ["USDT", "USDC", "DAI"],
    "symbolOverrides": {
      "1000PEPE": "PEPE"
    }
  }
}
```

---

## MVP decision

For the first iteration, implement **Static snapshot** and document the update procedure.

When we’re confident the pipeline is useful, swap the provider to a live source (CMC or alternative).
