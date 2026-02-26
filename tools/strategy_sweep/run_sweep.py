#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

from data_loader import load_ohlcv
from engine_v1 import run_backtest
from score import composite_score


HERE = Path(__file__).resolve().parent


def load_profiles(path: Path) -> Dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    # profiles.yaml is intentionally JSON-compatible YAML to avoid pyyaml dependency.
    return json.loads(text)


def frange(start: float, stop: float, step: float) -> Iterable[float]:
    x = start
    while x <= stop + 1e-12:
        yield round(x, 10)
        x += step


def sample_params(grid: Dict[str, dict], n: int, seed: int) -> List[Dict[str, float]]:
    random.seed(seed)
    fixed = {k: v for k, v in grid.items() if "value" in v}
    ranged = {k: v for k, v in grid.items() if "value" not in v}

    options = {}
    for k, spec in ranged.items():
        if spec["type"] == "int":
            options[k] = list(range(int(spec["min"]), int(spec["max"]) + 1, int(spec.get("step", 1))))
        else:
            options[k] = list(frange(float(spec["min"]), float(spec["max"]), float(spec.get("step", 0.1))))

    out: List[Dict[str, float]] = []
    seen = set()
    keys = list(options.keys())
    max_tries = max(n * 20, 200)

    tries = 0
    while len(out) < n and tries < max_tries:
        tries += 1
        combo = {k: random.choice(options[k]) for k in keys}
        combo_key = tuple((k, combo[k]) for k in sorted(combo.keys()))
        if combo_key in seen:
            continue
        seen.add(combo_key)
        merged = dict(combo)
        for fk, fv in fixed.items():
            merged[fk] = fv["value"]
        out.append(merged)

    if not out:
        out.append({k: v["value"] for k, v in fixed.items()})
    return out


def write_csv(path: Path, rows: List[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def run_profile(profile: str, profile_cfg: dict, rows: List[dict], samples: int, seed: int) -> List[dict]:
    params_list = sample_params(profile_cfg["params"], n=samples, seed=seed)
    results = []
    for idx, p in enumerate(params_list):
        merged = {
            **p,
            "profile": profile,
            "profile_risk_cap_pct": profile_cfg["constraints"]["profile_risk_cap_pct"],
            "max_notional_pct": profile_cfg["constraints"].get("max_notional_pct", 100.0),
            "initial_equity": profile_cfg["constraints"].get("initial_equity", 10_000.0),
        }
        metrics = run_backtest(rows, merged, seed=seed + idx)
        metrics["score"] = composite_score(metrics)
        results.append({**merged, **metrics})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="LiquidSniper Pine-v1-style strategy sweep scaffold")
    ap.add_argument("--data", required=True, help="Path to OHLCV csv/parquet")
    ap.add_argument("--profiles", default=str(HERE / "profiles.yaml"))
    ap.add_argument("--samples", type=int, default=80, help="max combinations sampled per profile")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(HERE / "outputs"))
    ap.add_argument("--only-profiles", default="C,I,S", help="comma-separated profiles to run, e.g. I")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_ohlcv(args.data)
    profiles = load_profiles(Path(args.profiles))

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data": str(Path(args.data).resolve()),
        "profiles": list(profiles.keys()),
        "samples": args.samples,
        "seed": args.seed,
    }

    selected = [p.strip() for p in args.only_profiles.split(",") if p.strip()]
    for i, profile in enumerate(selected):
        if profile not in profiles:
            raise ValueError(f"Unknown profile '{profile}'. Available: {sorted(profiles.keys())}")
        result_rows = run_profile(profile, profiles[profile], rows, args.samples, args.seed + i * 1000)
        write_csv(out_dir / f"leaderboard_{profile}.csv", result_rows)

    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Sweep complete. Artifacts in {out_dir}")


if __name__ == "__main__":
    main()
