from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class Trade:
    side: str
    entry_index: int
    entry_price: float
    stop_price: float
    risk_pct: float = 1.0
    size_mult: float = 1.0
    confluence_score: float = 0.0
    exit_index: int | None = None
    exit_price: float | None = None

    @property
    def closed(self) -> bool:
        return self.exit_index is not None and self.exit_price is not None


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def build_trades(events: list[dict], closes: pd.Series) -> list[Trade]:
    open_longs: deque[Trade] = deque()
    open_shorts: deque[Trade] = deque()
    closed: list[Trade] = []

    for e in events:
        idx = int(e["index"])
        price = float(closes.iloc[idx])
        ev = e["event"]

        if ev == "enter_long":
            entry = float(e.get("entry", price))
            stop = float(e.get("stop", entry * (1 - 0.001)))
            open_longs.append(
                Trade(
                    side="long",
                    entry_index=idx,
                    entry_price=entry,
                    stop_price=stop,
                    risk_pct=float(e.get("risk_pct", 1.0)),
                    size_mult=float(e.get("size_mult", 1.0)),
                    confluence_score=float(e.get("confluence_score", 0.0)),
                )
            )
        elif ev == "enter_short":
            entry = float(e.get("entry", price))
            stop = float(e.get("stop", entry * (1 + 0.001)))
            open_shorts.append(
                Trade(
                    side="short",
                    entry_index=idx,
                    entry_price=entry,
                    stop_price=stop,
                    risk_pct=float(e.get("risk_pct", 1.0)),
                    size_mult=float(e.get("size_mult", 1.0)),
                    confluence_score=float(e.get("confluence_score", 0.0)),
                )
            )
        elif ev in ("exit_stop", "exit_tp2"):
            side = e.get("side")
            if side == "long" and open_longs:
                t = open_longs.popleft()
                t.exit_index = idx
                t.exit_price = price
                closed.append(t)
            elif side == "short" and open_shorts:
                t = open_shorts.popleft()
                t.exit_index = idx
                t.exit_price = price
                closed.append(t)

    return closed


def _trade_cost(
    tr: Trade,
    units: float,
    fee_bps_per_side: float,
    slippage_bps_per_side: float,
    funding_bps_per_8h: float,
) -> float:
    notional_ref = tr.entry_price * units
    roundtrip_bps = 2.0 * (fee_bps_per_side + slippage_bps_per_side)
    fee_slip = notional_ref * (roundtrip_bps / 10_000.0)

    hold_hours = max((tr.exit_index - tr.entry_index) if tr.closed else 0, 0)
    funding = notional_ref * ((funding_bps_per_8h / 10_000.0) * (hold_hours / 8.0))
    return fee_slip + funding


def summarize(
    trades: list[Trade],
    fee_bps_per_side: float = 5.0,
    slippage_bps_per_side: float = 2.0,
    funding_bps_per_8h: float = 1.0,
    initial_equity: float = 10_000.0,
) -> dict:
    if not trades:
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
            "final_equity": initial_equity,
        }

    equity = initial_equity
    peak = initial_equity
    max_dd = 0.0
    max_dd_pct = 0.0

    pnls: list[float] = []
    for tr in trades:
        if not tr.closed:
            continue
        risk_per_unit = abs(tr.entry_price - tr.stop_price)
        if risk_per_unit <= 0:
            continue

        risk_amount = equity * (max(tr.risk_pct, 0.0) / 100.0)
        units = risk_amount / risk_per_unit
        if units <= 0:
            continue

        if tr.side == "long":
            gross = (float(tr.exit_price) - tr.entry_price) * units
        else:
            gross = (tr.entry_price - float(tr.exit_price)) * units

        costs = _trade_cost(tr, units, fee_bps_per_side, slippage_bps_per_side, funding_bps_per_8h)
        net = gross - costs
        pnls.append(net)
        equity += net

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
            "final_equity": initial_equity,
        }

    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    net = sum(pnls)
    wins = sum(1 for p in pnls if p > 0)
    losses = sum(1 for p in pnls if p < 0)
    win_rate = wins / max(len(pnls), 1)
    pf = (gross_profit / gross_loss) if gross_loss > 0 else 0.0

    return {
        "trades": len(pnls),
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "pf": pf,
        "net": net,
        "max_dd": max_dd,
        "max_dd_pct": max_dd_pct,
        "final_equity": equity,
    }


def run(symbol: str, price_csv: Path, events_jsonl: Path, fee_bps: float, slip_bps: float, funding_bps_8h: float) -> dict:
    df = pd.read_csv(price_csv)
    events = load_jsonl(events_jsonl)
    trades = build_trades(events, df["close"])
    out = summarize(trades, fee_bps_per_side=fee_bps, slippage_bps_per_side=slip_bps, funding_bps_per_8h=funding_bps_8h)
    out["symbol"] = symbol
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--btc-csv", type=Path, required=True)
    ap.add_argument("--eth-csv", type=Path, required=True)
    ap.add_argument("--btc-events", type=Path, required=True)
    ap.add_argument("--eth-events", type=Path, required=True)
    ap.add_argument("--fee-bps", type=float, default=5.0)
    ap.add_argument("--slippage-bps", type=float, default=2.0)
    ap.add_argument("--funding-bps-8h", type=float, default=1.0)
    args = ap.parse_args()

    btc = run("BTC", args.btc_csv, args.btc_events, args.fee_bps, args.slippage_bps, args.funding_bps_8h)
    eth = run("ETH", args.eth_csv, args.eth_events, args.fee_bps, args.slippage_bps, args.funding_bps_8h)
    print(json.dumps({"assumptions": {"fee_bps": args.fee_bps, "slippage_bps": args.slippage_bps, "funding_bps_8h": args.funding_bps_8h}, "btc": btc, "eth": eth}, indent=2))
