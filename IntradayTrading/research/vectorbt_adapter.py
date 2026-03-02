"""Vectorbt adapter scaffold for Intraday Revisit.

This file intentionally starts as a thin contract wrapper so we can lock
I/O expectations before plugging full vectorbt portfolio construction.
"""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass
class AdapterInput:
    df: pd.DataFrame
    long_entries_col: str = "long_entry"
    short_entries_col: str = "short_entry"


def prepare_signals(inp: AdapterInput) -> tuple[pd.Series, pd.Series]:
    if inp.long_entries_col not in inp.df.columns:
        raise ValueError(f"Missing column: {inp.long_entries_col}")
    if inp.short_entries_col not in inp.df.columns:
        raise ValueError(f"Missing column: {inp.short_entries_col}")
    return inp.df[inp.long_entries_col].astype(bool), inp.df[inp.short_entries_col].astype(bool)
