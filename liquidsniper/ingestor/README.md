# Legacy Surface Note

`liquidsniper/ingestor/` is now a legacy-compatibility path retained during the Surveyor / Arbiter refocus.

Why it still exists:
- existing entrypoints still reference this package path
- related parser, migration, Docker/Makefile, and smoke-test surfaces still exist
- the real implementation was moved to `legacy/telegram_ingestor/`

Current posture:
- not part of the primary repo center
- kept as a thin shim to avoid breaking imports/tests while cleanup continues

See:
- `docs/LEGACY_SURFACES_STATUS_2026-04-19.md`
- `docs/SECOND_ARCHIVE_PASS_CODE_ARTIFACT_TRIAGE_2026-04-20.md`
- `docs/PASS3_LEGACY_CODE_RELOCATION_MATRIX_2026-04-20.md`
