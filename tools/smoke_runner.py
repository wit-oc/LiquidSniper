#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from pathlib import Path

from liquidsniper.core.watchlist_router import classify_symbol


def _run(cmd: list[str], cwd: str) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def _latest_symbol(db_path: str) -> str | None:
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT symbol FROM signal_events ORDER BY id DESC LIMIT 1").fetchone()
    return row[0] if row else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="@MobChartBot")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--db", default="data/liquidsniper.sqlite")
    ap.add_argument("--session", default="data/telegram_liquidsniper")
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()

    repo = str(Path(args.repo).resolve())

    rc, out, err = _run(
        [
            "python3",
            "-m",
            "liquidsniper.ingestor.main",
            "--source",
            args.source,
            "--limit",
            str(args.limit),
            "--once",
            "--db",
            args.db,
            "--session",
            args.session,
        ],
        cwd=repo,
    )
    if rc != 0:
        print(json.dumps({"stage": "ingest", "status": "failed", "stderr": err}, indent=2))
        return 1

    ingest_summary = out.splitlines()[-1] if out else "{}"
    try:
        ingest_obj = json.loads(ingest_summary.replace("'", '"'))
    except Exception:
        ingest_obj = {"raw": ingest_summary}

    sym = _latest_symbol(str(Path(repo) / args.db))
    if not sym:
        print(json.dumps({"stage": "ingest", "status": "ok", "ingest": ingest_obj, "note": "no parsed symbols yet"}, indent=2))
        return 0

    chartability = classify_symbol(sym, Path(repo) / "config/watchlists.json")

    tv_symbol = f"BINANCE:{chartability.normalized_symbol}"
    rc2, out2, err2 = _run(["node", "tools/tradingview_snapshots.mjs", tv_symbol, "artifacts/tradingview/snapshots"], cwd=repo)
    if rc2 != 0:
        print(json.dumps({"stage": "tv_snapshots", "status": "failed", "symbol": tv_symbol, "stderr": err2}, indent=2))
        return 1

    tv_obj = json.loads(out2)
    report = {
        "status": "ok",
        "source": args.source,
        "ingest": ingest_obj,
        "symbol": sym,
        "chartability": chartability.state,
        "tv_symbol": tv_symbol,
        "snapshots": tv_obj.get("results", []),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
