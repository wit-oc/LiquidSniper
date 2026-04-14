from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANONICAL_SR_SOURCE = "okx_ccxt"
DEFAULT_VALIDATION_BASKET = Path("IntradayTrading/spec/phases/PHASE2_ZONE_ENGINE_V3_VALIDATION_BASKET_2026-03-10.json")
DEFAULT_DATA_ROOT = Path("IntradayTrading/data")
DEFAULT_TIMEFRAMES = ("1D", "4H")
TIMEFRAME_FILE_KEYS = {"1D": "1d", "4H": "4h", "1H": "1h", "15M": "15m"}
SOURCE_PRIORITY = ("okx_ccxt", "blofin_ccxt", "blofin_derived_from_1h")


@dataclass(frozen=True)
class UniverseSymbol:
    symbol: str
    name: str | None = None
    market_cap_rank: int | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_validation_basket(path: str | Path | None = None) -> list[UniverseSymbol]:
    basket_path = _repo_root() / (Path(path) if path else DEFAULT_VALIDATION_BASKET)
    payload = json.loads(basket_path.read_text(encoding="utf-8"))
    out: list[UniverseSymbol] = []
    for row in payload.get("symbols", []):
        symbol = str(row.get("symbol") or "").upper().strip()
        if not symbol:
            continue
        rank = row.get("market_cap_rank")
        out.append(
            UniverseSymbol(
                symbol=symbol,
                name=row.get("name"),
                market_cap_rank=int(rank) if rank is not None else None,
            )
        )
    return out


def symbol_to_asset(symbol: str) -> str:
    base = str(symbol or "").upper().strip()
    if base.endswith("USDT"):
        base = base[:-4]
    return "".join(ch for ch in base.lower() if ch.isalnum())


def discover_symbol_tf_files(
    *,
    symbols: list[str],
    source: str = CANONICAL_SR_SOURCE,
    timeframes: tuple[str, ...] = DEFAULT_TIMEFRAMES,
    data_root: str | Path = DEFAULT_DATA_ROOT,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    root = _repo_root() / Path(data_root)
    mapping: dict[str, dict[str, str]] = {}
    missing: list[str] = []
    source = str(source).strip()
    for symbol in symbols:
        asset = symbol_to_asset(symbol)
        tf_map: dict[str, str] = {}
        missing_tfs: list[str] = []
        for tf in timeframes:
            tf_key = TIMEFRAME_FILE_KEYS.get(str(tf).upper())
            if not tf_key:
                missing_tfs.append(str(tf))
                continue
            candidate = root / f"{asset}_{tf_key}_{source}_2022_to_now.csv"
            if candidate.exists():
                tf_map[str(tf).upper()] = str(candidate.relative_to(_repo_root()))
            else:
                missing_tfs.append(str(tf).upper())
        if tf_map:
            mapping[str(symbol).upper()] = tf_map
        if missing_tfs:
            missing.append(f"{str(symbol).upper()}:{','.join(missing_tfs)}")
    return mapping, missing


def resolve_market_structure_csv(symbol: str, tf: str, *, data_root: str | Path = DEFAULT_DATA_ROOT) -> Path | None:
    root = _repo_root() / Path(data_root)
    asset = symbol_to_asset(symbol)
    tf_key = TIMEFRAME_FILE_KEYS.get(str(tf).upper())
    if not asset or not tf_key:
        return None
    for source in SOURCE_PRIORITY:
        candidate = root / f"{asset}_{tf_key}_{source}_2022_to_now.csv"
        if candidate.exists():
            return candidate
    candidates = sorted(root.glob(f"{asset}_{tf_key}_*.csv"))
    return candidates[0] if candidates else None


def default_sr_symbol_tf_files() -> dict[str, dict[str, str]]:
    symbols = [row.symbol for row in load_validation_basket()]
    mapping, _missing = discover_symbol_tf_files(symbols=symbols)
    return mapping
