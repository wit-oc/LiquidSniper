from intraday_revisit.research.first_pass_metrics import Trade, summarize


def test_summarize_basic():
    trades = [
        Trade(side="long", entry_index=0, entry_price=100, exit_index=1, exit_price=110),
        Trade(side="long", entry_index=2, entry_price=100, exit_index=3, exit_price=95),
    ]
    s = summarize(trades)
    assert s["trades"] == 2
    assert s["wins"] == 1
    assert s["losses"] == 1
    assert s["pf"] > 0
