# Task 07 — Docker + compose

## Goal

Containerize ingestor + web per Spec 07.

## Deliverables

- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- Named volume `liquidsniper_data` mounted at `/data` for:
  - `liquidsniper.sqlite`
  - `telethon.session`
- Basic health/status logging

## Acceptance criteria

- `docker compose up --build` starts both services
- DB + session persist across restart
