"""Hybrid confluence scoring skeleton for analysis runs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Decision(StrEnum):
    """Pipeline decision labels persisted to candidate_decisions."""

    PUBLISH_CANDIDATE = "publish_candidate"
    WATCH_ONLY = "watch_only"
    REJECT = "reject"


@dataclass(frozen=True)
class ScoreInputs:
    """Core staged scoring inputs for one analysis run."""

    zone_priority: float
    context: float
    agent_confidence: float = 0.0


def pre_score(inputs: ScoreInputs) -> float:
    """Compute deterministic pre-score from zone/context stages."""
    return (0.55 * float(inputs.zone_priority)) + (0.45 * float(inputs.context))


def final_score(inputs: ScoreInputs) -> float:
    """Blend deterministic and optional agent confidence into final score."""
    deterministic = pre_score(inputs)
    return (0.70 * deterministic) + (0.30 * float(inputs.agent_confidence))


def classify_decision(
    inputs: ScoreInputs,
    *,
    pre_score_floor: float = 60.0,
    publish_threshold: float = 70.0,
) -> Decision:
    """Apply v0 thresholding to classify the analysis decision."""
    p_score = pre_score(inputs)
    if p_score < float(pre_score_floor):
        return Decision.WATCH_ONLY

    if final_score(inputs) >= float(publish_threshold):
        return Decision.PUBLISH_CANDIDATE

    return Decision.REJECT
