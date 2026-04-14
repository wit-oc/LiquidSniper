from tools.run_phase2_zone_engine_v3_validation_sweep import MVP_13_PAIR_UNIVERSE
from liquidsniper.core.sr_universe import discover_symbol_tf_files


def test_mvp_13_pair_universe_resolves_full_1d_4h_coverage() -> None:
    mapping, missing = discover_symbol_tf_files(symbols=MVP_13_PAIR_UNIVERSE)
    assert missing == []
    assert sorted(mapping.keys()) == sorted(MVP_13_PAIR_UNIVERSE)
    for symbol, tf_map in mapping.items():
        assert sorted(tf_map.keys()) == ["1D", "4H"], symbol
