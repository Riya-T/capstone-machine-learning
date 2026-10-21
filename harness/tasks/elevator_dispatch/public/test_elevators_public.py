"""Public checks for elevators.py.

Usage (with elevators.py importable, e.g. in the sandbox):
    python -m pytest public/test_elevators_public.py
"""

import pytest
from elevators import Building


@pytest.fixture
def building():
    b = Building(6)
    b.add_car("east")
    b.add_car("west")
    return b


def test_a_new_car_is_empty_on_floor_zero(building):
    assert building.get_car_floor("east") == 0
    assert building.get_riders("east") == []


def test_a_caller_waits_until_a_car_stops_on_their_floor(building):
    building.call("ann", 3, 5)
    assert building.get_waiting(3) == ["ann"]
    building.move_car("east", 3)
    assert building.get_car_floor("east") == 3
    assert building.get_riders("east") == ["ann"]
    assert building.get_waiting(3) == []


def test_riders_get_out_at_their_destination(building):
    building.call("ann", 2, 5)
    building.call("ben", 2, 4)
    building.move_car("east", 2)
    building.move_car("east", 4)
    assert building.get_riders("east") == ["ann"]
    assert building.get_delivered() == ["ben"]


def test_a_car_takes_at_most_four_riders(building):
    for name in ["p1", "p2", "p3", "p4", "p5"]:
        building.call(name, 1, 6)
    building.move_car("east", 1)
    assert building.get_riders("east") == ["p1", "p2", "p3", "p4"]
    assert building.get_waiting(1) == ["p5"]


def test_a_stop_on_the_current_floor_picks_people_up(building):
    building.call("ann", 0, 3)
    assert building.get_riders("east") == []
    building.move_car("east", 0)
    assert building.get_riders("east") == ["ann"]


def test_an_unknown_car_raises_key_error(building):
    with pytest.raises(KeyError):
        building.get_car_floor("north")
