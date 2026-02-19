# Telegram Ingestor Integration Hardening (Task 05)

## Scope

Task 05 closes ingestion wiring gaps so each parsed signal line can flow into both:

1. `signal_events` (raw parsed event persistence)
2. card/confluence state (`cards`, `confluences`) for downstream diagnostic UI

Python baseline for this repo is **3.11+**.

## Runtime flow

For each Telegram message:

1. Insert/resolve `raw_telegram_messages` by `(telegram_chat_id, telegram_message_id)`.
2. Parse message text with `parse_mobchart_message(...)`.
3. For each parsed signal row:
   - skip `ignored_line`
   - count `parse_error`
   - `INSERT OR IGNORE` into `signal_events` by `(raw_message_id, line_index)`
   - resolve `signal_events.id`
   - append card confluence via `record_event_confluence(...)` with `source_event_id`

## Failure-path handling

Ingest loop is hardened to keep processing when one row fails:

- `sqlite3` errors while writing `signal_events` increment `persist_errors` and continue.
- `sqlite3` or validation errors while writing card/confluence rows increment `persist_errors` and continue.
- Parse errors are tracked separately (`parse_errors`) and do not abort loop.

This keeps runs auditable without dropping the full batch because of one malformed or conflicting row.

## First-run login path (no code secrets)

Telethon needs an authenticated session file on first run:

```bash
python -m liquidsniper.ingestor.main \
  --source @MobChartBot \
  --limit 20 \
  --once \
  --db data/liquidsniper.sqlite \
  --session data/telegram_liquidsniper
```

- On first run, Telethon may prompt for phone/code in terminal.
- Session state is persisted under `--session` path for future headless runs.
- Required secrets:
  - `LIQUIDSNIPER_TELEGRAM_API_ID`
  - `LIQUIDSNIPER_TELEGRAM_API_HASH`
- Secrets may come from env vars or local keychain lookup in this ingestor.

## Run summary fields

`ingest_once(...)` now reports:

- `raw_messages`
- `parsed_events`
- `parse_errors`
- `ignored_lines`
- `confluences_written`
- `persist_errors`
