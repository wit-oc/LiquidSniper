from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _parse_ts(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _first_fail(run: dict[str, Any]) -> str:
    trail = run.get("gate_trail") if isinstance(run.get("gate_trail"), list) else []
    for node in trail:
        if not isinstance(node, dict):
            continue
        if node.get("ok") is False and isinstance(node.get("reason_code"), str):
            return str(node["reason_code"])
    codes = run.get("decision_reason_codes") if isinstance(run.get("decision_reason_codes"), list) else []
    return str(codes[0]) if codes else "ACCEPTED"


def build_summary(runs: list[dict[str, Any]], *, now: datetime) -> dict[str, Any]:
    windows = {"6h": now - timedelta(hours=6), "24h": now - timedelta(hours=24)}
    out: dict[str, Any] = {"generated_at": now.isoformat(), "windows": {}}
    for label, cutoff in windows.items():
        rows = [r for r in runs if (_parse_ts(r.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc)) >= cutoff]
        first_fail = Counter(_first_fail(r) for r in rows)
        reason_codes = Counter(code for r in rows for code in (r.get("decision_reason_codes") or []))
        funnel = {
            "total": len(rows),
            "score_gate_passed": sum(1 for r in rows if bool(r.get("score_gate_passed"))),
            "proposal_accepted": sum(1 for r in rows if r.get("proposal_decision") == "accepted"),
            "executed": sum(1 for r in rows if r.get("execution_decision") == "executed"),
        }
        out["windows"][label] = {
            "first_fail_distribution": dict(sorted(first_fail.items())),
            "reason_distribution": dict(sorted(reason_codes.items())),
            "funnel": funnel,
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", default="artifacts/paper_mvp/runs")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    runs = []
    if runs_dir.exists():
        for path in sorted(runs_dir.glob("*.json")):
            try:
                runs.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue

    payload = build_summary(runs, now=datetime.now(timezone.utc))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
