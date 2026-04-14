from __future__ import annotations

from pathlib import Path

from liquidsniper.core.sr_universe import (
    CANONICAL_SR_SOURCE,
    discover_symbol_tf_files,
    load_validation_basket,
    resolve_market_structure_csv,
)
from liquidsniper.ops.sr_bootstrap import _resolve_requested_symbols


def test_validation_basket_loads_cleaned_majors_contract() -> None:
    basket = load_validation_basket()
    symbols = [row.symbol for row in basket]
    assert symbols[:5] == ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]
    assert len(symbols) >= 15


def test_discover_symbol_tf_files_prefers_canonical_okx_corpus() -> None:
    mapping, missing = discover_symbol_tf_files(symbols=["BTCUSDT", "ETHUSDT"], source=CANONICAL_SR_SOURCE)
    assert missing == []
    assert mapping["BTCUSDT"]["1D"].endswith("btc_1d_okx_ccxt_2022_to_now.csv")
    assert mapping["ETHUSDT"]["4H"].endswith("eth_4h_okx_ccxt_2022_to_now.csv")


def test_resolve_market_structure_csv_prefers_okx_when_multiple_sources_exist() -> None:
    path = resolve_market_structure_csv("BTCUSDT", "1D")
    assert isinstance(path, Path)
    assert path.name == "btc_1d_okx_ccxt_2022_to_now.csv"


def test_resolve_requested_symbols_expands_config_driven_universe_when_cli_is_default_pair() -> None:
    cfg = {
        "universe": {
            "basket_path": "IntradayTrading/spec/phases/PHASE2_ZONE_ENGINE_V3_VALIDATION_BASKET_2026-03-10.json",
            "source": CANONICAL_SR_SOURCE,
        }
    }

    assert _resolve_requested_symbols("BTCUSDT,ETHUSDT", cfg) == []


def test_resolve_requested_symbols_preserves_explicit_cli_override_with_config_present() -> None:
    cfg = {
        "universe": {
            "basket_path": "IntradayTrading/spec/phases/PHASE2_ZONE_ENGINE_V3_VALIDATION_BASKET_2026-03-10.json",
            "source": CANONICAL_SR_SOURCE,
        }
    }

    assert _resolve_requested_symbols("SOLUSDT,ADAUSDT", cfg) == ["SOLUSDT", "ADAUSDT"]
