"""Hidden tests for the initial seat_reservation spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with seats.py importable, e.g. in the sandbox):
    python -m pytest private/test_seats_initial.py
"""

import pytest
from seats import NotEnoughSeats, ReservationError, SeatPlanner

BAD_COUNTS = [0, -3, 2.5, "4", None]


@pytest.fixture
def planner():
    p = SeatPlanner()
    p.add_coach("A", 10)  # limit 7
    p.add_coach("B", 20)  # limit 14
    return p


def state(p, bookings=()):
    """Every coach and the given bookings, to check that a failed call changed
    nothing."""
    coaches = {c: (p.get_reserved(c), p.get_available(c)) for c in p.get_coaches()}
    return coaches, {b: p.get_booking(b) for b in bookings}


# --- coaches ----------------------------------------------------------------


def test_coaches_are_listed_in_the_order_added():
    p = SeatPlanner()
    for coach in ["C", "A", "B"]:
        p.add_coach(coach, 10)
    assert p.get_coaches() == ["C", "A", "B"]


def test_a_new_coach_is_empty(planner):
    assert planner.get_reserved("A") == 0
    assert planner.get_available("A") == 7
    assert planner.get_available("B") == 14


@pytest.mark.parametrize("seats, limit", [(10, 7), (15, 10), (1, 0), (3, 2), (100, 70), (9, 6)])
def test_the_limit_is_seventy_percent_rounded_down(seats, limit):
    p = SeatPlanner()
    p.add_coach("X", seats)
    assert p.get_available("X") == limit


@pytest.mark.parametrize("seats", BAD_COUNTS)
def test_invalid_seat_counts_are_rejected(seats):
    p = SeatPlanner()
    with pytest.raises(ValueError):
        p.add_coach("X", seats)
    assert p.get_coaches() == []


def test_an_empty_coach_id_is_rejected():
    p = SeatPlanner()
    with pytest.raises(ValueError):
        p.add_coach("", 10)
    assert p.get_coaches() == []


def test_adding_a_coach_twice_is_rejected(planner):
    planner.reserve("smith", 2)
    before = state(planner, ["smith"])
    with pytest.raises(ReservationError):
        planner.add_coach("A", 30)
    assert state(planner, ["smith"]) == before
    assert planner.get_coaches() == ["A", "B"]


def test_a_bad_seat_count_is_reported_before_a_repeated_id(planner):
    with pytest.raises(ValueError):
        planner.add_coach("A", 0)


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.get_reserved("Z"),
        lambda p: p.get_available("Z"),
        lambda p: p.get_booking("nobody"),
        lambda p: p.move("nobody", "B"),
        lambda p: p.move("smith", "Z"),
        lambda p: p.get_reserved(None),
        lambda p: p.get_available(1),
        lambda p: p.get_booking(None),
    ],
)
def test_unknown_ids_raise_key_error_and_change_nothing(planner, call):
    planner.reserve("smith", 2)
    before = state(planner, ["smith"])
    with pytest.raises(KeyError):
        call(planner)
    assert state(planner, ["smith"]) == before


# --- reserving --------------------------------------------------------------


def test_groups_fill_a_coach_up_to_its_limit(planner):
    assert planner.reserve("smith", 3) == "A"
    assert planner.reserve("jones", 4) == "A"
    assert planner.get_booking("jones") == ("A", [4, 5, 6, 7])
    assert planner.get_reserved("A") == 7
    assert planner.get_available("A") == 0


def test_a_group_that_does_not_fit_goes_to_the_next_coach(planner):
    planner.reserve("smith", 5)
    assert planner.reserve("jones", 3) == "B"
    assert planner.get_booking("jones") == ("B", [1, 2, 3])
    # A still has room for two, so a pair goes back into A.
    assert planner.reserve("brown", 2) == "A"
    assert planner.get_booking("brown") == ("A", [6, 7])


def test_a_group_bigger_than_the_first_limit_skips_that_coach(planner):
    assert planner.reserve("school", 8) == "B"
    assert planner.get_reserved("A") == 0


def test_a_group_is_never_split_between_coaches(planner):
    planner.reserve("smith", 5)  # A: 2 left
    planner.reserve("jones", 12)  # B: 2 left
    before = state(planner, ["smith", "jones"])
    with pytest.raises(NotEnoughSeats):
        planner.reserve("brown", 3)
    assert state(planner, ["smith", "jones"]) == before


def test_no_coaches_means_no_room():
    p = SeatPlanner()
    with pytest.raises(NotEnoughSeats):
        p.reserve("smith", 1)


@pytest.mark.parametrize("size", BAD_COUNTS)
def test_invalid_sizes_are_rejected(planner, size):
    before = state(planner)
    with pytest.raises(ValueError):
        planner.reserve("smith", size)
    assert state(planner) == before
    with pytest.raises(KeyError):
        planner.get_booking("smith")


def test_an_empty_booking_id_is_rejected(planner):
    with pytest.raises(ValueError):
        planner.reserve("", 2)
    assert planner.get_reserved("A") == 0


def test_booking_an_id_twice_is_rejected(planner):
    planner.reserve("smith", 2)
    before = state(planner, ["smith"])
    with pytest.raises(ReservationError):
        planner.reserve("smith", 1)
    assert state(planner, ["smith"]) == before


def test_reserve_errors_come_in_order(planner):
    assert issubclass(NotEnoughSeats, ReservationError)
    planner.reserve("smith", 2)
    with pytest.raises(ValueError):
        planner.reserve("smith", 0)  # bad size before a repeated id
    with pytest.raises(ReservationError) as info:
        planner.reserve("smith", 50)  # repeated id before no room
    assert not isinstance(info.value, NotEnoughSeats)


# --- moving -----------------------------------------------------------------


def test_moving_frees_the_old_seats(planner):
    planner.reserve("smith", 3)
    planner.move("smith", "B")
    assert planner.get_booking("smith") == ("B", [1, 2, 3])
    assert planner.get_reserved("A") == 0
    assert planner.get_available("A") == 7
    assert planner.get_reserved("B") == 3


def test_a_move_takes_the_lowest_free_seats_of_the_new_coach(planner):
    planner.reserve("smith", 2)  # A 1-2
    planner.reserve("jones", 3)  # A 3-5
    planner.reserve("brown", 10)  # B 1-10
    planner.move("smith", "B")  # B 11-12, A 1-2 free
    assert planner.get_booking("smith") == ("B", [11, 12])
    planner.move("smith", "A")  # back into the gap at the front of A
    assert planner.get_booking("smith") == ("A", [1, 2])
    assert planner.get_reserved("A") == 5
    assert planner.get_reserved("B") == 10


def test_a_move_past_the_limit_raises_and_changes_nothing(planner):
    planner.reserve("smith", 5)  # A
    planner.reserve("jones", 12)  # B
    before = state(planner, ["smith", "jones"])
    with pytest.raises(NotEnoughSeats):
        planner.move("smith", "B")
    assert state(planner, ["smith", "jones"]) == before


def test_a_move_can_fill_a_coach_exactly_to_its_limit(planner):
    planner.reserve("smith", 5)  # A
    planner.reserve("jones", 9)  # B
    planner.move("smith", "B")
    assert planner.get_booking("smith") == ("B", [10, 11, 12, 13, 14])
    assert planner.get_available("B") == 0


def test_moving_to_the_same_coach_is_rejected(planner):
    planner.reserve("smith", 2)
    before = state(planner, ["smith"])
    with pytest.raises(ValueError):
        planner.move("smith", "A")
    assert state(planner, ["smith"]) == before


def test_move_errors_come_in_order(planner):
    planner.reserve("smith", 7)  # fills A
    planner.reserve("jones", 14)  # fills B
    with pytest.raises(KeyError):
        planner.move("nobody", "Z")
    with pytest.raises(KeyError):
        planner.move("smith", "Z")
    with pytest.raises(ValueError):
        planner.move("smith", "A")  # same coach before no room
    with pytest.raises(NotEnoughSeats):
        planner.move("smith", "B")


def test_later_bookings_fill_the_gaps_left_by_moves(planner):
    planner.reserve("smith", 2)  # A 1-2
    planner.reserve("jones", 2)  # A 3-4
    planner.reserve("brown", 2)  # A 5-6
    planner.move("jones", "B")
    assert planner.reserve("green", 1) == "A"
    assert planner.get_booking("green") == ("A", [3])
    assert planner.reserve("white", 2) == "A"
    assert planner.get_booking("white") == ("A", [4, 7])


def test_planners_do_not_share_coaches():
    first, second = SeatPlanner(), SeatPlanner()
    first.add_coach("A", 10)
    first.reserve("smith", 2)
    assert second.get_coaches() == []
    second.add_coach("A", 10)
    assert second.get_reserved("A") == 0
