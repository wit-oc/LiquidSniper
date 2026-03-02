from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RegimeDirection = Literal["bullish", "bearish"]
RegimeConfidence = Literal["confirmed", "transitional"]
TransitionReason = Literal["choch_detected", "bos_confirmed"]


@dataclass(frozen=True)
class SwingPoint:
    kind: Literal["high", "low"]
    pivot_index: int
    confirmed_index: int
    price: float


def detect_swings(highs: list[float], lows: list[float], *, left: int = 2, right: int = 2) -> list[SwingPoint]:
    if not highs or not lows or len(highs) != len(lows):
        return []
    n = len(highs)
    swings: list[SwingPoint] = []
    for i in range(left, n - right):
        hi = highs[i]
        lo = lows[i]
        if all(hi >= highs[j] for j in range(i - left, i + right + 1) if j != i):
            swings.append(SwingPoint("high", i, i + right, hi))
        if all(lo <= lows[j] for j in range(i - left, i + right + 1) if j != i):
            swings.append(SwingPoint("low", i, i + right, lo))
    swings.sort(key=lambda s: (s.confirmed_index, 0 if s.kind == "high" else 1, s.pivot_index))
    return swings


def run_phase1_htf_structure(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    *,
    left: int = 2,
    right: int = 2,
    initial_direction: RegimeDirection = "bullish",
    n_init: int = 25,
    break_min_frac_of_candle: float = 0.20,
) -> tuple[list[dict], list[dict], list[dict]]:
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("highs/lows/closes must have equal length")
    if not highs:
        return [], [], []

    n = len(closes)
    init_len = min(max(1, n_init), n)

    def ema_direction(series: list[float], period: int = 12) -> RegimeDirection:
        alpha = 2.0 / (period + 1.0)
        ema = series[0]
        for px in series[1:]:
            ema = alpha * px + (1.0 - alpha) * ema
        return "bullish" if series[-1] >= ema else "bearish"

    seed_direction = ema_direction(closes[:init_len]) if n >= 2 else initial_direction

    init_high = max(highs[:init_len])
    init_high_idx = highs[:init_len].index(init_high)
    init_low = min(lows[:init_len])
    init_low_idx = lows[:init_len].index(init_low)

    direction: RegimeDirection = seed_direction
    confidence: RegimeConfidence = "confirmed"

    # Structural/protected levels
    protected_low = init_low
    protected_low_idx = init_low_idx
    protected_high = init_high
    protected_high_idx = init_high_idx

    # Continuation levels
    validated_high: float | None = init_high if direction == "bullish" else None
    validated_high_idx: int | None = init_high_idx if direction == "bullish" else None
    validated_low: float | None = init_low if direction == "bearish" else None
    validated_low_idx: int | None = init_low_idx if direction == "bearish" else None

    # Candidate extremes + 2-step retracement validation anchors
    cand_high = highs[0]
    cand_high_idx = 0
    cand_high_opp = lows[0]

    cand_low = lows[0]
    cand_low_idx = 0
    cand_low_opp = highs[0]

    active_choch_level: float | None = None
    active_choch_index: int | None = None

    choch_emitted_keys: set[tuple[str, int]] = set()

    bars_log: list[dict] = []
    events_log: list[dict] = []
    swings_log: list[dict] = []

    def accepted_break_above(level: float, i: int) -> bool:
        rng = max(1e-9, highs[i] - lows[i])
        return closes[i] > level and (closes[i] - level) >= break_min_frac_of_candle * rng

    def accepted_break_below(level: float, i: int) -> bool:
        rng = max(1e-9, highs[i] - lows[i])
        return closes[i] < level and (level - closes[i]) >= break_min_frac_of_candle * rng

    def emit(i: int, event: str, price: float, *, anchor_idx: int | None = None, reason: TransitionReason | None = None):
        events_log.append(
            {
                "index": i,
                "event": event,
                "price": price,
                "regime_direction": direction,
                "regime_confidence": confidence,
                "transition_reason": reason,
                "anchor_index": i if anchor_idx is None else anchor_idx,
            }
        )

    for i in range(n):
        h, l, c = highs[i], lows[i], closes[i]
        transition_reason: TransitionReason | None = None

        if direction == "bullish":
            # Candidate high expansion.
            if h > cand_high:
                cand_high = h
                cand_high_idx = i
                cand_high_opp = l
                emit(i, "candidate_swing_high", h)

            # Trend-side SFP can re-anchor bullish continuation high.
            if validated_high is not None and h >= validated_high and c <= validated_high:
                emit(i, "sfp_detected", h)
                validated_high = h
                validated_high_idx = i
                emit(i, "sfp_reanchored", h)

            # Opposite-side sweep: log only.
            if l <= protected_low and c >= protected_low:
                emit(i, "sfp_detected", l)

            # 2-step retracement confirmation for swing high.
            if i > cand_high_idx and l <= cand_high_opp and h <= cand_high:
                if validated_high_idx != cand_high_idx:
                    validated_high = cand_high
                    validated_high_idx = cand_high_idx
                    swings_log.append({"kind": "swing_high", "index": cand_high_idx, "price": cand_high})
                    emit(i, "swing_high_validated_by_sweep", cand_high, anchor_idx=cand_high_idx)

            # Continuation BoS in bullish direction.
            if validated_high is not None and accepted_break_above(validated_high, i):
                start = validated_high_idx if validated_high_idx is not None else i
                window = lows[start : i + 1]
                lock_low = min(window)
                lock_idx = start + window.index(lock_low)
                protected_low = lock_low
                protected_low_idx = lock_idx
                swings_log.append({"kind": "swing_low", "index": lock_idx, "price": lock_low})
                emit(i, "bos_confirmed", c, reason="bos_confirmed")
                emit(i, "swing_low_locked", lock_low, anchor_idx=lock_idx)
                confidence = "confirmed"
                transition_reason = "bos_confirmed"
                active_choch_level = None
                active_choch_index = None
                validated_high = h
                validated_high_idx = i

            # CHoCH against protected low. One-shot per protected level.
            if accepted_break_below(protected_low, i):
                key = ("down", protected_low_idx)
                if key not in choch_emitted_keys:
                    choch_emitted_keys.add(key)
                    direction = "bearish"
                    confidence = "transitional"
                    transition_reason = "choch_detected"
                    active_choch_level = protected_low
                    active_choch_index = i
                    emit(i, "choch_detected", c, reason="choch_detected")

        else:  # bearish direction
            if l < cand_low:
                cand_low = l
                cand_low_idx = i
                cand_low_opp = h
                emit(i, "candidate_swing_low", l)

            # Trend-side SFP can re-anchor bearish continuation low.
            if validated_low is not None and l <= validated_low and c >= validated_low:
                emit(i, "sfp_detected", l)
                validated_low = l
                validated_low_idx = i
                emit(i, "sfp_reanchored", l)

            # Opposite-side sweep: log only.
            if h >= protected_high and c <= protected_high:
                emit(i, "sfp_detected", h)

            # 2-step retracement confirmation for swing low.
            if i > cand_low_idx and h >= cand_low_opp and l >= cand_low:
                if validated_low_idx != cand_low_idx:
                    validated_low = cand_low
                    validated_low_idx = cand_low_idx
                    swings_log.append({"kind": "swing_low", "index": cand_low_idx, "price": cand_low})
                    emit(i, "swing_low_validated_by_sweep", cand_low, anchor_idx=cand_low_idx)

            # Continuation BoS in bearish direction.
            if validated_low is not None and accepted_break_below(validated_low, i):
                start = validated_low_idx if validated_low_idx is not None else i
                window = highs[start : i + 1]
                lock_high = max(window)
                lock_idx = start + window.index(lock_high)
                protected_high = lock_high
                protected_high_idx = lock_idx
                swings_log.append({"kind": "swing_high", "index": lock_idx, "price": lock_high})
                emit(i, "bos_confirmed", c, reason="bos_confirmed")
                emit(i, "swing_high_locked", lock_high, anchor_idx=lock_idx)
                confidence = "confirmed"
                transition_reason = "bos_confirmed"
                active_choch_level = None
                active_choch_index = None
                validated_low = l
                validated_low_idx = i

            # CHoCH against protected high. One-shot per protected level.
            if accepted_break_above(protected_high, i):
                key = ("up", protected_high_idx)
                if key not in choch_emitted_keys:
                    choch_emitted_keys.add(key)
                    direction = "bullish"
                    confidence = "transitional"
                    transition_reason = "choch_detected"
                    active_choch_level = protected_high
                    active_choch_index = i
                    emit(i, "choch_detected", c, reason="choch_detected")

        bars_log.append(
            {
                "index": i,
                "close": c,
                "regime_direction": direction,
                "regime_confidence": confidence,
                "transition_reason": transition_reason,
                "protected_high": protected_high,
                "protected_low": protected_low,
                "active_choch_level": active_choch_level,
                "active_choch_index": active_choch_index,
            }
        )

    return bars_log, events_log, swings_log
