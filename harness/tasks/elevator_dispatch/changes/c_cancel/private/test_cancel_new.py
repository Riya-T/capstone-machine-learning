"""Hidden tests for the c_cancel change (cancelling a call).
Never shown to the writer or the editor.

Usage (with elevators.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/private/test_cancel_new.py
"""

import pytest
from elevators import Building, ElevatorError

TOP = 6
CARS = ["east", "west"]


@pytest.fixture
def building():
    b = Building(TOP)
    for car in CARS:
        b.add_car(car)
    return b


def state(b, cars=CARS, top=TOP):
    return (
        {c: (b.get_car_floor(c), b.get_riders(c)) for c in cars},
        [b.get_waiting(f) for f in range(top + 1)],
        b.get_delivered(),
        b.get_cancelled(),
    )


def test_cancel_list_starts_empty(building):
    assert building.get_cancelled() == []


def test_cancel_keeps_the_order_of_the_others(building):
    for name in ["ann", "ben", "cy", "dee"]:
        building.call(name, 3, 6)
    building.cancel_call("ben")
    assert building.get_waiting(3) == ["ann", "cy", "dee"]
    building.move_car("east", 3)
    assert building.get_riders("east") == ["ann", "cy", "dee"]


def test_cancel_frees_a_seat_for_the_next_in_line(building):
    for name in ["p1", "p2", "p3", "p4", "p5"]:
        building.call(name, 1, 4)
    building.cancel_call("p2")
    building.move_car("east", 1)
    assert building.get_riders("east") == ["p1", "p3", "p4", "p5"]
    assert building.get_waiting(1) == []


@pytest.mark.parametrize("passenger", ["nobody", None, 7])
def test_cancel_ids_without_a_call_raise_key_error(building, passenger):
    building.call("ann", 1, 4)
    before = state(building)
    with pytest.raises(KeyError):
        building.cancel_call(passenger)
    assert state(building) == before


def test_cancel_twice_raises_key_error(building):
    building.call("ann", 1, 4)
    building.cancel_call("ann")
    before = state(building)
    with pytest.raises(KeyError):
        building.cancel_call("ann")
    assert state(building) == before
    assert building.get_cancelled() == ["ann"]


def test_cancel_riders_and_arrived_passengers_cannot_cancel(building):
    building.call("ride", 2, 6)
    building.call("done", 2, 4)
    building.move_car("east", 2)
    building.move_car("east", 4)
    before = state(building)
    for name in ["ride", "done"]:
        with pytest.raises(ElevatorError):
            building.cancel_call(name)
    assert state(building) == before
    building.move_car("east", 6)
    assert building.get_delivered() == ["done", "ride"]


def test_cancel_a_freed_id_joins_the_end_of_its_new_floor(building):
    building.call("ann", 2, 5)
    building.call("ben", 4, 0)
    building.cancel_call("ann")
    building.call("ann", 4, 1)
    assert building.get_waiting(4) == ["ben", "ann"]
    assert building.get_waiting(2) == []
    building.move_car("west", 4)
    building.move_car("west", 1)
    assert building.get_delivered() == ["ann"]


def test_cancel_a_freed_id_is_used_again_by_its_new_call(building):
    building.call("ann", 2, 5)
    building.cancel_call("ann")
    building.call("ann", 2, 3)
    with pytest.raises(ElevatorError):
        building.call("ann", 1, 6)
    building.move_car("east", 2)
    building.move_car("east", 3)
    assert building.get_delivered() == ["ann"]


def test_cancel_is_listed_every_time_oldest_first(building):
    building.call("ann", 1, 2)
    building.call("ben", 3, 2)
    building.cancel_call("ben")
    building.cancel_call("ann")
    building.call("ben", 5, 0)
    building.cancel_call("ben")
    assert building.get_cancelled() == ["ben", "ann", "ben"]
    assert building.get_delivered() == []


def test_cancel_a_cancelled_call_is_never_delivered(building):
    building.call("ann", 1, 3)
    building.call("ben", 1, 3)
    building.cancel_call("ann")
    building.move_car("east", 1)
    building.move_car("east", 3)
    assert building.get_delivered() == ["ben"]
