from liquidsniper.core.sr_engine_v2 import build_zones_for_tf, nearest_sr_query


def _candles(base: float, n: int = 80):
    rows = []
    p = base
    for i in range(n):
        drift = (i % 7) - 3
        o = p
        h = p + 2 + (i % 3)
        l = p - 2 - ((i + 1) % 3)
        c = p + (drift * 0.2)
        rows.append({"open": o, "high": h, "low": l, "close": c, "close_time": f"2026-02-21T{i:02d}:00:00+00:00"})
        p = c + (0.1 if i % 2 == 0 else -0.05)
    return rows


def test_build_zones_for_tf_generates_zone_and_touches():
    zones, touches = build_zones_for_tf("BTCUSDT", "4H", _candles(100.0, 120))
    assert zones
    assert all(z["symbol"] == "BTCUSDT" for z in zones)
    assert all(z["tf"] == "4H" for z in zones)
    assert all("status" in z for z in zones)
    assert all("reaction_efficiency_score" in z for z in zones)
    assert all("spent_zone_penalty" in z for z in zones)
    assert touches


def test_nearest_sr_query_applies_profile_eligibility():
    zones = [
        {"zone_id": "z1", "tf": "1H", "status": "confirmed", "zone_low": 98.0, "zone_high": 99.0, "zone_mid": 98.5, "touch_count": 3, "first_retest_result": "reject", "strength_score": 60},
        {"zone_id": "z2", "tf": "1D", "status": "confirmed", "zone_low": 97.0, "zone_high": 98.0, "zone_mid": 97.5, "touch_count": 4, "first_retest_result": "reject", "strength_score": 80},
    ]
    q_swing = nearest_sr_query(profile_id="S", side="buy", entry=100.0, zones=zones)
    assert q_swing["sr_anchor_tf"] == "1D"
    assert q_swing["nearest_support"]["zone_id"] == "z2"
    assert "1H" not in q_swing["sr_eligible_tfs"]
