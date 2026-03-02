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
