"""Hidden tests for the c_coach_groups change (coach groups). Never shown to
the writer or the editor.

Usage (with seats.py importable, e.g. in the sandbox):
    python -m pytest changes/c_coach_groups/private/test_coach_groups_new.py
"""

import pytest
from seats import NotEnoughSeats, ReservationError, SeatPlanner


@pytest.fixture
def planner():
    p = SeatPlanner()
    p.add_coach("A", 10)  # standard, limit 7
    p.add_coach("C1", 10, group="comfort")  # limit 7
    p.add_coach("B", 20)  # standard, limit 14
    p.add_coach("C2", 20, group="comfort")  # limit 14
    return p


def state(p, bookings=()):
    coaches = {c: (p.get_reserved(c), p.get_available(c), p.get_group(c)) for c in p.get_coaches()}
    return coaches, {b: p.get_booking(b) for b in bookings}


def test_groups_default_to_standard():
    p = SeatPlanner()
    p.add_coach("A", 10)
    p.add_coach("B", 10)
    assert p.get_group("A") == "standard"
    assert p.get_groups() == ["standard"]
    assert p.get_coaches(group="standard") == ["A", "B"]


def test_groups_are_listed_once_in_order_of_their_first_coach():
    p = SeatPlanner()
    p.add_coach("x", 10, group="comfort")
    p.add_coach("y", 10)
    p.add_coach("z", 10, group="comfort")
    p.add_coach("w", 10, group="sleeper")
    assert p.get_groups() == ["comfort", "standard", "sleeper"]


def test_groups_none_means_every_coach(planner):
    assert planner.get_coaches(group=None) == ["A", "C1", "B", "C2"]
    assert planner.get_coaches(group="standard") == ["A", "B"]
    assert planner.get_coaches(group="comfort") == ["C1", "C2"]


def test_groups_unknown_group_raises_key_error(planner):
    before = state(planner)
    with pytest.raises(KeyError):
        planner.get_coaches(group="sleeper")
    with pytest.raises(KeyError):
        planner.get_group_available("sleeper")
    with pytest.raises(KeyError):
        planner.reserve("smith", 2, group="sleeper")
    with pytest.raises(KeyError):
        planner.get_group("Z")
    assert state(planner) == before


def test_groups_reserve_without_a_group_uses_any_coach(planner):
    assert planner.reserve("smith", 7) == "A"
    assert planner.reserve("jones", 7) == "C1"
    assert planner.reserve("brown", 7) == "B"


def test_groups_reserve_uses_the_first_coach_of_the_group_that_fits(planner):
    assert planner.reserve("smith", 5, group="comfort") == "C1"
    assert planner.reserve("jones", 4, group="comfort") == "C2"
    assert planner.get_booking("jones") == ("C2", [1, 2, 3, 4])
    assert planner.reserve("brown", 2, group="comfort") == "C1"
    assert planner.reserve("green", 8, group="standard") == "B"
    assert planner.get_reserved("A") == 0


def test_groups_a_full_group_changes_nothing(planner):
    planner.reserve("smith", 7, group="comfort")
    planner.reserve("jones", 14, group="comfort")
    before = state(planner, ["smith", "jones"])
    with pytest.raises(NotEnoughSeats):
        planner.reserve("brown", 1, group="comfort")
    assert state(planner, ["smith", "jones"]) == before


@pytest.mark.parametrize("group", ["", 5, None])
def test_groups_bad_group_names_are_rejected(planner, group):
    before = state(planner)
    with pytest.raises(ValueError):
        planner.add_coach("D", 10, group=group)
    assert state(planner) == before


def test_groups_reserve_errors_come_in_order(planner):
    planner.reserve("smith", 2)
    with pytest.raises(ValueError):
        planner.reserve("jones", 0, group="sleeper")  # bad size before unknown group
    with pytest.raises(KeyError):
        planner.reserve("smith", 2, group="sleeper")  # unknown group before repeated id
    with pytest.raises(ReservationError) as info:
        planner.reserve("smith", 50, group="comfort")
    assert not isinstance(info.value, NotEnoughSeats)


def test_groups_available_seats_are_summed(planner):
    assert planner.get_group_available("comfort") == 21
    assert planner.get_group_available("standard") == 21
    planner.reserve("smith", 5, group="comfort")
    planner.reserve("jones", 3)
    assert planner.get_group_available("comfort") == 16
    assert planner.get_group_available("standard") == 18


def test_groups_moves_may_cross_groups(planner):
    planner.reserve("smith", 3)
    planner.move("smith", "C2")
    assert planner.get_booking("smith") == ("C2", [1, 2, 3])
    assert planner.get_group_available("comfort") == 18
    assert planner.get_group_available("standard") == 21
