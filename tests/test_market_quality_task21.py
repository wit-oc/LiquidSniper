from __future__ import annotations

import pytest

from liquidsniper.core.market_data import CandleDTO, CandleValidationError
from liquidsniper.core.market_quality import aggregate_timeframe_candles, enforce_candle_quality


def _candle(ts_open_ms: int, *, timeframe: str = "1m", close: str = "100.5", volume: str = "10") -> CandleDTO:
    tf_ms = {"1m": 60_000, "5m": 300_000}[timeframe]
    return CandleDTO(
        provider_id="ccxt",
        venue="binance",
        symbol="BTC/USDT",
        timeframe=timeframe,
        ts_open_ms=ts_open_ms,
        ts_close_ms=ts_open_ms + tf_ms,
        open="100",
        high="101",
        low="99",
        close=close,
        volume=volume,
        dataset_version="v1",
        trace_id="t",
    )


def test_quality_gate_dedupes_identical_timestamp_rows():
    candles = [_candle(60_000), _candle(60_000), _candle(120_000)]

    out = enforce_candle_quality(candles, timeframe="1m", now_ms=170_000)

    assert [c.ts_open_ms for c in out.candles] == [60_000, 120_000]
    assert out.reason_codes == ["CANDLE_DEDUPED"]


def test_quality_gate_rejects_gap_and_stale_windows():
    with pytest.raises(CandleValidationError) as gap_exc:
        enforce_candle_quality([_candle(60_000), _candle(180_000)], timeframe="1m", now_ms=200_000)
    assert gap_exc.value.reason_code == "CANDLE_GAP_DETECTED"

    with pytest.raises(CandleValidationError) as stale_exc:
        enforce_candle_quality([_candle(60_000), _candle(120_000)], timeframe="1m", now_ms=500_000)
    assert stale_exc.value.reason_code == "CANDLE_STALE_WINDOW"


def test_aggregate_timeframe_builds_deterministic_5m_candle():
    ones = [
        _candle(0, close="101", volume="1"),
        _candle(60_000, close="102", volume="2"),
        _candle(120_000, close="103", volume="3"),
        _candle(180_000, close="104", volume="4"),
        _candle(240_000, close="105", volume="5"),
    ]

    out = aggregate_timeframe_candles(
        ones,
        from_timeframe="1m",
        to_timeframe="5m",
        dataset_version="v1-agg",
        trace_id="agg-trace",
    )

    assert len(out) == 1
    candle = out[0]
    assert candle.timeframe == "5m"
    assert candle.ts_open_ms == 0
    assert candle.ts_close_ms == 300_000
    assert candle.open == "100"
    assert candle.close == "105"
    assert candle.high == "101"
    assert candle.low == "99"
    assert candle.volume == "15"
    assert candle.dataset_version == "v1-agg"
    assert candle.trace_id == "agg-trace"


def test_aggregate_timeframe_skips_incomplete_bucket():
    out = aggregate_timeframe_candles(
        [_candle(0), _candle(60_000), _candle(120_000), _candle(180_000)],
        from_timeframe="1m",
        to_timeframe="5m",
        dataset_version="v1-agg",
        trace_id="agg-trace",
    )
    assert out == []
