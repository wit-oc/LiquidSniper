# Legacy Telegram Ingestor

This package contains the original Telegram / Mobchart ingestion implementation
that used to live directly under `liquidsniper/ingestor/`.

Why it moved:
- the current repo center is Surveyor / Arbiter
- Telegram ingestion is retained only as a legacy capability
- keeping the implementation here makes the old surface explicit without breaking
  existing entrypoints

Compatibility:
- `liquidsniper.ingestor.main` remains as a thin shim
- existing calls like `python -m liquidsniper.ingestor.main ...` still work

See:
- `docs/SECOND_ARCHIVE_PASS_CODE_ARTIFACT_TRIAGE_2026-04-20.md`
- `docs/PASS3_LEGACY_CODE_RELOCATION_MATRIX_2026-04-20.md`
