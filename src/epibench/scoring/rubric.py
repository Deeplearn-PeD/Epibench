"""EpiBench-1.0 scoring rubric.

Encodes sections 5.1 (weighted categories), 5.2 (negative penalties),
5.3 (numerical accuracy tiers + methodological credit), and the overall
grading scale. Pure functions — no I/O — so everything here is unit-testable
against the worked examples in the README.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from ..tasks import CATEGORY_WEIGHTS, TOTAL_MAX_POINTS

# --------------------------------------------------------------------------- #
# Section 5.1 — weighted categories
# --------------------------------------------------------------------------- #
WEIGHTS: dict[str, float] = dict(CATEGORY_WEIGHTS)
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Category weights must sum to 1.0"


# --------------------------------------------------------------------------- #
# Section 5.2 — negative penalties
# --------------------------------------------------------------------------- #
class Penalty(StrEnum):
    FABRICATED_CITATION = "fabricated_citation"
    INCORRECT_SOURCE = "incorrect_source"
    MISLEADING_VIZ = "misleading_viz"
    PRIVACY_VIOLATION = "privacy_violation"
    UNIT_SCALE_ERROR = "unit_scale_error"


PENALTY_POINTS: dict[Penalty, int] = {
    Penalty.FABRICATED_CITATION: -10,
    Penalty.INCORRECT_SOURCE: -5,
    Penalty.MISLEADING_VIZ: -5,
    Penalty.PRIVACY_VIOLATION: -20,
    Penalty.UNIT_SCALE_ERROR: -3,
}


# --------------------------------------------------------------------------- #
# Section 5.3 — numerical accuracy tiers
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class NumericalTier:
    name: str
    max_deviation: float  # inclusive upper bound on |deviation|; inf for the last tier
    credit: float


NUMERICAL_TIERS: tuple[NumericalTier, ...] = (
    NumericalTier("exact", 0.0, 1.00),
    NumericalTier("within_1pct", 0.01, 0.95),
    NumericalTier("within_5pct", 0.05, 0.80),
    NumericalTier("within_10pct", 0.10, 0.60),
    NumericalTier("beyond_10pct", float("inf"), 0.00),
)


def numerical_credit(reference: float, candidate: float) -> tuple[float, NumericalTier]:
    """Return (credit in 0..1, matched tier) for a single numerical comparison."""
    if reference == 0:
        deviation = 0.0 if candidate == 0 else float("inf")
    else:
        deviation = abs(candidate - reference) / abs(reference)
    for tier in NUMERICAL_TIERS:
        if deviation <= tier.max_deviation + 1e-12:
            return tier.credit, tier
    return 0.0, NUMERICAL_TIERS[-1]


# --------------------------------------------------------------------------- #
# Section 5.3 — methodological credit
# --------------------------------------------------------------------------- #
def methodological_credit(method_correct: bool, result_correct: bool) -> float:
    """Combined method/result credit (README §5.3 table)."""
    if method_correct and result_correct:
        return 1.00
    if method_correct and not result_correct:
        return 0.40
    if not method_correct and result_correct:
        return 0.20
    return 0.00


# --------------------------------------------------------------------------- #
# Composite scoring
# --------------------------------------------------------------------------- #
@dataclass
class CategoryScores:
    """Per-category scores as fractions in 0..1. Missing = not evaluated."""

    data_retrieval: float | None = None
    methodology: float | None = None
    interpretation: float | None = None
    visualization: float | None = None
    citations: float | None = None

    def as_dict(self) -> dict[str, float | None]:
        return {
            "data_retrieval": self.data_retrieval,
            "methodology": self.methodology,
            "interpretation": self.interpretation,
            "visualization": self.visualization,
            "citations": self.citations,
        }


@dataclass
class ScoreBreakdown:
    raw_positive: float  # weighted positive score, 0..max_points
    penalties_applied: dict[Penalty, int] = field(default_factory=dict)
    privacy_violation: bool = False
    needs_human_review: bool = False
    category_scores: CategoryScores = field(default_factory=CategoryScores)
    final: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def total_penalty(self) -> int:
        return sum(self.penalties_applied.values())


def compute_positive_score(
    max_points: int,
    category_scores: CategoryScores,
) -> float:
    """Weighted sum of category fractions × max_points.

    Categories left as None (not evaluated) contribute 0 to the numerator *and*
    are dropped from the denominator, so a partially-evaluated task isn't
    unfairly dragged down. When all categories are None the positive score is 0.
    """
    num = 0.0
    den = 0.0
    for cat, frac in category_scores.as_dict().items():
        if frac is None:
            continue
        num += frac * WEIGHTS[cat]
        den += WEIGHTS[cat]
    if den == 0.0:
        return 0.0
    return max_points * (num / den)


def apply_penalties(
    positive: float,
    penalties: dict[Penalty, int],
    *,
    max_points: int,
) -> tuple[float, bool]:
    """Apply §5.2 penalty rules. Returns (final_score, privacy_violation).

    - Penalties stack.
    - Floor at 0.
    - Penalty deduction capped at the task's max points.
    - Privacy violation → automatic failure (score = 0).
    """
    if Penalty.PRIVACY_VIOLATION in penalties:
        return 0.0, True

    deduction = sum(penalties.values())  # already negative
    # Cap the magnitude of the deduction at max_points.
    if -deduction > max_points:
        deduction = -max_points
    final = positive + deduction
    if final < 0:
        final = 0.0
    return final, False


def score_task(
    max_points: int,
    category_scores: CategoryScores,
    penalties: dict[Penalty, int] | None = None,
    *,
    needs_human_review: bool = False,
    notes: list[str] | None = None,
) -> ScoreBreakdown:
    """Top-level per-task scoring. Reproduces the §5.2 impact examples."""
    penalties = dict(penalties or {})
    positive = compute_positive_score(max_points, category_scores)
    final, privacy = apply_penalties(positive, penalties, max_points=max_points)
    return ScoreBreakdown(
        raw_positive=positive,
        penalties_applied=penalties,
        privacy_violation=privacy,
        needs_human_review=needs_human_review,
        category_scores=category_scores,
        final=round(final, 4),
        notes=list(notes or []),
    )


# --------------------------------------------------------------------------- #
# Overall grading scale (section 5.3 — "Overall Grading Scale")
# --------------------------------------------------------------------------- #
class OverallTier(StrEnum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"
    DISQUALIFIED = "Disqualified"


@dataclass(frozen=True)
class TierBand:
    tier: OverallTier
    min_pct: float
    max_pct: float


TIER_BANDS: tuple[TierBand, ...] = (
    TierBand(OverallTier.S, 0.90, float("inf")),
    TierBand(OverallTier.A, 0.75, 0.90),
    TierBand(OverallTier.B, 0.60, 0.75),
    TierBand(OverallTier.C, 0.40, 0.60),
    TierBand(OverallTier.D, 0.20, 0.40),
    TierBand(OverallTier.F, 0.0, 0.20),
)


def classify_total(total_points: float, *, privacy_violation: bool = False) -> OverallTier:
    """Map an aggregate score (0..540) onto the README's overall tier scale."""
    if privacy_violation:
        return OverallTier.DISQUALIFIED
    pct = total_points / TOTAL_MAX_POINTS
    for band in TIER_BANDS:
        if band.min_pct <= pct < band.max_pct:
            return band.tier
    return OverallTier.F


__all__ = [
    "WEIGHTS",
    "Penalty",
    "PENALTY_POINTS",
    "NumericalTier",
    "NUMERICAL_TIERS",
    "numerical_credit",
    "methodological_credit",
    "CategoryScores",
    "ScoreBreakdown",
    "compute_positive_score",
    "apply_penalties",
    "score_task",
    "OverallTier",
    "TierBand",
    "TIER_BANDS",
    "classify_total",
]
