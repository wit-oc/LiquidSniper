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
