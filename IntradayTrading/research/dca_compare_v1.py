from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from intraday_revisit.engine.runner import Bar, RunnerConfig, SignalRunner
from intraday_revisit.engine.structure import StructureBias, classify_structure_from_pivots, detect_pivots
from intraday_revisit.engine.zones_builder import build_zones_from_candles

FEE_BPS = 5.0
SLIPPAGE_BPS = 2.0
FUNDING_BPS_8H = 1.0
INITIAL_EQUITY = 10_000.0

OUT_DIR = Path("artifacts/sweeps/dca_compare_v1")

# Best post-instrumentation/desaturated profile from recent autonomy sweep.
BASELINE_PARAMS = {
    "zone_width": 0.0015,
    "retest_max_bars": 8,
    "reclaim_buffer_frac": 0.00035,
    "momentum_min_frac": 0.0012,
    "trend_slope_min": 0.0002,
    "chop_slope_abs_max": 0.00012,
    "strict_retest_bps_max": 18.0,
    "near_retest_bps_max": 24.0,
    "score_gate_min": 5.8,
    "risk_pct_high_conf": 1.6,
    "trigger_score_min": 7.2,
    "stop_buffer_frac": 0.0013,
    "rr_tp2": 2.2,
    "near_retest_penalty_max": 0.8,
}


@dataclass(frozen=True)
class TranchePlan:
    name: str
    # (adverse_move_to_stop_frac, risk_weight)
    levels: tuple[tuple[float, float], ...]


PLANS = {
    "baseline": TranchePlan("baseline", ((0.0, 1.0),)),
    "dca_50_50": TranchePlan("dca_50_50", ((0.0, 0.5), (0.5, 0.5))),
    "dca_30_30_40": TranchePlan("dca_30_30_40", ((0.0, 0.3), (0.33, 0.3), (0.66, 0.4))),
}


def load_ohlcv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path).sort_values("timestamp").reset_index(drop=True)


def resample_4h(df_1h: pd.DataFrame) -> pd.DataFrame:
    d = df_1h.copy()
    d["ts"] = pd.to_datetime(d["timestamp"], unit="s", utc=True)
    d = d.set_index("ts")
    out = pd.DataFrame()
    out["open"] = d["open"].resample("4h").first()
    out["high"] = d["high"].resample("4h").max()
    out["low"] = d["low"].resample("4h").min()
    out["close"] = d["close"].resample("4h").last()
    out = out.dropna().reset_index()
    out["timestamp"] = out["ts"].astype("int64") // 10**9
    return out[["timestamp", "open", "high", "low", "close"]]


def bias_map_from_4h(df_4h: pd.DataFrame, df_1h: pd.DataFrame) -> dict[int, StructureBias]:
    pivots = detect_pivots(df_4h["high"].tolist(), df_4h["low"].tolist(), left=2, right=2)
    points = classify_structure_from_pivots(pivots)
    bias_by_ts = {int(df_4h.iloc[p.index]["timestamp"]): p.bias for p in points}
    keys = sorted(bias_by_ts.keys())
    current = StructureBias.NEUTRAL
    mapped: dict[int, StructureBias] = {}
    ki = 0
    for i, row in df_1h.iterrows():
        ts = int(row["timestamp"])
        while ki < len(keys) and keys[ki] <= ts:
            current = bias_by_ts[keys[ki]]
            ki += 1
        mapped[i] = current
    return mapped


def run_events(df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> list[dict]:
    cfg = RunnerConfig(
        allow_neutral_bias=False,
        max_zone_width_frac=0.03,
        reclaim_buffer_frac=BASELINE_PARAMS["reclaim_buffer_frac"],
        retest_max_bars=BASELINE_PARAMS["retest_max_bars"],
        require_retest_sequence=True,
        enable_swing_location_gate=True,
        long_location_max=0.82,
        short_location_min=0.18,
        enable_momentum_gate=True,
        momentum_min_frac=BASELINE_PARAMS["momentum_min_frac"],
        enable_chop_gate=True,
        chop_slope_abs_max=BASELINE_PARAMS["chop_slope_abs_max"],
        trend_slope_min=BASELINE_PARAMS["trend_slope_min"],
        min_rejection_wick_frac=0.0006,
        min_body_frac=0.0005,
        atr_floor_frac=0.0009,
        strict_retest_bps_max=BASELINE_PARAMS["strict_retest_bps_max"],
        near_retest_bps_max=BASELINE_PARAMS["near_retest_bps_max"],
        near_retest_penalty_max=BASELINE_PARAMS["near_retest_penalty_max"],
        enable_confluence_gate=True,
        score_gate_min=BASELINE_PARAMS["score_gate_min"],
        trigger_score_min=BASELINE_PARAMS["trigger_score_min"],
        stop_buffer_frac=BASELINE_PARAMS["stop_buffer_frac"],
        rr_tp2=BASELINE_PARAMS["rr_tp2"],
        risk_pct_low_conf=1.0,
        risk_pct_high_conf=BASELINE_PARAMS["risk_pct_high_conf"],
        high_conf_score_threshold=8.0,
    )
    zones = build_zones_from_candles(df_4h["high"].tolist(), df_4h["low"].tolist(), width_frac=BASELINE_PARAMS["zone_width"])
    bmap = bias_map_from_4h(df_4h, df_1h)
    bars = [Bar(index=i, open=r.open, high=r.high, low=r.low, close=r.close) for i, r in df_1h.iterrows()]
    runner = SignalRunner(cfg)
    events, _ = runner.run_with_logs(bars, bmap, zones)
    return events


def _price_for_level(side: str, entry: float, stop: float, level: float) -> float:
    # Level is normalized adverse progress from entry (0.0) toward stop (1.0).
    if side == "long":
        return entry - (entry - stop) * level
    return entry + (stop - entry) * level


def _trigger_index(side: str, closes: pd.Series, start_idx: int, end_idx: int, trigger_price: float) -> int | None:
    for i in range(start_idx, end_idx + 1):
        c = float(closes.iloc[i])
        if side == "long" and c <= trigger_price:
            return i
        if side == "short" and c >= trigger_price:
            return i
    return None


def _cost(units: float, entry_price: float, hold_bars: int) -> float:
    notional_ref = entry_price * units
    roundtrip_bps = 2.0 * (FEE_BPS + SLIPPAGE_BPS)
    fee_slip = notional_ref * (roundtrip_bps / 10_000.0)
    funding = notional_ref * ((FUNDING_BPS_8H / 10_000.0) * (max(hold_bars, 0) / 8.0))
    return fee_slip + funding


def build_trade_records(events: list[dict], closes: pd.Series) -> list[dict[str, Any]]:
    open_longs: list[dict[str, Any]] = []
    open_shorts: list[dict[str, Any]] = []
    closed: list[dict[str, Any]] = []

    for e in events:
        idx = int(e["index"])
        ev = e["event"]
        price = float(closes.iloc[idx])

        if ev == "enter_long":
            entry = float(e.get("entry", price))
            stop = float(e.get("stop", entry * (1 - 0.001)))
            open_longs.append(
                {
                    "side": "long",
                    "entry_index": idx,
                    "entry_price": entry,
                    "stop_price": stop,
                    "risk_pct": float(e.get("risk_pct", 1.0)),
                }
            )
        elif ev == "enter_short":
            entry = float(e.get("entry", price))
            stop = float(e.get("stop", entry * (1 + 0.001)))
            open_shorts.append(
                {
                    "side": "short",
                    "entry_index": idx,
                    "entry_price": entry,
                    "stop_price": stop,
                    "risk_pct": float(e.get("risk_pct", 1.0)),
                }
            )
        elif ev in ("exit_stop", "exit_tp2"):
            side = e.get("side")
            if side == "long" and open_longs:
                t = open_longs.pop(0)
                t["exit_index"] = idx
                t["exit_price"] = price
                t["exit_event"] = ev
                closed.append(t)
            elif side == "short" and open_shorts:
                t = open_shorts.pop(0)
                t["exit_index"] = idx
                t["exit_price"] = price
                t["exit_event"] = ev
                closed.append(t)

    return closed


def _simulate_trade_net(tr: dict[str, Any], closes: pd.Series, plan: TranchePlan) -> float | None:
    side = str(tr["side"])
    entry_idx = int(tr["entry_index"])
    exit_idx = int(tr["exit_index"])
    stop_price = float(tr["stop_price"])
    rr = BASELINE_PARAMS["rr_tp2"]

    tranche_defs: list[dict[str, Any]] = []
    for level, weight in plan.levels:
        px = _price_for_level(side, float(tr["entry_price"]), stop_price, float(level))
        tranche_defs.append({"level": float(level), "weight": float(weight), "entry_price": px, "filled": False, "fill_idx": None})

    active: list[dict[str, Any]] = []

    def blended_entry(fills: list[dict[str, Any]]) -> float:
        if not fills:
            return float(tr["entry_price"])
        # Planning assumption for RR design: intended risk split by weight; units use fixed stop distance.
        num = 0.0
        den = 0.0
        for f in fills:
            risk_per_unit = abs(float(f["entry_price"]) - stop_price)
            if risk_per_unit <= 0:
                continue
            units = float(f["weight"]) / risk_per_unit
            num += float(f["entry_price"]) * units
            den += units
        return (num / den) if den > 0 else float(tr["entry_price"])

    last_tp: float | None = None

    for i in range(entry_idx, exit_idx + 1):
        c = float(closes.iloc[i])

        # Existing filled size exits first (execution realism on currently filled size).
        if active:
            if side == "long" and c <= stop_price:
                exit_price = stop_price
                tr["exit_eff_index"] = i
                break
            if side == "short" and c >= stop_price:
                exit_price = stop_price
                tr["exit_eff_index"] = i
                break
            if last_tp is not None:
                if side == "long" and c >= last_tp:
                    exit_price = last_tp
                    tr["exit_eff_index"] = i
                    break
                if side == "short" and c <= last_tp:
                    exit_price = last_tp
                    tr["exit_eff_index"] = i
                    break

        # Fill any pending DCA tranches at this close.
        newly_filled = False
        for td in tranche_defs:
            if td["filled"]:
                continue
            tp = float(td["entry_price"])
            if (side == "long" and c <= tp) or (side == "short" and c >= tp):
                td["filled"] = True
                td["fill_idx"] = i
                active.append(td)
                newly_filled = True

        # Recalculate TP after each DCA fill from current blended entry and fixed stop.
        if newly_filled and active:
            be = blended_entry(active)
            if side == "long":
                last_tp = be + rr * (be - stop_price)
            else:
                last_tp = be - rr * (stop_price - be)

            # Same-bar TP check after fill (close-based approximation).
            if side == "long" and c >= last_tp:
                exit_price = last_tp
                tr["exit_eff_index"] = i
                break
            if side == "short" and c <= last_tp:
                exit_price = last_tp
                tr["exit_eff_index"] = i
                break
    else:
        # Fallback to original signal exit if no simulated stop/TP was hit.
        exit_price = float(tr["exit_price"])

    if not active:
        return None

    total_risk_weight = sum(float(a["weight"]) for a in active)
    signal_net = 0.0
    for a in active:
        risk_per_unit = abs(float(a["entry_price"]) - stop_price)
        if risk_per_unit <= 0:
            continue
        units = (float(tr["risk_amount"]) * float(a["weight"])) / risk_per_unit
        if units <= 0:
            continue
        if side == "long":
            gross = (exit_price - float(a["entry_price"])) * units
        else:
            gross = (float(a["entry_price"]) - exit_price) * units
        hold_bars = max(int(tr["exit_eff_index"]) - int(a["fill_idx"]), 0)
        signal_net += gross - _cost(units, float(a["entry_price"]), hold_bars)

    tr["filled_weight"] = total_risk_weight
    return signal_net


def summarize_with_plan(trades: list[dict[str, Any]], closes: pd.Series, plan: TranchePlan) -> dict:
    equity = INITIAL_EQUITY
    peak = INITIAL_EQUITY
    max_dd = 0.0
    max_dd_pct = 0.0
    pnls: list[float] = []

    for tr in trades:
        tr["risk_amount"] = equity * (max(float(tr["risk_pct"]), 0.0) / 100.0)
        tr["exit_eff_index"] = int(tr["exit_index"])
        pnl = _simulate_trade_net(tr, closes, plan)
        if pnl is None:
            continue
        pnls.append(pnl)
        equity += pnl
        peak = max(peak, equity)
        dd = peak - equity
        max_dd = max(max_dd, dd)
        max_dd_pct = max(max_dd_pct, (dd / peak) * 100.0 if peak > 0 else 0.0)

    if not pnls:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "pf": 0.0,
            "net": 0.0,
            "max_dd": 0.0,
            "max_dd_pct": 0.0,
            "final_equity": INITIAL_EQUITY,
        }

    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    wins = sum(1 for p in pnls if p > 0)
    losses = sum(1 for p in pnls if p < 0)
    pf = gross_profit / gross_loss if gross_loss > 0 else 0.0

    return {
        "trades": len(pnls),
        "wins": wins,
        "losses": losses,
        "win_rate": wins / max(len(pnls), 1),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "pf": pf,
        "net": sum(pnls),
        "max_dd": max_dd,
        "max_dd_pct": max_dd_pct,
        "final_equity": equity,
    }


def eval_symbol(df_1h: pd.DataFrame, events: list[dict], plan: TranchePlan) -> dict:
    trades = build_trade_records(events, df_1h["close"])
    return summarize_with_plan(trades, df_1h["close"], plan)


def pack_result(name: str, btc: dict, eth: dict) -> dict:
    out = {
        "model": name,
        "params": BASELINE_PARAMS,
        "fill_formula": {
            "description": "Signal unchanged; split per-trade risk across tranche limits placed from entry toward stop by adverse-move fraction. Stop remains fixed at original invalidation. TP is recalculated after each realized tranche fill from current blended entry and fixed stop, using RR=rr_tp2.",
            "levels": [{"adverse_frac_to_stop": lv, "risk_weight": wt} for lv, wt in PLANS[name].levels],
            "risk_rule": "sum(tranche risk weights)=1.0, so full-planned stop loss equals configured per-trade risk_pct and never exceeds it.",
            "planning_assumption": "RR design assumes intended tranches fill; execution may exit early on partial filled size if TP is reached before full DCA completion.",
        },
        "btc": btc,
        "eth": eth,
    }
    out["avg_pf"] = (btc["pf"] + eth["pf"]) / 2.0
    out["worst_dd_pct"] = max(btc["max_dd_pct"], eth["max_dd_pct"])
    out["total_trades"] = btc["trades"] + eth["trades"]
    out["avg_win_rate"] = (btc["win_rate"] + eth["win_rate"]) / 2.0
    out["total_net"] = btc["net"] + eth["net"]
    return out


def delta_line(metric: str, base: float, other: float, pct: bool = False, scale: float = 1.0) -> str:
    b = base * scale
    o = other * scale
    d = o - b
    sign = "+" if d >= 0 else ""
    suffix = "%" if pct else ""
    return f"- {metric}: {b:.4f}{suffix} -> {o:.4f}{suffix} ({sign}{d:.4f}{suffix})"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    btc_df = load_ohlcv(Path("data/btc_1h_blofin_2022_to_now.csv"))
    eth_df = load_ohlcv(Path("data/eth_1h_blofin_2022_to_now.csv"))
    btc_4h = resample_4h(btc_df)
    eth_4h = resample_4h(eth_df)

    btc_events = run_events(btc_df, btc_4h)
    eth_events = run_events(eth_df, eth_4h)

    baseline = pack_result(
        "baseline",
        eval_symbol(btc_df, btc_events, PLANS["baseline"]),
        eval_symbol(eth_df, eth_events, PLANS["baseline"]),
    )
    dca_50 = pack_result(
        "dca_50_50",
        eval_symbol(btc_df, btc_events, PLANS["dca_50_50"]),
        eval_symbol(eth_df, eth_events, PLANS["dca_50_50"]),
    )
    dca_334 = pack_result(
        "dca_30_30_40",
        eval_symbol(btc_df, btc_events, PLANS["dca_30_30_40"]),
        eval_symbol(eth_df, eth_events, PLANS["dca_30_30_40"]),
    )

    (OUT_DIR / "baseline.json").write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    (OUT_DIR / "dca_50_50.json").write_text(json.dumps(dca_50, indent=2), encoding="utf-8")
    (OUT_DIR / "dca_30_30_40.json").write_text(json.dumps(dca_334, indent=2), encoding="utf-8")

    lines = [
        "# DCA comparison v1",
        "",
        "Baseline source: artifacts/sweeps/miniwave_v2_1_autonomy/iter_2026-02-28-1900_stop_buffer_frac_0p0013.json (best post-instrumentation avg_pf).",
        "",
        "## Fill model",
        "- Signal generation unchanged (same entries from runner).",
        "- DCA triggers are adverse-move fractions from entry toward fixed invalidation stop, evaluated on close prices.",
        "- TP is recalculated after each realized fill from updated blended entry and fixed stop using RR=rr_tp2.",
        "- Planning assumption for RR design: intended tranche set is the target allocation; risk weights sum to 1.0 (no risk over-allocation).",
        "- Execution realism: if TP is reached before full DCA completion, TP is applied only to currently filled size (remaining tranches stay unfilled).",
        "",
        "## Baseline vs DCA-50/50",
        delta_line("total_trades", baseline["total_trades"], dca_50["total_trades"]),
        delta_line("avg_pf", baseline["avg_pf"], dca_50["avg_pf"]),
        delta_line("worst_dd_pct", baseline["worst_dd_pct"], dca_50["worst_dd_pct"], pct=True),
        delta_line("total_net", baseline["total_net"], dca_50["total_net"]),
        delta_line("avg_win_rate", baseline["avg_win_rate"], dca_50["avg_win_rate"], pct=True, scale=100.0),
        "",
        "## Baseline vs DCA-30/30/40",
        delta_line("total_trades", baseline["total_trades"], dca_334["total_trades"]),
        delta_line("avg_pf", baseline["avg_pf"], dca_334["avg_pf"]),
        delta_line("worst_dd_pct", baseline["worst_dd_pct"], dca_334["worst_dd_pct"], pct=True),
        delta_line("total_net", baseline["total_net"], dca_334["total_net"]),
        delta_line("avg_win_rate", baseline["avg_win_rate"], dca_334["avg_win_rate"], pct=True, scale=100.0),
        "",
    ]

    best_pf_variant = max([dca_50, dca_334], key=lambda r: r["avg_pf"])
    best_dd_variant = min([dca_50, dca_334], key=lambda r: r["worst_dd_pct"])
    lines.append("## Conclusion")
    if any(r["avg_pf"] > baseline["avg_pf"] and r["worst_dd_pct"] <= baseline["worst_dd_pct"] for r in [dca_50, dca_334]):
        lines.append("- At least one DCA variant improved PF/DD jointly versus baseline.")
    else:
        lines.append(
            "- No DCA variant improved PF/DD jointly versus baseline: both DCA models reduced PF, while drawdown improved versus baseline."
        )
        lines.append(
            f"- Best PF among DCA variants: {best_pf_variant['model']} (PF {best_pf_variant['avg_pf']:.4f} vs baseline {baseline['avg_pf']:.4f})."
        )
        lines.append(
            f"- Best DD among DCA variants: {best_dd_variant['model']} (DD {best_dd_variant['worst_dd_pct']:.2f}% vs baseline {baseline['worst_dd_pct']:.2f}%)."
        )
    lines.append("- Caveat: close-based trigger approximation can differ from true intrabar limit fills.")

    (OUT_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
