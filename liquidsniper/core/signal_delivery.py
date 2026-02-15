"""Deterministic signal delivery payloads for Discord and iMessage.

No network sends here; this module only builds canonical message payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SignalPacket:
    symbol: str
    side: str
    final_score: float
    decision: str
    confidence_band: str
    thesis: str
    chart_context: str | None = None


def confidence_band(score: float) -> str:
    s = float(score)
    if s >= 80:
        return "high"
    if s >= 70:
        return "medium"
    if s >= 60:
        return "watch"
    return "low"


def make_signal_packet(row: dict[str, Any]) -> SignalPacket:
    score = round(float(row.get("final_score") or 0.0), 2)
    return SignalPacket(
        symbol=str(row.get("symbol") or "UNKNOWN"),
        side=str(row.get("side") or "unknown"),
        final_score=score,
        decision=str(row.get("decision") or "watch_only"),
        confidence_band=confidence_band(score),
        thesis=str(row.get("thesis") or "No thesis provided."),
        chart_context=row.get("chart_context"),
    )


def render_discord_payload(pkt: SignalPacket) -> dict[str, Any]:
    lines = [
        f"LiquidSniper Signal — {pkt.symbol}",
        f"Decision: {pkt.decision}",
        f"Score: {pkt.final_score} ({pkt.confidence_band})",
        f"Side: {pkt.side}",
        f"Thesis: {pkt.thesis}",
    ]
    if pkt.chart_context:
        lines.append(f"Chart: {pkt.chart_context}")

    return {
        "platform": "discord",
        "content": "\n".join(lines),
        "meta": {
            "symbol": pkt.symbol,
            "decision": pkt.decision,
            "score": pkt.final_score,
            "confidence_band": pkt.confidence_band,
        },
    }


def render_imessage_payload(pkt: SignalPacket) -> dict[str, Any]:
    # Keep concise for iMessage.
    text = (
        f"LiquidSniper {pkt.symbol} | {pkt.decision} | "
        f"score {pkt.final_score} ({pkt.confidence_band}) | {pkt.side}. "
        f"{pkt.thesis}"
    )
    if pkt.chart_context:
        text += f" Chart: {pkt.chart_context}"

    return {
        "platform": "imessage",
        "text": text,
        "meta": {
            "symbol": pkt.symbol,
            "decision": pkt.decision,
            "score": pkt.final_score,
            "confidence_band": pkt.confidence_band,
        },
    }
