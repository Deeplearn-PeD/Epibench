"""Scoring package: rubric (pure math), reference loader, and auto-scorer."""

from __future__ import annotations

from .auto import AutoScoreResult, auto_score
from .reference import ReferenceAnswer, load_all_references, load_reference
from .rubric import (
    CategoryScores,
    Penalty,
    ScoreBreakdown,
    classify_total,
    score_task,
)

__all__ = [
    "auto_score",
    "AutoScoreResult",
    "load_reference",
    "load_all_references",
    "ReferenceAnswer",
    "score_task",
    "ScoreBreakdown",
    "CategoryScores",
    "Penalty",
    "classify_total",
]
