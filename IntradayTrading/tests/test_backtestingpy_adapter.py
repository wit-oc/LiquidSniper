import pandas as pd

from intraday_revisit.research.backtestingpy_adapter import inject_event_columns


def test_inject_event_columns():
    df = pd.DataFrame({"open": [1, 2, 3]})
    events = pd.DataFrame([
        {"index": 0, "event": "enter_long"},
        {"index": 2, "event": "enter_short"},
    ])
    out = inject_event_columns(df, events)
    assert out.loc[0, "long_entry"]
    assert out.loc[2, "short_entry"]
