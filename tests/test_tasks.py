from __future__ import annotations

from epibench.tasks import (
    TOTAL_MAX_POINTS,
    Level,
    all_tasks,
    get_task,
    parse_task_selector,
    tasks_by_level,
    total_max_points,
)


def test_all_21_tasks_present():
    tasks = all_tasks()
    assert len(tasks) == 21
    assert [t.id for t in tasks] == [f"T{i:02d}" for i in range(1, 22)]


def test_points_sum_to_610():
    # README states 540, but per-task points actually sum to 610 (see
    # tasks.TOTAL_MAX_POINTS note). We assert against the computed value.
    assert total_max_points() == TOTAL_MAX_POINTS == 610


def test_level_point_counts():
    # Bronze 2×10, Silver 4×20, Gold 9×30, Platinum 6×40.
    assert sum(t.max_points for t in tasks_by_level([Level.BRONZE])) == 20
    assert sum(t.max_points for t in tasks_by_level([Level.SILVER])) == 80
    assert sum(t.max_points for t in tasks_by_level([Level.GOLD])) == 270
    assert sum(t.max_points for t in tasks_by_level([Level.PLATINUM])) == 240


def test_platinum_tasks_cover_all_competencies():
    from epibench.tasks import Competency

    for t in tasks_by_level([Level.PLATINUM]):
        assert set(t.competencies) == set(Competency)


def test_get_task_case_insensitive():
    assert get_task("t01").name == "Multi-Source Data Discovery"
    assert get_task("T01").id == "T01"


def test_get_task_unknown_raises():
    import pytest

    with pytest.raises(KeyError):
        get_task("T99")


def test_parse_task_selector_all():
    assert len(parse_task_selector("all")) == 21


def test_parse_task_selector_explicit():
    sel = parse_task_selector("T01,T03")
    assert [t.id for t in sel] == ["T01", "T03"]


def test_parse_task_selector_levels():
    sel = parse_task_selector("bronze,silver")
    ids = {t.id for t in sel}
    assert ids == {f"T{i:02d}" for i in range(1, 7)}


def test_parse_task_selector_mixed_dedupes():
    # T01 is bronze; "T01,bronze" should list T01 exactly once.
    sel = parse_task_selector("T01;bronze")
    ids = [t.id for t in sel]
    assert ids.count("T01") == 1
    assert "T02" in ids


def test_parse_task_selector_empty_raises():
    import pytest

    with pytest.raises(ValueError):
        parse_task_selector("   ")
