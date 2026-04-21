from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


def _normalize_row(row: Dict[str, str]) -> dict:
    ts_key = "timestamp" if "timestamp" in row else "time"
    return {
        "timestamp": row.get(ts_key, ""),
        "open": float(row["open"]),
        "high": float(row["high"]),
        "low": float(row["low"]),
        "close": float(row["close"]),
        "volume": float(row.get("volume", 0.0) or 0.0),
    }


def load_ohlcv(path: str) -> List[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    if p.suffix.lower() == ".parquet":
        try:
            import pandas as pd  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Parquet requested but pandas/pyarrow not available") from exc
        df = pd.read_parquet(p)
        cols = {c.lower(): c for c in df.columns}
        required = ["open", "high", "low", "close"]
        missing = [c for c in required if c not in cols]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        rows = []
        for _, rec in df.iterrows():
            row = {
                "timestamp": str(rec.get(cols.get("timestamp", cols.get("time", df.columns[0])))),
                "open": float(rec[cols["open"]]),
                "high": float(rec[cols["high"]]),
                "low": float(rec[cols["low"]]),
                "close": float(rec[cols["close"]]),
                "volume": float(rec.get(cols.get("volume"), 0.0)) if "volume" in cols else 0.0,
            }
            rows.append(row)
        return rows

    with p.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV missing header")
        map_fields = {name.lower(): name for name in reader.fieldnames}
        data = []
        for row in reader:
            normalized = {k: row[v] for k, v in map_fields.items() if v in row}
            data.append(_normalize_row(normalized))
        return data
