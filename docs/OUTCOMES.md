# Outcomes + trade/evaluation labels

We want a quick way to tag signals (and later trade intents) with outcomes so we can learn.

Phase 1 is mostly **paper** / manual review, but the schema should be compatible with Phase 2 evaluation.

## Outcome labels (v0)

Suggested controlled vocabulary:

- `SKIPPED` — reviewed, did not take
- `STOPPED_OUT` — trade (paper or live) hit stop
- `TAKE_PROFIT` — trade hit TP
- `WIN_BUT_BAD_STOPS` — would have worked with slightly better stop placement
- `LOSS_BUT_BAD_ENTRY` — would have worked with better entry timing/price
- `AMBIGUOUS` — unclear / noisy / needs deeper review

## Outcome record (proposed)

Store outcome annotations separately from signal events (append-only), referencing a signal event.

```json
{
  "kind": "outcome_annotation",
  "ts": "2026-02-06T16:00:00Z",
  "signal_ref": {
    "chat_id": "<string>",
    "message_id": "<string>",
    "line_index": 0
  },
  "label": "STOPPED_OUT",
  "notes": "Entered on first touch; stop too tight; second retest would have worked.",
  "template_version": "mvp-v0.1",
  "paper": true
}
```

## Why separate annotations

- We never mutate raw signals.
- Multiple reviewers/iterations can attach multiple annotations.
- We can later attach computed metrics (MFE/MAE) without overwriting human tags.

## Future (Phase 2+)

Add optional structured fields:
- `entry_price`, `stop_price`, `tp_price`
- `rr` (risk-reward)
- `max_drawdown` during trade
- `time_in_trade`
