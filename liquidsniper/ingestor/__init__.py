"""Legacy-compatibility shim for the Telegram/Mobchart ingestor package."""

from legacy.telegram_ingestor import ingest_once, main

__all__ = ["ingest_once", "main"]
