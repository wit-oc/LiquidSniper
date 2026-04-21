from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


@dataclass
class Trade:
    side: str
    entry_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    qty: float
    pnl: float
    r_multiple: float
    reason: str


def ema(values: Sequence[float], length: int) -> List[float]:
    if length <= 0:
        raise ValueError("EMA length must be > 0")
    out: List[float] = []
    alpha = 2.0 / (length + 1)
    prev: Optional[float] = None
    for v in values:
        prev = v if prev is None else (alpha * v + (1 - alpha) * prev)
        out.append(prev)
    return out


def atr(rows: Sequence[dict], length: int = 14) -> List[float]:
    tr: List[float] = []
    prev_close: Optional[float] = None
    for r in rows:
        hi, lo, c = r["high"], r["low"], r["close"]
        if prev_close is None:
            tr.append(hi - lo)
        else:
            tr.append(max(hi - lo, abs(hi - prev_close), abs(lo - prev_close)))
        prev_close = c
    return ema(tr, length)


def adx_proxy(rows: Sequence[dict], length: int = 14) -> List[float]:
    up_dm: List[float] = [0.0]
    down_dm: List[float] = [0.0]
    tr: List[float] = [rows[0]["high"] - rows[0]["low"]]

    for i in range(1, len(rows)):
        up = rows[i]["high"] - rows[i - 1]["high"]
        down = rows[i - 1]["low"] - rows[i]["low"]
        up_dm.append(up if up > down and up > 0 else 0.0)
        down_dm.append(down if down > up and down > 0 else 0.0)
        hi, lo, prev_close = rows[i]["high"], rows[i]["low"], rows[i - 1]["close"]
        tr.append(max(hi - lo, abs(hi - prev_close), abs(lo - prev_close)))

    tr_rma = ema(tr, length)
    plus = [100.0 * ema(up_dm, length)[i] / max(tr_rma[i], 1e-9) for i in range(len(rows))]
    minus = [100.0 * ema(down_dm, length)[i] / max(tr_rma[i], 1e-9) for i in range(len(rows))]
    dx = [100.0 * abs(plus[i] - minus[i]) / max(plus[i] + minus[i], 1e-9) for i in range(len(rows))]
    return ema(dx, length)


def chop_index(rows: Sequence[dict], length: int = 14) -> List[float]:
    out: List[float] = []
    tr = atr(rows, 1)
    for i in range(len(rows)):
        lo = max(0, i - length + 1)
        window = rows[lo : i + 1]
        tr_sum = sum(tr[lo : i + 1])
        span = max(r["high"] for r in window) - min(r["low"] for r in window)
        raw = 100.0 if span <= 1e-9 else 100.0 * math.log10(max(tr_sum / span, 1e-9)) / math.log10(length)
        out.append(max(0.0, min(100.0, raw)))
    return out


def find_swings(rows: Sequence[dict], swing_len: int) -> Dict[str, List[Optional[float]]]:
    highs: List[Optional[float]] = [None] * len(rows)
    lows: List[Optional[float]] = [None] * len(rows)
    for i in range(swing_len, len(rows) - swing_len):
        c_hi = rows[i]["high"]
        c_lo = rows[i]["low"]
        left = rows[i - swing_len : i]
        right = rows[i + 1 : i + 1 + swing_len]
        if all(c_hi > r["high"] for r in left + right):
            highs[i] = c_hi
        if all(c_lo < r["low"] for r in left + right):
            lows[i] = c_lo
    return {"highs": highs, "lows": lows}


def calculate_confluence(features: Dict[str, bool], side: str) -> float:
    return (
        (2.0 if features[f"trend_{side}"] else 0.0)
        + (2.0 if features[f"structure_{side}"] else 0.0)
        + (2.0 if features[f"first_retest_{side}"] else 0.0)
        + (1.0 if features[f"ema_stack_{side}"] else 0.0)
        + (1.0 if features["chop_ok"] else 0.0)
        + (1.0 if features["candle_ok"] else 0.0)
        + (1.0 if features[f"sr_side_ok_{side}"] else 0.0)
    )


def gate_pass(score: float, trigger_score: float, chop_ok: bool, trend_ok: bool, candle_ok: bool = True) -> bool:
    return score >= trigger_score and chop_ok and trend_ok and candle_ok


def compute_risk_based_qty(
    equity: float,
    risk_pct: float,
    entry_price: float,
    stop_price: float,
    profile_cap_pct: float,
    max_notional_pct: float,
) -> float:
    risk_pct_effective = max(0.0, min(risk_pct, profile_cap_pct))
    if risk_pct_effective <= 0:
        return 0.0
    risk_per_unit = abs(entry_price - stop_price)
    if risk_per_unit <= 1e-12:
        return 0.0
    risk_budget = equity * (risk_pct_effective / 100.0)
    qty = risk_budget / risk_per_unit
    max_notional = equity * (max_notional_pct / 100.0)
    max_qty = max_notional / max(entry_price, 1e-9)
    return max(0.0, min(qty, max_qty))


def run_backtest(rows: Sequence[dict], params: Dict[str, float], seed: int = 42) -> Dict[str, float]:
    if len(rows) < 120:
        return {"trades": 0, "win_rate": 0.0, "net_pnl": 0.0, "pf": 0.0, "max_dd": 0.0, "score": 0.0}

    close = [r["close"] for r in rows]
    e20 = ema(close, int(params.get("entry_ema_fast", 20)))
    e50 = ema(close, int(params.get("entry_ema_slow", 50)))
    e_itf20 = ema(close, int(params.get("itf_ema_fast", 50)))
    e_itf50 = ema(close, int(params.get("itf_ema_slow", 100)))
    e_htf20 = ema(close, int(params.get("htf_ema_fast", 100)))
    e_htf50 = ema(close, int(params.get("htf_ema_slow", 200)))

    ci = chop_index(rows, int(params.get("chop_len", 14)))
    adx = adx_proxy(rows, int(params.get("adx_len", 14)))
    swings = find_swings(rows, int(params["structure_swing_len"]))
    atr_vals = atr(rows, 14)

    eq = float(params.get("initial_equity", 10_000.0))
    peak = eq
    drawdown = 0.0
    wins = 0
    losses = 0
    gross_win = 0.0
    gross_loss = 0.0

    profile_cap = float(params.get("profile_risk_cap_pct", 5.0))
    cooldown = int(params.get("cooldown_bars", 3))
    rr = float(params.get("rr_target", 2.0))
    be_r = float(params.get("be_trigger_r", 1.0))

    last_swing_hi = None
    last_swing_lo = None
    structure_dir = 0
    bars_since_long_bos = 10**9
    bars_since_short_bos = 10**9
    long_retest_armed = False
    short_retest_armed = False
    long_retested = False
    short_retested = False

    position = None
    last_trade_idx = -10**9

    for i in range(1, len(rows)):
        r = rows[i]
        bars_since_long_bos += 1
        bars_since_short_bos += 1

        if swings["highs"][i] is not None:
            last_swing_hi = swings["highs"][i]
        if swings["lows"][i] is not None:
            last_swing_lo = swings["lows"][i]

        bos_up = last_swing_hi is not None and r["close"] > last_swing_hi
        bos_down = last_swing_lo is not None and r["close"] < last_swing_lo
        prior_structure = structure_dir
        if bos_up:
            structure_dir = 1
            long_retest_armed, long_retested, bars_since_long_bos = True, False, 0
            short_retest_armed = False
        if bos_down:
            structure_dir = -1
            short_retest_armed, short_retested, bars_since_short_bos = True, False, 0
            long_retest_armed = False

        choch_up = bos_up and prior_structure == -1
        choch_down = bos_down and prior_structure == 1

        window = int(params["retest_window_bars"])
        if bars_since_long_bos > window:
            long_retest_armed = False
        if bars_since_short_bos > window:
            short_retest_armed = False

        sr_anchor = e_itf50[i]
        zone_half = sr_anchor * (float(params["retest_bps"]) / 10_000.0)
        touch_zone = r["high"] >= (sr_anchor - zone_half) and r["low"] <= (sr_anchor + zone_half)

        long_first_retest = bool(touch_zone and long_retest_armed and not long_retested)
        short_first_retest = bool(touch_zone and short_retest_armed and not short_retested)
        if long_first_retest:
            long_retested, long_retest_armed = True, False
        if short_first_retest:
            short_retested, short_retest_armed = True, False

        trend_long = e_itf20[i] > e_itf50[i] and e_htf20[i] > e_htf50[i]
        trend_short = e_itf20[i] < e_itf50[i] and e_htf20[i] < e_htf50[i]
        ema_stack_long = close[i] > e20[i] > e50[i]
        ema_stack_short = close[i] < e20[i] < e50[i]
        chop_ok = ci[i] <= float(params["chop_ci_max"]) and adx[i] >= float(params["chop_adx_min"])

        common = {"chop_ok": chop_ok, "candle_ok": True}
        features = {
            **common,
            "trend_long": trend_long,
            "structure_long": bool(bos_up or choch_up),
            "first_retest_long": long_first_retest,
            "ema_stack_long": ema_stack_long,
            "sr_side_ok_long": close[i] > sr_anchor,
            "trend_short": trend_short,
            "structure_short": bool(bos_down or choch_down),
            "first_retest_short": short_first_retest,
            "ema_stack_short": ema_stack_short,
            "sr_side_ok_short": close[i] < sr_anchor,
        }

        s_long = calculate_confluence(features, "long")
        s_short = calculate_confluence(features, "short")
        trig_long = gate_pass(s_long, float(params["trigger_score"]), chop_ok, trend_long)
        trig_short = gate_pass(s_short, float(params["trigger_score"]), chop_ok, trend_short)

        if position is None and i - last_trade_idx > cooldown:
            side = None
            score = 0.0
            if trig_long:
                side, score = "long", s_long
            elif trig_short:
                side, score = "short", s_short

            if side:
                entry = r["close"]
                a = atr_vals[i]
                if side == "long":
                    stop = min(last_swing_lo or (entry - a * 1.4), entry - a * 0.5)
                    tp = entry + (entry - stop) * rr
                else:
                    stop = max(last_swing_hi or (entry + a * 1.4), entry + a * 0.5)
                    tp = entry - (stop - entry) * rr

                high_conf = score >= float(params["high_conf_score_threshold"])
                risk_pct = float(params["risk_pct_high_conf"] if high_conf else params["risk_pct_low_conf"])
                if params.get("sizing_mode", "risk_based") == "risk_based":
                    qty = compute_risk_based_qty(
                        equity=eq,
                        risk_pct=risk_pct,
                        entry_price=entry,
                        stop_price=stop,
                        profile_cap_pct=profile_cap,
                        max_notional_pct=float(params.get("max_notional_pct", 100.0)),
                    )
                else:
                    pct = max(0.0, min(risk_pct, profile_cap)) / 100.0
                    qty = (eq * pct) / max(entry, 1e-9)

                if qty > 0:
                    position = {
                        "side": side,
                        "entry": entry,
                        "stop": stop,
                        "tp": tp,
                        "qty": qty,
                        "entry_idx": i,
                        "risk": abs(entry - stop),
                        "be_active": False,
                        "be_price": entry * (1 + float(params.get("be_offset_pct", 0.0)) / 100.0)
                        if side == "long"
                        else entry * (1 - float(params.get("be_offset_pct", 0.0)) / 100.0),
                        "be_trigger": entry + abs(entry - stop) * be_r if side == "long" else entry - abs(entry - stop) * be_r,
                    }
                    last_trade_idx = i

        if position is not None:
            side = position["side"]
            hi, lo = r["high"], r["low"]

            if float(params.get("be_enabled", 1)):
                if side == "long" and hi >= position["be_trigger"]:
                    position["be_active"] = True
                if side == "short" and lo <= position["be_trigger"]:
                    position["be_active"] = True

            stop_eff = position["stop"]
            if position["be_active"]:
                if side == "long":
                    stop_eff = max(stop_eff, position["be_price"])
                else:
                    stop_eff = min(stop_eff, position["be_price"])

            exit_reason = None
            exit_price = None
            if side == "long":
                if lo <= stop_eff:
                    exit_reason, exit_price = "stop", stop_eff
                elif hi >= position["tp"]:
                    exit_reason, exit_price = "tp", position["tp"]
            else:
                if hi >= stop_eff:
                    exit_reason, exit_price = "stop", stop_eff
                elif lo <= position["tp"]:
                    exit_reason, exit_price = "tp", position["tp"]

            if exit_reason:
                pnl = (exit_price - position["entry"]) * position["qty"]
                if side == "short":
                    pnl = -pnl
                eq += pnl
                peak = max(peak, eq)
                drawdown = max(drawdown, (peak - eq) / max(peak, 1e-9))

                r_mult = pnl / max(position["risk"] * position["qty"], 1e-9)
                if pnl >= 0:
                    wins += 1
                    gross_win += pnl
                else:
                    losses += 1
                    gross_loss += abs(pnl)
                position = None

    trades = wins + losses
    win_rate = wins / trades if trades else 0.0
    pf = gross_win / gross_loss if gross_loss > 1e-9 else (10.0 if gross_win > 0 else 0.0)
    net_pnl = eq - float(params.get("initial_equity", 10_000.0))

    return {
        "trades": trades,
        "win_rate": win_rate,
        "net_pnl": net_pnl,
        "pf": pf,
        "max_dd": drawdown,
        "score": 0.0,
    }
