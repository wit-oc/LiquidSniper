import pandas as pd

from intraday_revisit.research.vectorbt_adapter import AdapterInput, prepare_signals


def test_prepare_signals_ok():
    df = pd.DataFrame({"long_entry": [0, 1], "short_entry": [1, 0]})
    le, se = prepare_signals(AdapterInput(df=df))
    assert le.tolist() == [False, True]
    assert se.tolist() == [True, False]
