from intraday_revisit.engine.logger import normalize_event


def test_normalize_event_keyset_stable():
    event = {
        "index": 1,
        "symbol": "BTC",
        "action": "enter_long",
        "extra": "ignored",
    }
    out = normalize_event(event)
    assert out["index"] == 1
    assert out["symbol"] == "BTC"
    assert out["action"] == "enter_long"
    assert "extra" not in out


def test_normalize_event_preserves_dynamic_levels_payload():
    event = {
        "index": 2,
        "symbol": "BTC",
        "action": "none",
        "dynamic_levels": {
            "dynamic_4h_yvwap_available": True,
            "dynamic_4h_yvwap_value": 101.25,
        },
    }
    out = normalize_event(event)
    assert out["dynamic_levels"]["dynamic_4h_yvwap_available"] is True
    assert out["dynamic_levels"]["dynamic_4h_yvwap_value"] == 101.25
