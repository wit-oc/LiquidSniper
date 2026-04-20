"""Compatibility shim for the legacy Telegram/Mobchart ingestor entrypoint.

Usage remains:
  python -m liquidsniper.ingestor.main --source @MobChartBot --limit 20 --once
"""

from legacy.telegram_ingestor.main import ingest_once, main


if __name__ == "__main__":
    raise SystemExit(main())
