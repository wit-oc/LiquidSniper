# Signal Delivery + Paper-Trade Dry Run (MVP v1)

## What this adds

- Canonical payload rendering for:
  - Discord
  - iMessage
- Deterministic confidence banding from final score
- Local paper-trade journal (`jsonl`) for dry-run auditing

## Files

- `liquidsniper/core/signal_delivery.py`
- `liquidsniper/core/paper_trade.py`
- `tests/test_signal_delivery_and_paper_trade.py`
- `tests/fixtures/signal_snapshot_expected.json`

## Local verification

```bash
python3 -m pytest -q tests/test_signal_delivery_and_paper_trade.py
```
