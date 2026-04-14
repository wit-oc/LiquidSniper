from intraday_revisit.engine.structure import (
    RegimeState,
    StructureBias,
    classify_structure_from_pivots,
    detect_pivots,
    project_regime,
)


def test_detect_pivots_basic():
    highs = [1, 2, 5, 2, 1, 2, 4, 2, 1]
    lows = [1, 1, 1, 1, 0.5, 1, 1, 1, 1]
    pivots = detect_pivots(highs, lows, left=1, right=1)

    # Known obvious peaks around indices 2 and 6
    high_idxs = [p.index for p in pivots if p.kind == "high"]
    assert 2 in high_idxs
    assert 6 in high_idxs


def test_pivot_requires_right_bars_no_lookahead():
    highs_short = [1, 2, 5]
    lows_short = [1, 1, 1]
    pivots_short = detect_pivots(highs_short, lows_short, left=1, right=1)
    assert len(pivots_short) == 0

    highs_full = [1, 2, 5, 2]
    lows_full = [1, 1, 1, 1]
    pivots_full = detect_pivots(highs_full, lows_full, left=1, right=1)
    assert any(p.index == 2 and p.kind == "high" for p in pivots_full)


def test_classify_structure_bullish_transition():
    # synthetic pivot sequence: HH + HL progression
    class P:
        def __init__(self, index, price, kind):
            self.index = index
            self.price = price
            self.kind = kind

    pivots = [
        P(1, 100, "low"),
        P(2, 110, "high"),
        P(3, 103, "low"),
        P(4, 115, "high"),
    ]

    points = classify_structure_from_pivots(pivots)
    assert points[-1].bias == StructureBias.BULLISH
    assert any(p.transition for p in points)


def test_project_regime_requires_choch_then_bos_for_flip():
    points = [
        type("S", (), {"index": 1, "bias": StructureBias.BULLISH, "transition": True})(),
        type("S", (), {"index": 2, "bias": StructureBias.BEARISH, "transition": True})(),
        type("S", (), {"index": 3, "bias": StructureBias.NEUTRAL, "transition": False})(),
        type("S", (), {"index": 4, "bias": StructureBias.BEARISH, "transition": True})(),
    ]

    projected = project_regime(points, initial=RegimeState.BULLISH)
    assert projected[1].regime == RegimeState.BULLISH
    assert projected[1].choch_candidate == RegimeState.BEARISH
    assert projected[-1].regime == RegimeState.BEARISH
    assert projected[-1].bos_confirmed is True
