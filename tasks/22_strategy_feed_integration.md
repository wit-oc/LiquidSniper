# Task 22 — Strategy feed integration (canonical candles as baseline)

## Goal

Wire strategy scoring and HTF/POI analysis to canonical OHLCV data as the primary decision input.

## Deliverables

- Strategy/analysis path reads from canonical candle store for structure/POI features.
- Mobchart Telegram feed is treated as trigger/context overlay only.
- Explicit fail-closed behavior when required candle windows are unavailable.

## Acceptance criteria

- Strategy decisions can run with canonical candles present even if trigger feed is absent.
- Trigger feed can influence prioritization/context but cannot substitute missing candles.
- Replay harness includes cases proving decision behavior under feed-available vs feed-degraded scenarios.
