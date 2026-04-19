from __future__ import annotations

from dataclasses import dataclass
from math import sin

from intraday_revisit.engine.dynamic_levels import (
    DynamicLevelConfig,
    PriceSide,
    ZoneRelation,
    build_dynamic_level_packet,
    classify_price_side,
    classify_zone_relation,
)
from intraday_revisit.engine.zones import Zone, ZoneKind


@dataclass
class SyntheticBar:
    index: int
    open: float
    high: float
    low: float
    close: float
    timestamp: int
    volume: float


def _make_hourly_bars(count: int, *, start_ts: int = 1735689600, base: float = 100.0) -> list[SyntheticBar]:
    bars: list[SyntheticBar] = []
    last_close = base
    for i in range(count):
        wave = sin(i / 18.0) * 1.8
        close = base + (i * 0.12) + wave
        open_ = last_close
        high = max(open_, close) + 1.2
        low = min(open_, close) - 1.1
        volume = 1000.0 + ((i % 24) * 10.0)
        bars.append(
            SyntheticBar(
                index=i,
                open=open_,
                high=high,
                low=low,
                close=close,
                timestamp=start_ts + (i * 3600),
                volume=volume,
            )
        )
        last_close = close
    return bars


def test_build_dynamic_level_packet_emits_raw_certified_surfaces():
    bars = _make_hourly_bars(24 * 420)
    current_price = bars[-1].close
    zone = Zone(id="z1", kind=ZoneKind.SUPPORT, low=current_price - 18.0, high=current_price - 8.0, created_at=0)

    packet = build_dynamic_level_packet(
        bars,
        as_of_bar_index=len(bars) - 1,
        symbol="BTC",
        base_tf="1h",
        intended_direction="bullish",
        selected_zone=zone,
        source_contract_version="phase2a3.dynamic_levels.v2.raw_only",
        fib_context_id="fib:example",
    )

    assert packet.feed_provider == "OKX"
    assert packet.current_price == current_price
    assert packet.zone_id == "z1"
    assert packet.source_contract_version == "phase2a3.dynamic_levels.v2.raw_only"
    assert len(packet.levels) == 10

    lookup = {(level["timeframe"], level["level_name"]): level for level in packet.levels}
    timeframe_levels = {
        "4h": ("YVWAP", "QVWAP", "EMA200", "EMA12"),
        "1d": ("YVWAP", "QVWAP", "RYVWAP", "RQVWAP", "EMA200", "EMA12"),
    }
    for timeframe, level_names in timeframe_levels.items():
        for level_name in level_names:
            level = lookup[(timeframe, level_name)]
            assert level["available"] is True
            assert level["level_value"] is not None
            assert level["price_side"] in {"above", "below", "overlapping"}
            assert level["zone_relation"] in {
                "above_zone",
                "below_zone",
                "inside_zone",
                "overlapping_zone",
                "near_zone",
                "far_from_zone",
            }
            assert level["distance_abs"] is not None
            assert level["distance_pct"] is not None
            assert level["timeframe_bar_ts"] is not None
            assert level["availability_reason"] is None
            assert "watcher_label" not in level
            assert "strength_hint" not in level

    assert ("4h", "RYVWAP") not in lookup
    assert ("4h", "RQVWAP") not in lookup
    assert lookup[("1d", "RYVWAP")]["level_value"] != lookup[("1d", "YVWAP")]["level_value"]
    assert lookup[("1d", "RQVWAP")]["level_value"] != lookup[("1d", "QVWAP")]["level_value"]

    assert not hasattr(packet, "dynamic_context_label")
    assert not hasattr(packet, "macro_context_label")
    assert not hasattr(packet, "local_flow_label")
    assert not hasattr(packet, "contrary_macro_present")


def test_price_side_and_zone_relation_classifiers_cover_expected_cases():
    cfg = DynamicLevelConfig(price_overlap_bps=10.0, zone_overlap_bps=10.0, near_zone_bps=30.0, far_zone_bps=120.0)

    assert classify_price_side(100.0, 95.0, cfg) == PriceSide.ABOVE.value
    assert classify_price_side(100.0, 105.0, cfg) == PriceSide.BELOW.value
    assert classify_price_side(100.0, 100.05, cfg) == PriceSide.OVERLAPPING.value

    assert classify_zone_relation(120.0, 100.0, 110.0, cfg) == ZoneRelation.FAR_FROM_ZONE.value
    assert classify_zone_relation(109.0, 100.0, 110.0, cfg) == ZoneRelation.INSIDE_ZONE.value
    assert classify_zone_relation(110.05, 100.0, 110.0, cfg) == ZoneRelation.OVERLAPPING_ZONE.value
    assert classify_zone_relation(110.2, 100.0, 110.0, cfg) == ZoneRelation.NEAR_ZONE.value
    assert classify_zone_relation(110.5, 100.0, 110.0, cfg) == ZoneRelation.ABOVE_ZONE.value
    assert classify_zone_relation(99.5, 100.0, 110.0, cfg) == ZoneRelation.BELOW_ZONE.value


def test_vwap_surfaces_fail_cleanly_when_history_is_insufficient():
    bars = _make_hourly_bars(24 * 20, start_ts=1740787200)  # 2025-03-01 UTC
    packet = build_dynamic_level_packet(
        bars,
        as_of_bar_index=len(bars) - 1,
        symbol="BTC",
        base_tf="1h",
        intended_direction="bullish",
        selected_zone=None,
    )

    lookup = {(level["timeframe"], level["level_name"]): level for level in packet.levels}
    assert lookup[("4h", "YVWAP")]["available"] is False
    assert lookup[("1d", "YVWAP")]["available"] is False
    assert lookup[("4h", "YVWAP")]["availability_reason"] == "incomplete_anchor_history"
    assert lookup[("4h", "QVWAP")]["availability_reason"] == "incomplete_anchor_history"
    assert lookup[("1d", "RYVWAP")]["available"] is False
    assert lookup[("1d", "RYVWAP")]["availability_reason"] == "insufficient_history_for_rolling_vwap_365"
    assert lookup[("1d", "RQVWAP")]["available"] is False
    assert lookup[("1d", "RQVWAP")]["availability_reason"] == "insufficient_history_for_rolling_vwap_90"
    assert lookup[("4h", "EMA12")]["availability_reason"] is None
