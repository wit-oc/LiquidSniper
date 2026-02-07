# Spec 07 — Docker / Ops

## Goal

Containerize Phase 1 so it runs via docker-compose.

## Services

- `ingestor`:
  - python runtime
  - mounts `/data` volume
  - runs `python -m liquidsniper.ingestor`

- `web`:
  - python runtime
  - mounts `/data` volume
  - runs `streamlit run liquidsniper/web/app.py --server.port=8501 --server.address=0.0.0.0`

## Files

- `Dockerfile` (shared base)
- `docker-compose.yml`
- `.env.example`

## Volumes

- named volume `liquidsniper_data` mounted to `/data`
- contains:
  - `liquidsniper.sqlite`
  - `telethon.session`

## Ports

- web exposed on `8501`

## Acceptance criteria

- `docker compose up --build` works.
- DB persists after restart.
- Session persists after restart.
