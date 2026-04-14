"""backtesting.py adapter scaffold for Intraday Revisit.

Defines transform contract from event logs into bar-level signal columns.
"""

from __future__ import annotations

import pandas as pd


def inject_event_columns(df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["long_entry"] = False
    out["short_entry"] = False

    if "index" not in events_df.columns or "event" not in events_df.columns:
        raise ValueError("events_df requires columns: index,event")

    for _, r in events_df.iterrows():
        i = int(r["index"])
        e = str(r["event"])
        if i < 0 or i >= len(out):
            continue
        if e == "enter_long":
            out.loc[i, "long_entry"] = True
        elif e == "enter_short":
            out.loc[i, "short_entry"] = True
    return out
