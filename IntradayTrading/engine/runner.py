from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from .risk import BreakerState
from .signals import SignalContext, should_enter_long, should_enter_short
from .structure import RegimeState, StructureBias
from .zones import Zone
from .zones_runtime import ZoneInteraction, find_interaction
from .fib_context import FibConfig, FibTimeframe, aggregate_fib_context, compute_timeframe_state
from .dynamic_levels import build_dynamic_level_packet, flatten_dynamic_level_packet
from .fib_anchors import (
    build_phase1_contract_context_for_timeframe,
    compute_fib_level_tap_history_for_timeframe,
    select_phase1_contract_anchor_for_timeframe,
    select_latest_impulse_anchor_for_timeframe,
    tag_anchor_as_debug_fallback,
)


@dataclass
class Bar:
    index: int
    open: float
    high: float
    low: float
    close: float
    timestamp: int | None = None
    volume: float | None = None


@dataclass
class Position:
    side: str  # long|short
    entry: float
    stop: float
    tp1: float
    tp2: float
    open_index: int
    risk_pct: float = 1.0
    size_mult: float = 1.0
    confluence_score: float = 0.0
    tp1_hit: bool = False
    is_at_risk: bool = True


@dataclass
class RunnerConfig:
    max_at_risk_positions: int = 2
    require_retest_sequence: bool = True
    rr_tp1: float = 1.0
    rr_tp2: float = 2.5
    stop_buffer_frac: float = 0.001
    be_buffer_frac: float = 0.0002
    max_open_positions: int = 4
    max_zone_width_frac: float = 0.01
    reclaim_buffer_frac: float = 0.0005

    # New selective gates
    allow_neutral_bias: bool = False
    retest_max_bars: int = 6
    min_body_frac: float = 0.0008
    min_rejection_wick_frac: float = 0.0008
    atr_period: int = 14
    atr_floor_frac: float = 0.0015
    trend_lookback: int = 20
    trend_slope_min: float = 0.0005
    stop_cluster_window_bars: int = 24
    stop_cluster_count: int = 3
    cooldown_bars: int = 12

    # Foxian contextual confluence gates
    enable_swing_location_gate: bool = True
    swing_lookback_bars: int = 96
    long_location_max: float = 0.4
    short_location_min: float = 0.6
    enable_momentum_gate: bool = True
    momentum_lookback: int = 8
    momentum_min_frac: float = 0.003
    enable_chop_gate: bool = True
    chop_slope_abs_max: float = 0.001

    # LiquidSniper-inspired intraday additions
    strict_retest_bps_max: float = 18.0
    near_retest_bps_max: float = 30.0
    near_retest_penalty_max: float = 0.7
    enable_confluence_gate: bool = True
    score_gate_min: float = 6.0
    trigger_score_min: float = 7.2
    risk_pct_low_conf: float = 1.0
    risk_pct_high_conf: float = 2.0
    high_conf_score_threshold: float = 8.0

    # Sprint: candle/fib/retest-ordinal controls
    enable_candle_confirmation: bool = True
    candle_score_min: float = 1.6
    enable_fib_directional_gate: bool = True
    fib_long_min: float = 0.618
    fib_long_max: float = 0.786
    fib_short_min: float = 0.618
    fib_short_max: float = 0.786
    fib_use_phase1_contract_anchors: bool = True
    fib_allow_debug_anchor_fallback: bool = True
    retest_ordinal_decay: float = 0.35
    retest_ordinal_max_bonus: float = 0.8


class EntryFSMState(str, Enum):
    IDLE = "idle"
    WATCH = "watch"
    TRIGGER = "trigger"
    INVALID = "invalid"
    EXPIRED = "expired"


@dataclass
class EntryWatch:
    side: str
    zone_id: str | None
    start_index: int
    expires_at: int


class RetestTracker:
    def __init__(self):
        self.last_touch_index: dict[str, int] = {}
        self.touch_counts: dict[str, int] = {}

    def update(self, bar_index: int, zone_id: str, touched: bool, reclaimed: bool, max_bars: int) -> bool:
        if touched:
            self.last_touch_index[zone_id] = bar_index
            self.touch_counts[zone_id] = self.touch_counts.get(zone_id, 0) + 1
        touch_idx = self.last_touch_index.get(zone_id)
        if touch_idx is None:
            return False
        return reclaimed and (bar_index - touch_idx <= max_bars)

    def retest_ordinal(self, zone_id: str | None) -> int:
        if zone_id is None:
            return 0
        return self.touch_counts.get(zone_id, 0)


class SignalRunner:
    def __init__(self, cfg: RunnerConfig | None = None):
        self.cfg = cfg or RunnerConfig()

    def run(self, bars: List[Bar], structure_bias_by_index: Dict[int, StructureBias], zones: List[Zone]) -> List[dict]:
        events, _ = self.run_with_logs(bars, structure_bias_by_index, zones)
        return events

    def _count_at_risk(self, positions: List[Position]) -> int:
        return sum(1 for p in positions if p.is_at_risk)

    def _quality_gate(self, b: Bar, interaction: ZoneInteraction | None, side: str) -> bool:
        if interaction is None:
            return False
        body = abs(b.close - b.open) / max(abs(b.close), 1e-9)
        upper_wick = (b.high - max(b.open, b.close)) / max(abs(b.close), 1e-9)
        lower_wick = (min(b.open, b.close) - b.low) / max(abs(b.close), 1e-9)

        if body < self.cfg.min_body_frac:
            return False

        if side == "long":
            return interaction.kind.value == "support" and lower_wick >= self.cfg.min_rejection_wick_frac and b.close >= b.open
        return interaction.kind.value == "resistance" and upper_wick >= self.cfg.min_rejection_wick_frac and b.close <= b.open

    def _candle_score(self, prev: Bar | None, cur: Bar, side: str) -> float:
        """Soft candle confirmation score.

        Allows near-engulf and strong rejection anatomy to qualify with reduced weight.
        """
        if prev is None:
            return 0.0

        prev_body = abs(prev.close - prev.open)
        cur_body = abs(cur.close - cur.open)
        rng = max(cur.high - cur.low, 1e-9)
        body_frac = cur_body / rng
        upper_wick = cur.high - max(cur.open, cur.close)
        lower_wick = min(cur.open, cur.close) - cur.low

        bullish_engulf = (
            prev.close < prev.open
            and cur.close > cur.open
            and cur.open <= prev.close
            and cur.close >= prev.open
            and cur_body >= prev_body * 0.9
        )
        bearish_engulf = (
            prev.close > prev.open
            and cur.close < cur.open
            and cur.open >= prev.close
            and cur.close <= prev.open
            and cur_body >= prev_body * 0.9
        )

        # near-engulf tolerance ("just shy" allowance)
        near_bullish_engulf = (
            prev.close < prev.open
            and cur.close > cur.open
            and cur.open <= prev.close * 1.001
            and cur.close >= prev.open * 0.998
        )
        near_bearish_engulf = (
            prev.close > prev.open
            and cur.close < cur.open
            and cur.open >= prev.close * 0.999
            and cur.close <= prev.open * 1.002
        )

        hammer = lower_wick >= (cur_body * 1.8) and upper_wick <= (cur_body * 0.8) and cur.close >= cur.open
        shooting_star = upper_wick >= (cur_body * 1.8) and lower_wick <= (cur_body * 0.8) and cur.close <= cur.open

        score = 0.0
        if side == "long":
            score += 1.5 if bullish_engulf else (0.9 if near_bullish_engulf else 0.0)
            score += 1.0 if hammer else 0.0
            score += 0.5 if body_frac >= 0.6 and cur.close >= cur.open else 0.0
        else:
            score += 1.5 if bearish_engulf else (0.9 if near_bearish_engulf else 0.0)
            score += 1.0 if shooting_star else 0.0
            score += 0.5 if body_frac >= 0.6 and cur.close <= cur.open else 0.0

        return score

    def _update_positions(self, b: Bar, positions: List[Position], events: List[dict], stop_exit_bars: deque[int]) -> None:
        survivors: List[Position] = []
        for p in positions:
            if p.side == "long" and b.low <= p.stop:
                events.append({"index": b.index, "event": "exit_stop", "side": p.side})
                stop_exit_bars.append(b.index)
                continue
            if p.side == "short" and b.high >= p.stop:
                events.append({"index": b.index, "event": "exit_stop", "side": p.side})
                stop_exit_bars.append(b.index)
                continue

            if not p.tp1_hit:
                if p.side == "long" and b.high >= p.tp1:
                    p.tp1_hit = True
                    p.is_at_risk = False
                    p.stop = p.entry * (1 + self.cfg.be_buffer_frac)
                    events.append({"index": b.index, "event": "tp1_hit", "side": p.side})
                elif p.side == "short" and b.low <= p.tp1:
                    p.tp1_hit = True
                    p.is_at_risk = False
                    p.stop = p.entry * (1 - self.cfg.be_buffer_frac)
                    events.append({"index": b.index, "event": "tp1_hit", "side": p.side})

            if p.side == "long" and b.high >= p.tp2:
                events.append({"index": b.index, "event": "exit_tp2", "side": p.side})
                continue
            if p.side == "short" and b.low <= p.tp2:
                events.append({"index": b.index, "event": "exit_tp2", "side": p.side})
                continue

            survivors.append(p)

        positions[:] = survivors

    def _build_position(self, b: Bar, side: str, risk_pct: float, size_mult: float, confluence_score: float) -> Position:
        if side == "long":
            stop = b.close * (1 - self.cfg.stop_buffer_frac)
            risk = max(b.close - stop, 1e-9)
            tp1 = b.close + (risk * self.cfg.rr_tp1)
            tp2 = b.close + (risk * self.cfg.rr_tp2)
        else:
            stop = b.close * (1 + self.cfg.stop_buffer_frac)
            risk = max(stop - b.close, 1e-9)
            tp1 = b.close - (risk * self.cfg.rr_tp1)
            tp2 = b.close - (risk * self.cfg.rr_tp2)

        return Position(
            side=side,
            entry=b.close,
            stop=stop,
            tp1=tp1,
            tp2=tp2,
            open_index=b.index,
            risk_pct=risk_pct,
            size_mult=size_mult,
            confluence_score=confluence_score,
        )

    def _confluence_score(
        self,
        side: str,
        strict_retest: bool,
        near_retest: bool,
        trend_ok: bool,
        quality_ok: bool,
        momentum_ok: bool,
        location_ok: bool,
        chop_ok: bool,
        near_distance_bps: float,
        retest_ordinal: int,
    ) -> float:
        # Desaturated scoring: no constant baseline; score must be earned.
        score = 0.0
        score += 1.6 if trend_ok else 0.0
        score += 2.0 if strict_retest else (0.9 if near_retest else 0.0)
        score += 1.4 if quality_ok else 0.0
        score += 1.1 if momentum_ok else 0.0
        score += 0.8 if location_ok else 0.0
        score += 0.7 if chop_ok else 0.0

        penalty = 0.0
        ordinal_bonus = 0.0
        if retest_ordinal > 0 and (strict_retest or near_retest):
            ordinal_bonus = self.cfg.retest_ordinal_max_bonus * max(1.0 - ((retest_ordinal - 1) * self.cfg.retest_ordinal_decay), 0.0)

        if near_retest and self.cfg.near_retest_bps_max > self.cfg.strict_retest_bps_max:
            denom = max(self.cfg.near_retest_bps_max - self.cfg.strict_retest_bps_max, 1e-9)
            scaled = max(min((near_distance_bps - self.cfg.strict_retest_bps_max) / denom, 1.0), 0.0)
            penalty = scaled * self.cfg.near_retest_penalty_max

        return max(score + ordinal_bonus - penalty, 0.0)

    def run_with_logs(
        self,
        bars: List[Bar],
        structure_bias_by_index: Dict[int, StructureBias],
        zones: List[Zone],
        symbol: str = "BTC",
        tf: str = "1h",
    ) -> tuple[List[dict], List[dict]]:
        events: List[dict] = []
        logs: List[dict] = []
        positions: List[Position] = []
        breaker = BreakerState(daily_locked=False, weekly_locked=False)
        tracker = RetestTracker()
        stop_exit_bars: deque[int] = deque()

        tr_hist: deque[float] = deque(maxlen=self.cfg.atr_period)
        close_hist: deque[float] = deque(maxlen=max(self.cfg.trend_lookback + 1, self.cfg.momentum_lookback + 1))
        swing_hist: deque[float] = deque(maxlen=self.cfg.swing_lookback_bars)
        prev_close: float | None = None
        initial_regime = RegimeState.BULLISH
        for i in sorted(structure_bias_by_index.keys()):
            b0 = structure_bias_by_index.get(i, StructureBias.NEUTRAL)
            if b0 == StructureBias.BULLISH:
                initial_regime = RegimeState.BULLISH
                break
            if b0 == StructureBias.BEARISH:
                initial_regime = RegimeState.BEARISH
                break
        regime = initial_regime
        choch_candidate: RegimeState | None = None
        prev_bar: Bar | None = None
        watch_long: EntryWatch | None = None
        watch_short: EntryWatch | None = None
        fib_cfg = FibConfig()
        fib_phase1_ctx_1d = (
            build_phase1_contract_context_for_timeframe(bars, base_tf=tf, target_tf="1d")
            if self.cfg.fib_use_phase1_contract_anchors
            else None
        )
        fib_phase1_ctx_4h = (
            build_phase1_contract_context_for_timeframe(bars, base_tf=tf, target_tf="4h")
            if self.cfg.fib_use_phase1_contract_anchors
            else None
        )
        fib_phase1_ctx_1w = (
            build_phase1_contract_context_for_timeframe(bars, base_tf=tf, target_tf="1w")
            if self.cfg.fib_use_phase1_contract_anchors
            else None
        )
        zone_by_id = {zone.id: zone for zone in zones}
        dynamic_timestamps = [int(bar.timestamp) for bar in bars] if bars and all(getattr(bar, "timestamp", None) is not None for bar in bars) else None
        dynamic_volumes = [float(bar.volume) for bar in bars] if bars and all(getattr(bar, "volume", None) is not None for bar in bars) else None

        for bar_pos, b in enumerate(bars):
            self._update_positions(b, positions, events, stop_exit_bars)
            at_risk_count = self._count_at_risk(positions)

            # ATR/Trend updates
            if prev_close is None:
                tr = b.high - b.low
            else:
                tr = max(b.high - b.low, abs(b.high - prev_close), abs(b.low - prev_close))
            tr_hist.append(tr)
            close_hist.append(b.close)
            swing_hist.append(b.close)
            prev_close = b.close

            atr = (sum(tr_hist) / len(tr_hist)) if tr_hist else 0.0
            atr_frac = atr / max(abs(b.close), 1e-9)
            trend_slope = 0.0
            if len(close_hist) >= 2:
                trend_slope = (close_hist[-1] - close_hist[0]) / max(abs(close_hist[0]), 1e-9)

            momentum = 0.0
            if len(close_hist) >= self.cfg.momentum_lookback + 1:
                ref = close_hist[-(self.cfg.momentum_lookback + 1)]
                momentum = (b.close - ref) / max(abs(ref), 1e-9)

            swing_loc = 0.5
            if len(swing_hist) >= 2:
                lo = min(swing_hist)
                hi = max(swing_hist)
                rng = max(hi - lo, 1e-9)
                swing_loc = (b.close - lo) / rng

            # cooldown on stop clusters
            while stop_exit_bars and (b.index - stop_exit_bars[0] > self.cfg.stop_cluster_window_bars):
                stop_exit_bars.popleft()
            cooldown_active = len(stop_exit_bars) >= self.cfg.stop_cluster_count and (
                b.index - stop_exit_bars[-1] <= self.cfg.cooldown_bars
            )

            bias = structure_bias_by_index.get(b.index, StructureBias.NEUTRAL)
            regime_transition = None
            target_regime: RegimeState | None = None
            if bias == StructureBias.BULLISH:
                target_regime = RegimeState.BULLISH
            elif bias == StructureBias.BEARISH:
                target_regime = RegimeState.BEARISH

            if target_regime is None:
                pass
            elif target_regime == regime:
                choch_candidate = None
            elif choch_candidate != target_regime:
                choch_candidate = target_regime
                regime_transition = "choch_candidate"
            else:
                old = regime
                regime = target_regime
                choch_candidate = None
                regime_transition = f"bos_confirmed_flip:{old.value}->{regime.value}"

            interaction = find_interaction(
                zones,
                close_price=b.close,
                high_price=b.high,
                low_price=b.low,
                max_zone_width_frac=self.cfg.max_zone_width_frac,
                reclaim_buffer_frac=self.cfg.reclaim_buffer_frac,
                near_retest_bps_max=self.cfg.near_retest_bps_max,
            )

            zone_touched = interaction is not None and interaction.touched

            strict_retest = False
            near_retest = False
            if interaction is not None:
                if interaction.kind.value == "support":
                    close_edge_bps = abs((b.close - interaction.high) / max(abs(b.close), 1e-9)) * 10_000.0
                else:
                    close_edge_bps = abs((b.close - interaction.low) / max(abs(b.close), 1e-9)) * 10_000.0

                strict_retest = (
                    interaction.touched
                    and interaction.reclaimed
                    and close_edge_bps <= self.cfg.strict_retest_bps_max
                )
                near_retest = (
                    (not interaction.touched)
                    and interaction.reclaimed
                    and interaction.distance_bps <= self.cfg.near_retest_bps_max
                )

            reclaim_confirmed = False
            if interaction is not None and interaction.touched:
                reclaim_confirmed = tracker.update(
                    bar_index=b.index,
                    zone_id=interaction.zone_id,
                    touched=interaction.touched,
                    reclaimed=interaction.reclaimed,
                    max_bars=self.cfg.retest_max_bars,
                )

            if self.cfg.require_retest_sequence:
                if interaction is not None and interaction.touched:
                    reclaim_gate = reclaim_confirmed
                else:
                    reclaim_gate = interaction.reclaimed if interaction is not None else False
            else:
                reclaim_gate = True

            retest_gate = (strict_retest or near_retest) and reclaim_gate
            regime_gate = atr_frac >= self.cfg.atr_floor_frac
            long_trend_ok = trend_slope >= self.cfg.trend_slope_min
            short_trend_ok = trend_slope <= -self.cfg.trend_slope_min

            chop_ok = (abs(trend_slope) >= self.cfg.chop_slope_abs_max) if self.cfg.enable_chop_gate else True
            long_momo_ok = (momentum >= self.cfg.momentum_min_frac) if self.cfg.enable_momentum_gate else True
            short_momo_ok = (momentum <= -self.cfg.momentum_min_frac) if self.cfg.enable_momentum_gate else True
            long_loc_ok = (swing_loc <= self.cfg.long_location_max) if self.cfg.enable_swing_location_gate else True
            short_loc_ok = (swing_loc >= self.cfg.short_location_min) if self.cfg.enable_swing_location_gate else True

            fib_pos = swing_loc

            fib_as_of_ts = f"idx:{b.index}"
            default_fib_bias_side = "long" if regime == RegimeState.BULLISH else "short"

            def resolve_anchor(target_tf: str, phase1_ctx):
                phase1_conf = "unknown"
                if self.cfg.fib_use_phase1_contract_anchors:
                    phase1_anchor, phase1_bias_side, phase1_conf = select_phase1_contract_anchor_for_timeframe(
                        phase1_ctx,
                        as_of_bar_count=bar_pos + 1,
                        fallback_bias_side=default_fib_bias_side,
                    )
                    if phase1_anchor.available:
                        return phase1_anchor, phase1_bias_side, phase1_conf

                    if self.cfg.fib_allow_debug_anchor_fallback:
                        fallback = select_latest_impulse_anchor_for_timeframe(
                            bars[: bar_pos + 1],
                            phase1_bias_side,
                            base_tf=tf,
                            target_tf=target_tf,
                        )
                        if fallback.available:
                            return tag_anchor_as_debug_fallback(fallback, target_tf=target_tf), phase1_bias_side, phase1_conf
                    return phase1_anchor, phase1_bias_side, phase1_conf

                fallback = select_latest_impulse_anchor_for_timeframe(
                    bars[: bar_pos + 1],
                    default_fib_bias_side,
                    base_tf=tf,
                    target_tf=target_tf,
                )
                return fallback, default_fib_bias_side, phase1_conf

            fib_anchor_1d, fib_bias_side_1d, fib_phase1_conf_1d = resolve_anchor("1d", fib_phase1_ctx_1d)
            fib_anchor_4h, fib_bias_side_4h, fib_phase1_conf_4h = resolve_anchor("4h", fib_phase1_ctx_4h)
            fib_anchor_1w, fib_bias_side_1w, fib_phase1_conf_1w = resolve_anchor("1w", fib_phase1_ctx_1w)

            structure_superseded = bool(regime_transition and regime_transition.startswith("bos_confirmed_flip"))

            fib_1d = compute_timeframe_state(
                timeframe=FibTimeframe.D1,
                as_of_index=b.index,
                as_of_ts=fib_as_of_ts,
                bias_side=fib_bias_side_1d,
                anchor_start_id=fib_anchor_1d.start_id,
                anchor_end_id=fib_anchor_1d.end_id,
                anchor_start_price=fib_anchor_1d.start_price,
                anchor_end_price=fib_anchor_1d.end_price,
                opposite_end_swept=fib_anchor_1d.opposite_end_swept,
                structure_superseded=structure_superseded,
                bar_high=b.high,
                bar_low=b.low,
                bar_close=b.close,
                cfg=fib_cfg,
            )
            fib_4h = compute_timeframe_state(
                timeframe=FibTimeframe.H4,
                as_of_index=b.index,
                as_of_ts=fib_as_of_ts,
                bias_side=fib_bias_side_4h,
                anchor_start_id=fib_anchor_4h.start_id,
                anchor_end_id=fib_anchor_4h.end_id,
                anchor_start_price=fib_anchor_4h.start_price,
                anchor_end_price=fib_anchor_4h.end_price,
                opposite_end_swept=fib_anchor_4h.opposite_end_swept,
                structure_superseded=structure_superseded,
                bar_high=b.high,
                bar_low=b.low,
                bar_close=b.close,
                cfg=fib_cfg,
            )
            fib_1w = compute_timeframe_state(
                timeframe=FibTimeframe.W1,
                as_of_index=b.index,
                as_of_ts=fib_as_of_ts,
                bias_side=fib_bias_side_1w,
                anchor_start_id=fib_anchor_1w.start_id,
                anchor_end_id=fib_anchor_1w.end_id,
                anchor_start_price=fib_anchor_1w.start_price,
                anchor_end_price=fib_anchor_1w.end_price,
                opposite_end_swept=fib_anchor_1w.opposite_end_swept,
                structure_superseded=structure_superseded,
                bar_high=b.high,
                bar_low=b.low,
                bar_close=b.close,
                cfg=fib_cfg,
            )
            fib_ctx = aggregate_fib_context(
                as_of_index=b.index,
                as_of_ts=fib_as_of_ts,
                timeframe_states=[fib_1d, fib_4h, fib_1w],
                cfg=fib_cfg,
            )
            dynamic_levels_log = None
            if dynamic_timestamps is not None and dynamic_volumes is not None:
                selected_zone = zone_by_id.get(interaction.zone_id) if interaction is not None else None
                dynamic_packet = build_dynamic_level_packet(
                    bars,
                    as_of_bar_index=bar_pos,
                    symbol=symbol,
                    base_tf=tf,
                    intended_direction=bias.value,
                    selected_zone=selected_zone,
                    timestamps=dynamic_timestamps,
                    volumes=dynamic_volumes,
                    feed_provider="OKX",
                    feed_provenance_note="runner_log_adapter.raw_dynamic_export",
                    source_contract_version="phase2a3.dynamic_levels.v2.raw_only",
                    fib_context_id=f"fib:{fib_ctx.as_of_ts}",
                )
                dynamic_levels_log = dict(flatten_dynamic_level_packet(dynamic_packet))

            fib_taps_1d = compute_fib_level_tap_history_for_timeframe(
                bars[: bar_pos + 1],
                base_tf=tf,
                target_tf="1d",
                anchor=fib_anchor_1d,
                level_0_618=fib_1d.level_0_618,
                level_0_705=fib_1d.level_0_705,
                level_0_786=fib_1d.level_0_786,
            )
            fib_taps_4h = compute_fib_level_tap_history_for_timeframe(
                bars[: bar_pos + 1],
                base_tf=tf,
                target_tf="4h",
                anchor=fib_anchor_4h,
                level_0_618=fib_4h.level_0_618,
                level_0_705=fib_4h.level_0_705,
                level_0_786=fib_4h.level_0_786,
            )
            fib_taps_1w = compute_fib_level_tap_history_for_timeframe(
                bars[: bar_pos + 1],
                base_tf=tf,
                target_tf="1w",
                anchor=fib_anchor_1w,
                level_0_618=fib_1w.level_0_618,
                level_0_705=fib_1w.level_0_705,
                level_0_786=fib_1w.level_0_786,
            )

            long_fib_ok = (self.cfg.fib_long_min <= fib_pos <= self.cfg.fib_long_max) if self.cfg.enable_fib_directional_gate else True
            short_fib_ok = (self.cfg.fib_short_min <= fib_pos <= self.cfg.fib_short_max) if self.cfg.enable_fib_directional_gate else True

            long_candle_score = self._candle_score(prev_bar, b, "long") if self.cfg.enable_candle_confirmation else self.cfg.candle_score_min
            short_candle_score = self._candle_score(prev_bar, b, "short") if self.cfg.enable_candle_confirmation else self.cfg.candle_score_min
            long_candle_ok = long_candle_score >= self.cfg.candle_score_min
            short_candle_ok = short_candle_score >= self.cfg.candle_score_min

            long_bias_ok = regime == RegimeState.BULLISH
            short_bias_ok = regime == RegimeState.BEARISH

            long_quality_ok = self._quality_gate(b, interaction, "long")
            short_quality_ok = self._quality_gate(b, interaction, "short")

            retest_ordinal = tracker.retest_ordinal(interaction.zone_id if interaction else None)

            long_score = self._confluence_score(
                side="long",
                strict_retest=strict_retest,
                near_retest=near_retest,
                trend_ok=long_trend_ok,
                quality_ok=long_quality_ok,
                momentum_ok=long_momo_ok,
                location_ok=long_loc_ok,
                chop_ok=chop_ok,
                near_distance_bps=(interaction.distance_bps if interaction else 0.0),
                retest_ordinal=retest_ordinal,
            )
            short_score = self._confluence_score(
                side="short",
                strict_retest=strict_retest,
                near_retest=near_retest,
                trend_ok=short_trend_ok,
                quality_ok=short_quality_ok,
                momentum_ok=short_momo_ok,
                location_ok=short_loc_ok,
                chop_ok=chop_ok,
                near_distance_bps=(interaction.distance_bps if interaction else 0.0),
                retest_ordinal=retest_ordinal,
            )

            long_score_ok = (not self.cfg.enable_confluence_gate) or (long_score >= self.cfg.score_gate_min)
            short_score_ok = (not self.cfg.enable_confluence_gate) or (short_score >= self.cfg.score_gate_min)

            long_watch_ok = regime_gate and retest_gate and long_trend_ok and long_momo_ok and long_loc_ok and chop_ok and long_score_ok and (not cooldown_active)
            short_watch_ok = regime_gate and retest_gate and short_trend_ok and short_momo_ok and short_loc_ok and chop_ok and short_score_ok and (not cooldown_active)
            long_trigger_ok = long_watch_ok and long_quality_ok and long_fib_ok and long_candle_ok
            short_trigger_ok = short_watch_ok and short_quality_ok and short_fib_ok and short_candle_ok

            action = "none"
            reason = "no_signal"
            chosen_score = 0.0
            chosen_size_mult = 1.0
            fsm_transition = "none"
            fsm_reason = "none"

            if watch_long and (b.index > watch_long.expires_at):
                fsm_transition = "watch->expired"
                fsm_reason = "timeout"
                events.append({"index": b.index, "event": "watch_expired", "side": "long", "zone_id": watch_long.zone_id})
                watch_long = None
            if watch_short and (b.index > watch_short.expires_at):
                fsm_transition = "watch->expired"
                fsm_reason = "timeout"
                events.append({"index": b.index, "event": "watch_expired", "side": "short", "zone_id": watch_short.zone_id})
                watch_short = None

            if watch_long and not long_bias_ok:
                fsm_transition = "watch->invalid"
                fsm_reason = "structure_invalidation"
                events.append({"index": b.index, "event": "watch_invalid", "side": "long", "zone_id": watch_long.zone_id})
                watch_long = None
            if watch_short and not short_bias_ok:
                fsm_transition = "watch->invalid"
                fsm_reason = "structure_invalidation"
                events.append({"index": b.index, "event": "watch_invalid", "side": "short", "zone_id": watch_short.zone_id})
                watch_short = None

            long_poi_ok = long_bias_ok and interaction is not None and long_watch_ok
            short_poi_ok = short_bias_ok and interaction is not None and short_watch_ok
            if watch_long is None and long_poi_ok:
                watch_long = EntryWatch(side="long", zone_id=interaction.zone_id if interaction else None, start_index=b.index, expires_at=b.index + self.cfg.retest_max_bars)
                fsm_transition = "idle->watch"
                fsm_reason = "regime_poi_valid"
                events.append({"index": b.index, "event": "watch_start", "side": "long", "zone_id": watch_long.zone_id})
            if watch_short is None and short_poi_ok:
                watch_short = EntryWatch(side="short", zone_id=interaction.zone_id if interaction else None, start_index=b.index, expires_at=b.index + self.cfg.retest_max_bars)
                fsm_transition = "idle->watch"
                fsm_reason = "regime_poi_valid"
                events.append({"index": b.index, "event": "watch_start", "side": "short", "zone_id": watch_short.zone_id})

            if len(positions) < self.cfg.max_open_positions and watch_long is not None and long_trigger_ok and long_score >= self.cfg.trigger_score_min:
                ctx_long = SignalContext(
                    structure_bias=StructureBias.BULLISH,
                    zone_touched=zone_touched,
                    reclaim_confirmed=retest_gate,
                    filters_passed=True,
                    breaker=breaker,
                    at_risk_count=at_risk_count,
                    max_at_risk=self.cfg.max_at_risk_positions,
                )
                if should_enter_long(ctx_long):
                    risk_pct = self.cfg.risk_pct_high_conf if long_score >= self.cfg.high_conf_score_threshold else self.cfg.risk_pct_low_conf
                    size_mult = max(risk_pct / max(self.cfg.risk_pct_low_conf, 1e-9), 0.0)
                    p = self._build_position(b, "long", risk_pct=risk_pct, size_mult=size_mult, confluence_score=long_score)
                    positions.append(p)
                    events.append(
                        {
                            "index": b.index,
                            "event": "enter_long",
                            "zone_id": interaction.zone_id if interaction else None,
                            "entry": p.entry,
                            "stop": p.stop,
                            "risk_pct": p.risk_pct,
                            "size_mult": p.size_mult,
                            "confluence_score": p.confluence_score,
                            "retest_mode": "strict" if strict_retest else "near" if near_retest else "none",
                        }
                    )
                    action = "enter_long"
                    reason = "watch_triggered_long"
                    chosen_score = long_score
                    chosen_size_mult = size_mult
                    fsm_transition = "watch->trigger"
                    fsm_reason = "fib_candle_quality_pass"
                    watch_long = None
                else:
                    fsm_transition = "watch->invalid"
                    fsm_reason = "acceptance_failure"
                    events.append({"index": b.index, "event": "watch_invalid", "side": "long", "zone_id": watch_long.zone_id})
                    watch_long = None

            if action == "none" and len(positions) < self.cfg.max_open_positions and watch_short is not None and short_trigger_ok and short_score >= self.cfg.trigger_score_min:
                ctx_short = SignalContext(
                    structure_bias=StructureBias.BEARISH,
                    zone_touched=zone_touched,
                    reclaim_confirmed=retest_gate,
                    filters_passed=True,
                    breaker=breaker,
                    at_risk_count=at_risk_count,
                    max_at_risk=self.cfg.max_at_risk_positions,
                )
                if should_enter_short(ctx_short):
                    risk_pct = self.cfg.risk_pct_high_conf if short_score >= self.cfg.high_conf_score_threshold else self.cfg.risk_pct_low_conf
                    size_mult = max(risk_pct / max(self.cfg.risk_pct_low_conf, 1e-9), 0.0)
                    p = self._build_position(b, "short", risk_pct=risk_pct, size_mult=size_mult, confluence_score=short_score)
                    positions.append(p)
                    events.append(
                        {
                            "index": b.index,
                            "event": "enter_short",
                            "zone_id": interaction.zone_id if interaction else None,
                            "entry": p.entry,
                            "stop": p.stop,
                            "risk_pct": p.risk_pct,
                            "size_mult": p.size_mult,
                            "confluence_score": p.confluence_score,
                            "retest_mode": "strict" if strict_retest else "near" if near_retest else "none",
                        }
                    )
                    action = "enter_short"
                    reason = "watch_triggered_short"
                    chosen_score = short_score
                    chosen_size_mult = size_mult
                    fsm_transition = "watch->trigger"
                    fsm_reason = "fib_candle_quality_pass"
                    watch_short = None
                else:
                    fsm_transition = "watch->invalid"
                    fsm_reason = "acceptance_failure"
                    events.append({"index": b.index, "event": "watch_invalid", "side": "short", "zone_id": watch_short.zone_id})
                    watch_short = None

            logs.append(
                {
                    "index": b.index,
                    "timestamp": getattr(b, "timestamp", None),
                    "symbol": symbol,
                    "tf": tf,
                    "structure_bias": bias.value,
                    "regime_state": regime.value,
                    "regime_choch_candidate": choch_candidate.value if choch_candidate else None,
                    "regime_transition": regime_transition,
                    "zone_id": interaction.zone_id if interaction else None,
                    "zone_kind": interaction.kind.value if interaction else None,
                    "zone_touched": zone_touched,
                    "strict_retest": strict_retest,
                    "near_retest": near_retest,
                    "retest_gate": retest_gate,
                    "reclaim_confirmed": reclaim_gate,
                    "zone_distance_bps": interaction.distance_bps if interaction else None,
                    "regime_gate": regime_gate,
                    "chop_ok": chop_ok,
                    "cooldown_active": cooldown_active,
                    "long_bias_ok": long_bias_ok,
                    "short_bias_ok": short_bias_ok,
                    "long_trend_ok": long_trend_ok,
                    "short_trend_ok": short_trend_ok,
                    "long_momo_ok": long_momo_ok,
                    "short_momo_ok": short_momo_ok,
                    "long_loc_ok": long_loc_ok,
                    "short_loc_ok": short_loc_ok,
                    "long_fib_ok": long_fib_ok,
                    "short_fib_ok": short_fib_ok,
                    "fib_position": fib_pos,
                    "fib_1d_anchor_source": fib_anchor_1d.source,
                    "fib_1d_anchor_reason": fib_anchor_1d.reason,
                    "fib_1d_anchor_available": fib_anchor_1d.available,
                    "fib_1d_anchor_bias_side": fib_bias_side_1d,
                    "fib_1d_phase1_confidence": fib_phase1_conf_1d,
                    "fib_1d_anchor_start_id": fib_anchor_1d.start_id,
                    "fib_1d_anchor_end_id": fib_anchor_1d.end_id,
                    "fib_1d_anchor_start_price": fib_anchor_1d.start_price,
                    "fib_1d_anchor_end_price": fib_anchor_1d.end_price,
                    "fib_4h_anchor_source": fib_anchor_4h.source,
                    "fib_4h_anchor_reason": fib_anchor_4h.reason,
                    "fib_4h_anchor_available": fib_anchor_4h.available,
                    "fib_4h_anchor_bias_side": fib_bias_side_4h,
                    "fib_4h_phase1_confidence": fib_phase1_conf_4h,
                    "fib_4h_anchor_start_id": fib_anchor_4h.start_id,
                    "fib_4h_anchor_end_id": fib_anchor_4h.end_id,
                    "fib_4h_anchor_start_price": fib_anchor_4h.start_price,
                    "fib_4h_anchor_end_price": fib_anchor_4h.end_price,
                    "fib_1w_anchor_source": fib_anchor_1w.source,
                    "fib_1w_anchor_reason": fib_anchor_1w.reason,
                    "fib_1w_anchor_available": fib_anchor_1w.available,
                    "fib_1w_anchor_bias_side": fib_bias_side_1w,
                    "fib_1w_phase1_confidence": fib_phase1_conf_1w,
                    "fib_1w_anchor_start_id": fib_anchor_1w.start_id,
                    "fib_1w_anchor_end_id": fib_anchor_1w.end_id,
                    "fib_1w_anchor_start_price": fib_anchor_1w.start_price,
                    "fib_1w_anchor_end_price": fib_anchor_1w.end_price,
                    "fib_quality_score": fib_ctx.fib_quality_score,
                    "fib_overall_state": fib_ctx.overall_state,
                    "fib_overall_reason": fib_ctx.overall_reason,
                    "fib_overlap_cluster": fib_ctx.overlap_cluster,
                    "fib_has_1d_4h_overlap": fib_ctx.has_1d_4h_overlap,
                    "fib_has_1w_bonus_overlap": fib_ctx.has_1w_bonus_overlap,
                    "fib_active_timeframes": ",".join(fib_ctx.active_timeframes),
                    "fib_1d_state": fib_1d.fib_state.value,
                    "fib_1d_interaction": fib_1d.band_interaction.value,
                    "fib_1d_sub_zone": fib_1d.sub_zone.value,
                    "fib_1d_disarm_reason": fib_1d.disarm_reason.value,
                    "fib_1d_level_0_618": fib_1d.level_0_618,
                    "fib_1d_level_0_705": fib_1d.level_0_705,
                    "fib_1d_level_0_786": fib_1d.level_0_786,
                    "fib_1d_level_0_886": fib_1d.level_0_886,
                    "fib_1d_band_low": fib_1d.band_low,
                    "fib_1d_band_high": fib_1d.band_high,
                    "fib_1d_score_contribution": fib_1d.tf_score_contribution,
                    "fib_1d_level_0_618_tapped_before": fib_taps_1d["level_0_618_tapped_before"],
                    "fib_1d_level_0_705_tapped_before": fib_taps_1d["level_0_705_tapped_before"],
                    "fib_1d_level_0_786_tapped_before": fib_taps_1d["level_0_786_tapped_before"],
                    "fib_1d_band_tapped_before": fib_taps_1d["band_tapped_before"],
                    "fib_1d_band_tap_count_before": fib_taps_1d["band_tap_count_before"],
                    "fib_1d_band_first_tap_index": fib_taps_1d["band_first_tap_index"],
                    "fib_1d_band_last_tap_index": fib_taps_1d["band_last_tap_index"],
                    "fib_4h_state": fib_4h.fib_state.value,
                    "fib_4h_interaction": fib_4h.band_interaction.value,
                    "fib_4h_sub_zone": fib_4h.sub_zone.value,
                    "fib_4h_disarm_reason": fib_4h.disarm_reason.value,
                    "fib_4h_level_0_618": fib_4h.level_0_618,
                    "fib_4h_level_0_705": fib_4h.level_0_705,
                    "fib_4h_level_0_786": fib_4h.level_0_786,
                    "fib_4h_level_0_886": fib_4h.level_0_886,
                    "fib_4h_band_low": fib_4h.band_low,
                    "fib_4h_band_high": fib_4h.band_high,
                    "fib_4h_score_contribution": fib_4h.tf_score_contribution,
                    "fib_4h_level_0_618_tapped_before": fib_taps_4h["level_0_618_tapped_before"],
                    "fib_4h_level_0_705_tapped_before": fib_taps_4h["level_0_705_tapped_before"],
                    "fib_4h_level_0_786_tapped_before": fib_taps_4h["level_0_786_tapped_before"],
                    "fib_4h_band_tapped_before": fib_taps_4h["band_tapped_before"],
                    "fib_4h_band_tap_count_before": fib_taps_4h["band_tap_count_before"],
                    "fib_4h_band_first_tap_index": fib_taps_4h["band_first_tap_index"],
                    "fib_4h_band_last_tap_index": fib_taps_4h["band_last_tap_index"],
                    "fib_1w_state": fib_1w.fib_state.value,
                    "fib_1w_interaction": fib_1w.band_interaction.value,
                    "fib_1w_sub_zone": fib_1w.sub_zone.value,
                    "fib_1w_disarm_reason": fib_1w.disarm_reason.value,
                    "fib_1w_level_0_618": fib_1w.level_0_618,
                    "fib_1w_level_0_705": fib_1w.level_0_705,
                    "fib_1w_level_0_786": fib_1w.level_0_786,
                    "fib_1w_level_0_886": fib_1w.level_0_886,
                    "fib_1w_band_low": fib_1w.band_low,
                    "fib_1w_band_high": fib_1w.band_high,
                    "fib_1w_score_contribution": fib_1w.tf_score_contribution,
                    "fib_1w_level_0_618_tapped_before": fib_taps_1w["level_0_618_tapped_before"],
                    "fib_1w_level_0_705_tapped_before": fib_taps_1w["level_0_705_tapped_before"],
                    "fib_1w_level_0_786_tapped_before": fib_taps_1w["level_0_786_tapped_before"],
                    "fib_1w_band_tapped_before": fib_taps_1w["band_tapped_before"],
                    "fib_1w_band_tap_count_before": fib_taps_1w["band_tap_count_before"],
                    "fib_1w_band_first_tap_index": fib_taps_1w["band_first_tap_index"],
                    "fib_1w_band_last_tap_index": fib_taps_1w["band_last_tap_index"],
                    "long_candle_ok": long_candle_ok,
                    "short_candle_ok": short_candle_ok,
                    "retest_ordinal": retest_ordinal,
                    "long_quality_ok": long_quality_ok,
                    "short_quality_ok": short_quality_ok,
                    "long_candle_score": long_candle_score,
                    "short_candle_score": short_candle_score,
                    "long_score": long_score,
                    "short_score": short_score,
                    "long_score_ok": long_score_ok,
                    "short_score_ok": short_score_ok,
                    "long_watch_ok": long_watch_ok,
                    "short_watch_ok": short_watch_ok,
                    "long_trigger_ok": long_trigger_ok,
                    "short_trigger_ok": short_trigger_ok,
                    "trigger_score_min": self.cfg.trigger_score_min,
                    "selected_score": chosen_score,
                    "size_mult": chosen_size_mult,
                    "watch_long_state": EntryFSMState.WATCH.value if watch_long else EntryFSMState.IDLE.value,
                    "watch_short_state": EntryFSMState.WATCH.value if watch_short else EntryFSMState.IDLE.value,
                    "fsm_transition": fsm_transition,
                    "fsm_reason": fsm_reason,
                    "retest_mode": "strict" if strict_retest else "near" if near_retest else "none",
                    "filters_passed": (long_trigger_ok if action == "enter_long" else short_trigger_ok if action == "enter_short" else False),
                    "at_risk_count": self._count_at_risk(positions),
                    "breaker_open": breaker.is_open,
                    "action": action,
                    "reason": reason,
                    "dynamic_levels": dynamic_levels_log,
                }
            )
            prev_bar = b

        return events, logs
