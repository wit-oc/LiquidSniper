"""TradingView screenshot artifact persistence + UI link helpers."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import PurePosixPath

UI_TIMEFRAME_ORDER = ("15m", "1h", "4h", "1D", "1W")


@dataclass(frozen=True)
class ArtifactMountContract:
    """Shared mount contract between backend writer and UI reader."""

    writer_root: PurePosixPath = PurePosixPath("/data/artifacts")
    ui_root: PurePosixPath = PurePosixPath("/artifacts")

    @classmethod
    def from_env(cls) -> "ArtifactMountContract":
        writer = os.getenv("TV_ARTIFACTS_WRITER_ROOT", "/data/artifacts")
        ui = os.getenv("TV_ARTIFACTS_UI_ROOT", "/artifacts")
        return cls(writer_root=PurePosixPath(writer), ui_root=PurePosixPath(ui))

    def to_ui_href(self, artifact_path: str) -> str:
        """Translate backend artifact path to UI-visible mount path."""
        src = PurePosixPath(artifact_path)
        try:
            rel = src.relative_to(self.writer_root)
        except ValueError:
            return artifact_path
        return str(self.ui_root / rel)


def insert_screenshot_artifact(
    conn: sqlite3.Connection,
    *,
    analysis_run_id: int,
    timeframe: str,
    captured_ts: str,
    artifact_path: str,
    source_chart_url: str | None = None,
    artifact_hash: str | None = None,
) -> int:
    """Persist one screenshot artifact row."""
    with conn:
        cur = conn.execute(
            """
            INSERT INTO screenshot_artifacts(
                analysis_run_id, timeframe, captured_ts, source_chart_url, artifact_path, artifact_hash
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                int(analysis_run_id),
                timeframe,
                captured_ts,
                source_chart_url,
                artifact_path,
                artifact_hash,
            ),
        )
    return int(cur.lastrowid)


def query_ui_artifact_links(
    conn: sqlite3.Connection,
    *,
    analysis_run_id: int,
    mount: ArtifactMountContract | None = None,
) -> dict[str, str | None]:
    """Return timeframe-keyed UI links for 15m/1h/4h/1D/1W."""
    contract = mount or ArtifactMountContract.from_env()
    links: dict[str, str | None] = {tf: None for tf in UI_TIMEFRAME_ORDER}

    rows = conn.execute(
        """
        SELECT timeframe, artifact_path
        FROM screenshot_artifacts
        WHERE analysis_run_id = ?
        ORDER BY captured_ts DESC, id DESC;
        """,
        (int(analysis_run_id),),
    ).fetchall()

    for timeframe, artifact_path in rows:
        tf = str(timeframe)
        if tf not in links or links[tf] is not None:
            continue
        links[tf] = contract.to_ui_href(str(artifact_path))

    return links
