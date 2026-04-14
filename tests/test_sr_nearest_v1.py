from __future__ import annotations

import json
from pathlib import Path

from liquidsniper.core.sr_engine_v2 import nearest_sr_levels_v1


def _zone(mid: float, *, tf: str = "1D", idx: int = 1) -> dict:
    width = max(mid * 0.01, 250.0)
    return {
        "zone_id": f"z-{tf}-{idx}-{int(mid)}",
        "symbol": "BTCUSDT",
        "tf": tf,
        "status": "confirmed",
        "zone_low": mid - (width * 0.5),
        "zone_high": mid + (width * 0.5),
        "zone_mid": mid,
        "touch_count": 4,
        "first_retest_result": "reject",
        "strength_score": 75.0,
    }


def test_nearest_sr_levels_v1_returns_expected_two_per_side() -> None:
    levels = [60000.0, 74000.0, 98000.0, 108000.0, 125000.0]
    zones = [_zone(mid, idx=i + 1) for i, mid in enumerate(levels)]

    q = nearest_sr_levels_v1(profile_id="S", entry=77200.0, zones=zones)

    assert q["nearest_support"] is not None
    assert q["next_support"] is not None
    assert q["nearest_resistance"] is not None
    assert q["next_resistance"] is not None

    nearest_support_mid = q["nearest_support"]["bounds"]["mid"]
    next_support_mid = q["next_support"]["bounds"]["mid"]
    nearest_res_mid = q["nearest_resistance"]["bounds"]["mid"]
    next_res_mid = q["next_resistance"]["bounds"]["mid"]

    assert nearest_support_mid == 74000.0
    assert next_support_mid == 60000.0
    assert nearest_res_mid == 98000.0
    assert next_res_mid == 108000.0


def test_btc_grey_zone_fixture_values_are_validation_only_targets() -> None:
    fixture_path = Path("tests/fixtures/sr/btc_grey_zone_targets_2026-03-08.json")
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert payload["symbol"] == "BTCUSDT"
    anchors = payload["anchors"]
    assert anchors == [60000, 74000, 98000, 108000, 125000]
    assert payload["tolerance_pct"] == 0.05
