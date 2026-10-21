"""Hidden tests for the c_capacity change (adjustable car capacities).
Never shown to the writer or the editor.

Usage (with elevators.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from elevators import Building, ElevatorError

TOP = 6
CARS = ["east", "freight"]
BAD_CAPACITIES = [0, -2, 2.5, "3", True]


@pytest.fixture
def building():
    b = Building(TOP)
    b.add_car("east")
    b.add_car("freight", capacity=6)
    return b


def state(b, cars=CARS, top=TOP):
    return (
        {c: (b.get_car_floor(c), b.get_riders(c), b.get_capacity(c)) for c in cars},
        [b.get_waiting(f) for f in range(top + 1)],
        b.get_delivered(),
    )


def board(b, car, names, floor=1, destination=5):
    for name in names:
        b.call(name, floor, destination)
    b.move_car(car, floor)


def test_capacity_defaults_to_four_and_the_building_value():
    plain = Building(TOP)
    plain.add_car("east")
    assert plain.get_capacity("east") == 4
    small = Building(TOP, capacity=3)
    small.add_car("east")
    small.add_car("big", capacity=5)
    small.add_car("auto", capacity=None)
    assert [small.get_capacity(c) for c in ["east", "big", "auto"]] == [3, 5, 3]


def test_capacity_boarding_uses_each_cars_own_capacity(building):
    names = ["p1", "p2", "p3", "p4", "p5", "p6", "p7"]
    board(building, "freight", names)
    assert building.get_riders("freight") == names[:6]
    assert building.get_waiting(1) == ["p7"]
    building.move_car("east", 1)
    assert building.get_riders("east") == ["p7"]


def test_capacity_one_takes_a_single_rider():
    b = Building(TOP, capacity=1)
    b.add_car("tiny")
    board(b, "tiny", ["ann", "ben"])
    assert b.get_riders("tiny") == ["ann"]
    b.move_car("tiny", 5)
    b.move_car("tiny", 1)
    assert b.get_riders("tiny") == ["ben"]
    assert b.get_delivered() == ["ann"]


@pytest.mark.parametrize("capacity", BAD_CAPACITIES + [None])
def test_capacity_invalid_building_capacities_are_rejected(capacity):
    with pytest.raises(ValueError):
        Building(TOP, capacity=capacity)


@pytest.mark.parametrize("capacity", BAD_CAPACITIES)
def test_capacity_invalid_car_capacities_add_no_car(building, capacity):
    before = state(building)
    with pytest.raises(ValueError):
        building.add_car("west", capacity=capacity)
    with pytest.raises(KeyError):
        building.get_capacity("west")
    assert state(building) == before


def test_capacity_a_bad_capacity_is_reported_before_an_existing_car(building):
    with pytest.raises(ValueError):
        building.add_car("east", capacity=0)
    assert building.get_capacity("east") == 4


def test_capacity_unknown_cars_raise_key_error(building):
    with pytest.raises(KeyError):
        building.get_capacity("north")
    with pytest.raises(KeyError):
        building.set_capacity("north", 2)
    with pytest.raises(KeyError):
        building.set_capacity("north", 0)
    with pytest.raises(KeyError):
        building.get_capacity(None)


def test_capacity_can_be_replaced(building):
    building.set_capacity("east", 2)
    assert building.get_capacity("east") == 2
    board(building, "east", ["ann", "ben", "cy"])
    assert building.get_riders("east") == ["ann", "ben"]
    assert building.get_capacity("freight") == 6


@pytest.mark.parametrize("capacity", BAD_CAPACITIES)
def test_capacity_invalid_values_are_rejected_when_setting(building, capacity):
    before = state(building)
    with pytest.raises(ValueError):
        building.set_capacity("east", capacity)
    assert state(building) == before


def test_capacity_below_the_current_riders_is_rejected(building):
    board(building, "east", ["ann", "ben", "cy"])
    before = state(building)
    with pytest.raises(ElevatorError):
        building.set_capacity("east", 2)
    assert state(building) == before
    building.set_capacity("east", 3)  # exactly the riders aboard
    assert building.get_capacity("east") == 3


def test_capacity_a_bad_value_is_reported_before_the_rider_check(building):
    board(building, "east", ["ann", "ben"])
    with pytest.raises(ValueError):
        building.set_capacity("east", 0)


def test_capacity_raised_capacity_is_used_at_the_next_stop(building):
    building.set_capacity("east", 1)
    building.call("ann", 0, 4)
    building.call("ben", 0, 4)
    building.move_car("east", 0)
    assert building.get_riders("east") == ["ann"]
    building.set_capacity("east", 3)
    assert building.get_riders("east") == ["ann"]
    assert building.get_waiting(0) == ["ben"]
    building.move_car("east", 0)
    assert building.get_riders("east") == ["ann", "ben"]
