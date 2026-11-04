"""Hidden tests for the c_cancel change (cancellations). Never shown to the
writer or the editor.

Usage (with seats.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/private/test_cancel_new.py
"""

import pytest
from seats import NotEnoughSeats, SeatPlanner


@pytest.fixture
def planner():
    p = SeatPlanner()
    p.add_coach("A", 10)  # limit 7
    p.add_coach("B", 20)  # limit 14
    return p


def state(p, bookings=()):
    coaches = {c: (p.get_reserved(c), p.get_available(c)) for c in p.get_coaches()}
    return coaches, {b: tuple(p.get_booking(b)) for b in bookings}, p.get_cancelled()


def test_cancel_list_starts_empty(planner):
    assert planner.get_cancelled() == []


def test_cancel_of_an_unknown_booking_raises_key_error(planner):
    planner.reserve("smith", 2)
    before = state(planner, ["smith"])
    for bad in ["nobody", None, 1]:
        with pytest.raises(KeyError):
            planner.cancel(bad)
    with pytest.raises(KeyError):
        planner.cancel("nobody", 1)
    assert state(planner, ["smith"]) == before


def test_cancel_twice_raises_key_error(planner):
    planner.reserve("smith", 2)
    planner.cancel("smith")
    with pytest.raises(KeyError):
        planner.cancel("smith")
    with pytest.raises(KeyError):
        planner.move("smith", "B")
    assert planner.get_cancelled() == ["smith"]


def test_cancel_lets_an_id_be_booked_again(planner):
    planner.reserve("smith", 2)
    planner.cancel("smith")
    assert planner.reserve("smith", 5) == "A"
    assert planner.get_booking("smith") == ("A", 5)
    planner.cancel("smith")
    assert planner.get_cancelled() == ["smith", "smith"]


def test_cancel_list_keeps_the_order_of_cancelling(planner):
    for booking in ["smith", "jones", "brown"]:
        planner.reserve(booking, 1)
    planner.cancel("jones")
    planner.cancel("brown", 1)
    planner.cancel("smith")
    assert planner.get_cancelled() == ["jones", "brown", "smith"]


def test_cancel_of_every_passenger_cancels_the_booking(planner):
    planner.reserve("smith", 4)
    planner.cancel("smith", 4)
    assert planner.get_cancelled() == ["smith"]
    assert planner.get_reserved("A") == 0
    with pytest.raises(KeyError):
        planner.get_booking("smith")


def test_cancel_in_part_more_than_once(planner):
    planner.reserve("smith", 5)
    planner.cancel("smith", 2)
    planner.cancel("smith", 1)
    assert planner.get_booking("smith") == ("A", 2)
    assert planner.get_available("A") == 5
    planner.cancel("smith", 2)
    assert planner.get_cancelled() == ["smith"]


@pytest.mark.parametrize("count", [0, -1, 5])
def test_cancel_with_a_bad_count_is_rejected(planner, count):
    planner.reserve("smith", 4)
    before = state(planner, ["smith"])
    with pytest.raises(ValueError):
        planner.cancel("smith", count)
    assert state(planner, ["smith"]) == before


def test_cancel_in_part_frees_room_for_later_bookings(planner):
    planner.reserve("smith", 4)
    planner.reserve("jones", 2)
    planner.cancel("smith", 2)
    assert planner.get_booking("smith") == ("A", 2)
    assert planner.get_booking("jones") == ("A", 2)
    assert planner.reserve("brown", 3) == "A"
    assert planner.get_available("A") == 0


def test_cancel_in_part_then_move_takes_only_the_remaining_passengers(planner):
    planner.reserve("smith", 4)
    planner.cancel("smith", 1)
    planner.move("smith", "B")
    assert planner.get_booking("smith") == ("B", 3)
    assert planner.get_reserved("A") == 0
    assert planner.get_reserved("B") == 3


def test_cancel_after_a_move_frees_room_in_the_new_coach(planner):
    planner.reserve("smith", 3)
    planner.move("smith", "B")
    planner.cancel("smith")
    assert planner.get_reserved("A") == 0
    assert planner.get_reserved("B") == 0
    assert planner.get_available("B") == 14


def test_cancel_makes_room_for_a_group_that_did_not_fit(planner):
    planner.reserve("smith", 5)  # A: 2 left
    planner.reserve("jones", 12)  # B: 2 left
    with pytest.raises(NotEnoughSeats):
        planner.reserve("brown", 3)
    planner.cancel("smith", 2)
    assert planner.reserve("brown", 3) == "A"
    assert planner.get_available("A") == 1
