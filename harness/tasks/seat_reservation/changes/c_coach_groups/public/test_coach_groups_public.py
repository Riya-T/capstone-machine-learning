"""Public checks for the c_coach_groups change (coach groups). Shown to the
editor, never to the writer.

Usage (with seats.py importable, e.g. in the sandbox):
    python -m pytest changes/c_coach_groups/public/test_coach_groups_public.py
"""

import pytest
from seats import NotEnoughSeats, SeatPlanner


@pytest.fixture
def planner():
    p = SeatPlanner()
    p.add_coach("A", 10)  # standard, limit 7
    p.add_coach("C", 10, group="comfort")  # limit 7
    return p


def test_groups_reserve_in_the_asked_group(planner):
    assert planner.reserve("smith", 3, group="comfort") == "C"
    assert planner.get_group("A") == "standard"
    assert planner.get_group("C") == "comfort"
    assert planner.get_groups() == ["standard", "comfort"]


def test_groups_a_full_group_raises_even_if_another_has_room(planner):
    planner.reserve("smith", 7, group="comfort")
    with pytest.raises(NotEnoughSeats):
        planner.reserve("jones", 1, group="comfort")
    assert planner.get_available("A") == 7


def test_groups_filter_the_coach_list(planner):
    planner.add_coach("D", 12, group="comfort")
    assert planner.get_coaches(group="comfort") == ["C", "D"]
    assert planner.get_coaches() == ["A", "C", "D"]
