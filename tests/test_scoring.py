from __future__ import annotations

import pytest

from epibench.scoring.rubric import (
    PENALTY_POINTS,
    CategoryScores,
    Penalty,
    apply_penalties,
    classify_total,
    compute_positive_score,
    methodological_credit,
    numerical_credit,
    score_task,
)
from epibench.tasks import TOTAL_MAX_POINTS


# --------------------------------------------------------------------------- #
# §5.3 numerical tiers
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "reference,candidate,expected_credit",
    [
        (100, 100, 1.00),  # exact
        (100, 100.5, 0.95),  # within 1%
        (100, 103, 0.80),  # within 5%
        (100, 108, 0.60),  # within 10%
        (100, 120, 0.00),  # beyond 10%
    ],
)
def test_numerical_credit_tiers(reference, candidate, expected_credit):
    credit, tier = numerical_credit(reference, candidate)
    assert credit == pytest.approx(expected_credit)


def test_numerical_credit_zero_reference():
    credit, _ = numerical_credit(0, 0)
    assert credit == 1.0
    credit, _ = numerical_credit(0, 1)
    assert credit == 0.0


# --------------------------------------------------------------------------- #
# §5.3 methodological credit
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "method,result,expected",
    [
        (True, True, 1.00),
        (True, False, 0.40),
        (False, True, 0.20),
        (False, False, 0.00),
    ],
)
def test_methodological_credit(method, result, expected):
    assert methodological_credit(method, result) == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# §5.2 penalty table & rules
# --------------------------------------------------------------------------- #
def test_penalty_table_matches_readme():
    assert PENALTY_POINTS[Penalty.FABRICATED_CITATION] == -10
    assert PENALTY_POINTS[Penalty.INCORRECT_SOURCE] == -5
    assert PENALTY_POINTS[Penalty.MISLEADING_VIZ] == -5
    assert PENALTY_POINTS[Penalty.PRIVACY_VIOLATION] == -20
    assert PENALTY_POINTS[Penalty.UNIT_SCALE_ERROR] == -3


def test_penalties_stack_and_floor_at_zero():
    # Two penalties totalling -15 on a 26-point positive → 11.
    final, privacy = apply_penalties(
        26.0,
        {Penalty.FABRICATED_CITATION: -10, Penalty.INCORRECT_SOURCE: -5},
        max_points=30,
    )
    assert final == pytest.approx(11.0)
    assert privacy is False


def test_penalty_floor():
    final, _ = apply_penalties(3.0, {Penalty.FABRICATED_CITATION: -10}, max_points=30)
    assert final == 0.0


def test_privacy_violation_auto_fails():
    final, privacy = apply_penalties(26.0, {Penalty.PRIVACY_VIOLATION: -20}, max_points=30)
    assert final == 0.0
    assert privacy is True


def test_penalty_capped_at_max_points():
    # Stacked penalties exceeding max points are capped.
    final, _ = apply_penalties(
        26.0,
        {
            Penalty.FABRICATED_CITATION: -10,
            Penalty.INCORRECT_SOURCE: -5,
            Penalty.MISLEADING_VIZ: -5,
            Penalty.UNIT_SCALE_ERROR: -3,
        },
        max_points=20,
    )
    # Deduction capped at -20 → 26-20 = 6.
    assert final == pytest.approx(6.0)


# --------------------------------------------------------------------------- #
# §5.2 impact examples (the README table for a Gold task at 26/30)
# --------------------------------------------------------------------------- #
def _gold_positive() -> float:
    # Build a CategoryScores whose weighted sum gives 26/30.
    # All five categories at fraction f → positive = 30 * f. So f = 26/30.
    f = 26.0 / 30.0
    return compute_positive_score(
        30,
        CategoryScores(
            data_retrieval=f,
            methodology=f,
            interpretation=f,
            visualization=f,
            citations=f,
        ),
    )


def test_readme_impact_examples():
    positive = _gold_positive()
    assert positive == pytest.approx(26.0, abs=1e-6)

    # Strong analysis, no errors → 26
    assert score_task(30, _category(26, 30), {}).final == pytest.approx(26.0)
    # +1 fabricated citation → 16
    assert score_task(
        30, _category(26, 30), {Penalty.FABRICATED_CITATION: -10}
    ).final == pytest.approx(16.0)
    # +misleading viz → 21
    assert score_task(
        30, _category(26, 30), {Penalty.MISLEADING_VIZ: -5}
    ).final == pytest.approx(21.0)
    # fabricated + wrong source → 11
    assert score_task(
        30,
        _category(26, 30),
        {Penalty.FABRICATED_CITATION: -10, Penalty.INCORRECT_SOURCE: -5},
    ).final == pytest.approx(11.0)
    # privacy violation → 0
    res = score_task(30, _category(26, 30), {Penalty.PRIVACY_VIOLATION: -20})
    assert res.final == 0.0
    assert res.privacy_violation is True


def _category(points: float, max_points: int) -> CategoryScores:
    f = points / max_points
    return CategoryScores(
        data_retrieval=f,
        methodology=f,
        interpretation=f,
        visualization=f,
        citations=f,
    )


# --------------------------------------------------------------------------- #
# Partial-category scoring normalizes over evaluated categories only
# --------------------------------------------------------------------------- #
def test_partial_categories_normalize():
    # If only data_retrieval (35%) is evaluated and it's perfect, the positive
    # score should be the full max_points (not 35% of it).
    cs = CategoryScores(data_retrieval=1.0)
    assert compute_positive_score(30, cs) == pytest.approx(30.0)


def test_no_categories_scored_is_zero():
    assert compute_positive_score(30, CategoryScores()) == 0.0


# --------------------------------------------------------------------------- #
# Overall tier classification (§5.3 grading scale)
# --------------------------------------------------------------------------- #
# Tier bands are defined by PERCENTAGE in the README. The per-task points sum
# to 610 (see tasks.TOTAL_MAX_POINTS), so we assert on the percentage
# boundaries rather than absolute point values.
@pytest.mark.parametrize(
    "pct,tier",
    [
        (1.00, "S"),  # 100%
        (0.90, "S"),  # 90% exactly
        (0.89, "A"),
        (0.75, "A"),  # 75% exactly
        (0.74, "B"),
        (0.60, "B"),  # 60% exactly
        (0.59, "C"),
        (0.40, "C"),  # 40% exactly
        (0.39, "D"),
        (0.20, "D"),  # 20% exactly
        (0.19, "F"),
        (0.0, "F"),
    ],
)
def test_overall_tier_classification(pct, tier):
    points = TOTAL_MAX_POINTS * pct
    assert classify_total(points).value == tier


def test_overall_tier_disqualified_on_privacy():
    assert classify_total(500, privacy_violation=True).value == "Disqualified"
