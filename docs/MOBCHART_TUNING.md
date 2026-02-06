# Mobchart tuning + signal budget

Mobchart’s Liquidity Screener is useful, but noisy. Our edge (if any) comes from:

- tight filters (reduce low-quality alerts)
- multi-exchange correlation
- disciplined TP/SL templates and time stops

## Constraint: Mobchart notification limit

There is a **100 events/day** Telegram notification cap.

Implications:
- we must be deliberate about which alerts we “spend” notifications on
- we should bias toward **high signal-to-noise** settings

## Knobs (as observed / documented)

These can be used to dial fidelity and reduce noise:

1) **Order distance to price (%)**
- Smaller distance → more actionable, fewer alerts
- Too small can be “late” if you need lead time

2) **Order lifespan** (how long it has existed)
- Longer lifespan tends to be more meaningful
- But very old levels can be “known” and fade in efficacy

3) **Order strength (%)**
- Prefer higher values
- Even 100% is not a guarantee; treat as a quality filter, not a signal by itself

4) **Order quantity distribution**
- More distribution groups suggests it’s not just one whale
- Hypothesis: broader distribution reduces spoof risk

5) **Liquidity size ($)**
- Larger size generally more relevant
- But note: size alone can attract “liquidity hunting” and fakeouts

6) **Estimated fill rate**
- If most of the order is already filled, the remaining wall may be weak

7) **Current order # of touches**
- Too many touches may mean the level is being chewed through
- Too few touches may mean it’s untested

8) **Order’s price level touches (last 12 hours)**
- Another measure of “was this level a magnet already?”

9) **Pair whitelist**
- Strongly recommended for MVP.
- Start with majors (BTC/ETH/SOL) and a small set of liquid alts.

10) **Pair blacklist**
- Exclude obvious manipulation magnets or low-liquidity pairs.

11) **Exclude unstable order quantities**
- Recommended ON to reduce spoof-like behavior.

12) **Order type**
- All vs buy-only vs sell-only.
- For reversal setups, both sides can matter; consider separate streams.

## Multi-exchange correlation (design intent)

Mobchart levels are exchange-specific. A stronger signal is when:

- two or more exchanges show a level near the same price (within tolerance),
  and/or
- both spot and perps show aligned levels.

We can’t compute this from a single-exchange feed alone.

### Practical approach (Phase 1 → Phase 2)

Phase 1:
- ingest + store all alerts we receive

Phase 2:
- group events by:
  - symbol
  - side (bid/ask)
  - time window (e.g. last 15m)
- cluster by level price:
  - define a tolerance (e.g. within 0.1% of each other)
- score clusters:
  - count of distinct exchanges
  - sum of liquidity_size_usd
  - min/avg strength bucket

The output is not an order; it’s an **“actionable cluster candidate”**.

## TP/SL addendum analysis (why it’s needed)

Because signals are hit-or-miss, the system must evaluate:

- What TP and SL templates would have worked historically?
- How often does price reverse enough to hit TP before invalidation?
- How often do we need time stops?

Early evaluation metrics:
- MFE/MAE over 30s, 2m, 5m, 15m windows
- probability of reaching TP before SL
- sensitivity to fees/slippage

## Recommended initial Mobchart settings (starting hypothesis)

Not final—just a direction to preserve the 100/day budget.

- Whitelist only: BTCUSDT, ETHUSDT, SOLUSDT (and add slowly)
- Distance to price: small (e.g. <= 1–2%)
- Strength: high (e.g. >= 80% or higher)
- Size: set a floor that ensures liquidity is meaningful for the pair
- Exclude unstable quantities: ON
- Consider requiring a minimum lifespan (avoid newborn levels)

We should iterate empirically by:
- tracking alert volume/day
- tracking post-alert price behavior
