"""Hidden tests for the c_wait change (wait statistics).
Never shown to the writer or the editor.

Usage (with elevators.py importable, e.g. in the sandbox):
    python -m pytest changes/c_wait/private/test_wait_new.py
"""

import pytest
from elevators import Building, CarOutOfService, ElevatorError

TOP = 6


@pytest.fixture
def building():
    b = Building(TOP)
    b.add_car("east")
    b.add_car("west")
    return b


def test_wait_clock_starts_at_zero_and_counts_every_stop(building):
    assert building.get_clock() == 0
    building.move_car("east", 3)
    building.move_car("east", 2)
    building.move_car("west", 1)
    assert building.get_clock() == 3


def test_wait_failed_moves_do_not_advance_the_clock(building):
    building.move_car("east", 1)
    building.take_out_of_service("west")
    for call, error in [
        (lambda: building.move_car("north", 1), KeyError),
        (lambda: building.move_car("east", 99), ValueError),
        (lambda: building.move_car("west", 2), CarOutOfService),
    ]:
        with pytest.raises(error):
            call()
    assert building.get_clock() == 1


def test_wait_counts_moves_of_every_car(building):
    building.call("ann", 3, 6)
    building.move_car("east", 5)
    building.move_car("west", 1)
    building.move_car("east", 3)
    assert building.get_wait("ann") == 3


def test_wait_starts_when_the_passenger_calls(building):
    building.move_car("east", 1)
    building.move_car("east", 2)
    building.call("ben", 4, 0)
    building.move_car("west", 4)
    assert building.get_clock() == 3
    assert building.get_wait("ben") == 1


def test_wait_is_kept_after_arrival(building):
    building.call("ann", 2, 4)
    building.move_car("east", 1)
    building.move_car("east", 2)
    building.move_car("east", 4)
    building.move_car("east", 0)
    assert building.get_delivered() == ["ann"]
    assert building.get_wait("ann") == 2


def test_wait_of_passengers_who_did_not_fit_keeps_growing(building):
    for name in ["p1", "p2", "p3", "p4", "p5"]:
        building.call(name, 2, 6)
    building.move_car("east", 2)
    building.move_car("west", 3)
    building.move_car("west", 2)
    assert [building.get_wait(n) for n in ["p1", "p2", "p3", "p4"]] == [1, 1, 1, 1]
    assert building.get_wait("p5") == 3


def test_wait_unknown_and_waiting_passengers_are_rejected(building):
    building.call("ann", 3, 5)
    building.move_car("east", 1)
    with pytest.raises(KeyError):
        building.get_wait("nobody")
    with pytest.raises(KeyError):
        building.get_wait(None)
    with pytest.raises(ElevatorError):
        building.get_wait("ann")
    assert building.get_waiting(3) == ["ann"]


def test_wait_longest_is_zero_until_someone_boards(building):
    assert building.get_longest_wait() == 0
    building.call("ann", 3, 5)
    building.move_car("east", 1)
    building.move_car("east", 2)
    assert building.get_longest_wait() == 0


def test_wait_longest_covers_riders_and_arrived_but_not_waiting(building):
    building.call("ann", 1, 2)
    building.call("ben", 4, 6)
    building.call("cy", 5, 6)
    building.move_car("east", 1)  # ann in at clock 1, wait 1
    building.move_car("east", 2)  # ann arrives
    building.move_car("west", 3)
    building.move_car("west", 4)  # ben in at clock 4, wait 4
    assert building.get_longest_wait() == 4
    building.move_car("west", 6)
    assert building.get_longest_wait() == 4  # cy still waiting, ben arrived
    building.move_car("east", 5)  # cy in at clock 6, wait 6
    assert building.get_longest_wait() == 6


def test_wait_totals_are_kept_per_car(building):
    building.call("ann", 1, 3)
    building.call("ben", 1, 4)
    building.call("cy", 2, 5)
    building.move_car("east", 1)  # ann and ben, 1 each
    building.move_car("west", 1)  # nobody is left waiting there
    building.move_car("west", 2)  # cy, 3
    building.move_car("east", 3)
    assert building.get_total_wait("east") == 2
    assert building.get_total_wait("west") == 3
    building.add_car("north")
    assert building.get_total_wait("north") == 0
    with pytest.raises(KeyError):
        building.get_total_wait("south")
