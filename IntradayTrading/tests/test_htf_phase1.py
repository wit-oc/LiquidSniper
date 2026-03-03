from intraday_revisit.engine.htf_phase1 import detect_swings, run_phase1_htf_structure


def test_detect_swings_reports_pivot_and_confirmation_indices():
    highs = [1, 2, 5, 2, 1, 2, 4, 2, 1]
    lows = [1, 1, 1, 1, 0.5, 1, 1, 1, 1]
    swings = detect_swings(highs, lows, left=1, right=1)

    high_swings = [s for s in swings if s.kind == "high"]
    assert any(s.pivot_index == 2 and s.confirmed_index == 3 for s in high_swings)
    assert any(s.pivot_index == 6 and s.confirmed_index == 7 for s in high_swings)


def test_choch_persists_transitional_until_bos_confirms():
    highs = [100, 101, 102, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 93, 92, 91, 90, 89, 88, 89, 88, 87, 86, 84, 83, 82]
    lows = [99, 100, 101, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 92, 91, 90, 89, 88, 87, 88, 87, 86, 85, 80, 79, 78]
    closes = [99.5, 100.5, 101.5, 102.8, 101.6, 100.6, 99.6, 98.6, 97.6, 96.6, 95.6, 94.6, 93.6, 92.6, 91.6, 92.4, 91.4, 90.4, 89.4, 88.4, 87.4, 88.3, 87.3, 86.3, 85.3, 80.5, 79.5, 78.5]

    bars, events, _ = run_phase1_htf_structure(highs, lows, closes, n_init=5, break_min_frac_of_candle=0.2)

    choch = [e for e in events if e["event"] == "choch_detected"]
    bos = [e for e in events if e["event"] == "bos_confirmed"]

    assert choch
    assert bos
    assert choch[0]["index"] < bos[0]["index"]
    assert all(bars[i]["regime_confidence"] == "transitional" for i in range(choch[0]["index"], bos[0]["index"]))
    assert bars[bos[0]["index"]]["regime_confidence"] == "confirmed"


def test_back_to_back_choch_updates_tentative_direction():
    highs = [100, 101, 102, 103, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 95, 96, 97, 98, 99, 100, 105, 106, 107, 108]
    lows = [99, 100, 101, 102, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 94, 95, 96, 97, 98, 99, 104, 105, 106, 107]
    closes = [99.6, 100.6, 101.6, 102.6, 103.6, 102.4, 101.4, 100.4, 99.4, 98.4, 97.4, 96.4, 95.4, 94.4, 93.4, 94.6, 95.6, 96.6, 97.6, 98.6, 99.6, 104.8, 105.8, 106.8, 107.8]

    bars, events, _ = run_phase1_htf_structure(highs, lows, closes, n_init=5, break_min_frac_of_candle=0.2)
    choch = [e for e in events if e["event"] == "choch_detected"]

    assert len(choch) >= 2
    assert choch[0]["regime_direction"] != choch[1]["regime_direction"]
    assert bars[choch[1]["index"]]["regime_confidence"] == "transitional"


def test_one_shot_choch_dedupes_repeated_breaks_same_level():
    highs = [100, 101, 102, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81]
    lows = [99, 100, 101, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80]
    closes = [99.5, 100.5, 101.5, 102.7, 101.6, 100.6, 99.6, 98.6, 97.6, 96.6, 95.6, 94.6, 93.6, 92.6, 91.6, 90.6, 89.6, 88.6, 87.6, 86.6, 85.6, 84.6, 83.6, 82.6, 81.6, 80.6]

    _, events, _ = run_phase1_htf_structure(highs, lows, closes, n_init=5, break_min_frac_of_candle=0.2)
    choch = [e for e in events if e["event"] == "choch_detected"]

    assert len(choch) == 1


def test_bos_locks_opposing_anchor_to_window_extreme():
    highs = [10, 11, 12, 12, 12, 12, 12]
    lows = [9, 10, 11, 11, 11, 11, 11]
    closes = [9.5, 10.5, 11.5, 12.2, 12.3, 12.4, 12.5]

    bars, events, _ = run_phase1_htf_structure(
        highs,
        lows,
        closes,
        n_init=3,
        break_min_frac_of_candle=0.15,
        bos_require_fresh_cross=True,
    )

    bos = next(e for e in events if e["event"] == "bos_confirmed")
    lock = next(e for e in events if e["event"] == "swing_low_locked")

    assert bos["index"] == 3
    assert bos["anchor_index"] == 2
    assert lock["anchor_index"] == 2
    assert lock["price"] == 11
    assert bars[bos["index"]]["protected_low_idx"] == 2
    assert bars[bos["index"]]["protected_low"] == 11


def test_bos_fresh_cross_blocks_repeated_same_side_closes():
    highs = [10, 11, 12, 12, 12, 12, 12]
    lows = [9, 10, 11, 11, 11, 11, 11]
    closes = [9.5, 10.5, 11.5, 12.2, 12.3, 12.4, 12.5]

    bars, events, _ = run_phase1_htf_structure(
        highs,
        lows,
        closes,
        n_init=3,
        break_min_frac_of_candle=0.15,
        bos_require_fresh_cross=True,
    )

    bos = [e for e in events if e["event"] == "bos_confirmed"]
    assert len(bos) == 1
    assert bars[4]["bos_check"]["blocked_reason"] == "no_fresh_cross"
    assert bars[5]["bos_check"]["blocked_reason"] == "no_fresh_cross"
    assert bars[6]["bos_check"]["blocked_reason"] == "no_fresh_cross"


def test_phase1_engine_is_deterministic():
    highs = [10, 11, 12, 11, 12, 13, 12, 11, 10, 9, 8]
    lows = [9.0, 9.5, 10.0, 9.2, 9.7, 10.4, 9.6, 9.0, 8.8, 8.5, 8.0]
    closes = [9.5, 10.6, 11.4, 9.6, 11.3, 12.5, 10.0, 9.1, 8.7, 8.3, 7.9]

    a = run_phase1_htf_structure(highs, lows, closes, left=1, right=1, initial_direction="bullish")
    b = run_phase1_htf_structure(highs, lows, closes, left=1, right=1, initial_direction="bullish")

    assert a == b
