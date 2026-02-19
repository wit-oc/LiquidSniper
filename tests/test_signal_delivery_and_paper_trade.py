from __future__ import annotations

import json
from pathlib import Path

from liquidsniper.core.paper_trade import append_journal, read_journal
from liquidsniper.core.signal_delivery import make_signal_packet, render_discord_payload, render_imessage_payload


SAMPLE = {
    "symbol": "BTCUSDT",
    "side": "long",
    "final_score": 74.2,
    "decision": "publish_candidate",
    "thesis": "HTF trend intact with clean retest.",
    "chart_context": "https://tradingview.com/chart/example",
}


def _expected() -> dict:
    p = Path(__file__).parent / "fixtures" / "signal_snapshot_expected.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_signal_payload_snapshots() -> None:
    pkt = make_signal_packet(SAMPLE)
    d = render_discord_payload(pkt)
    i = render_imessage_payload(pkt)

    exp = _expected()
    for s in exp["discord_contains"]:
        assert s in d["content"]
    for s in exp["imessage_contains"]:
        assert s in i["text"]


def test_paper_trade_journal_append_and_read(tmp_path: Path) -> None:
    journal = tmp_path / "journal.jsonl"
    append_journal(journal, SAMPLE)
    rows = read_journal(journal)

    assert len(rows) == 1
    assert rows[0]["symbol"] == "BTCUSDT"
    assert rows[0]["decision"] == "publish_candidate"
    assert "discord_payload" in rows[0]
    assert "imessage_payload" in rows[0]
    assert rows[0]["stop_policy"]["move_to_break_even_on_tp1"] is True


def test_paper_trade_journal_includes_trade_detail_fields(tmp_path: Path) -> None:
    journal = tmp_path / "journal_details.jsonl"
    row = {
        **SAMPLE,
        "entry": 2012.5,
        "stop_loss": 1978.0,
        "tp_levels": [2060.0, 2125.0, 2190.0],
        "tp_plan": [
            {"level": 2060.0, "size_pct": 0.4},
            {"level": 2125.0, "size_pct": 0.35},
            {"level": 2190.0, "size_pct": 0.25},
        ],
        "tp_events": [{"level": 2060.0, "hit_ts": "2026-02-19T05:10:00Z"}],
        "exit_reason": "tp",
        "outcome": "partial_tp",
        "pnl_r": 0.8,
        "pnl_pct": 0.34,
    }

    append_journal(journal, row)
    out = read_journal(journal)[0]

    assert out["entry"] == 2012.5
    assert out["stop_loss_initial"] == 1978.0
    assert out["tp_levels"] == [2060.0, 2125.0, 2190.0]
    assert len(out["tp_plan"]) == 3
    assert out["tp_events"][0]["level"] == 2060.0
    assert out["stop_policy"]["break_even_price"] == 2012.5
    assert out["exit_reason"] == "tp"
    assert out["pnl_r"] == 0.8
