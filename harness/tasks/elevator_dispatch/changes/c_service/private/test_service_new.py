"""Hidden tests for the c_service change (cars out of service).
Never shown to the writer or the editor.

Usage (with elevators.py importable, e.g. in the sandbox):
    python -m pytest changes/c_service/private/test_service_new.py
"""

import pytest
from elevators import Building, CarOutOfService, ElevatorError

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
        {c: (b.get_car_floor(c), b.get_riders(c), b.is_in_service(c)) for c in cars},
        [b.get_waiting(f) for f in range(top + 1)],
        b.get_delivered(),
    )


def test_service_new_cars_are_in_service(building):
    assert building.is_in_service("east")
    assert building.is_in_service("west")
    assert building.get_cars_in_service() == ["east", "west"]


def test_service_repeating_a_change_does_nothing(building):
    building.take_out_of_service("east")
    building.take_out_of_service("east")
    assert not building.is_in_service("east")
    building.return_to_service("east")
    building.return_to_service("east")
    assert building.is_in_service("east")
    building.return_to_service("west")
    assert building.is_in_service("west")


@pytest.mark.parametrize("method", ["take_out_of_service", "return_to_service", "is_in_service"])
def test_service_unknown_cars_raise_key_error(building, method):
    with pytest.raises(KeyError):
        getattr(building, method)("north")
    with pytest.raises(KeyError):
        getattr(building, method)(None)


def test_service_a_car_with_riders_cannot_be_taken_out(building):
    building.call("ann", 2, 5)
    building.move_car("east", 2)
    before = state(building)
    with pytest.raises(ElevatorError):
        building.take_out_of_service("east")
    assert state(building) == before
    assert building.is_in_service("east")


def test_service_a_car_can_be_taken_out_once_everyone_arrived(building):
    building.call("ann", 2, 5)
    building.move_car("east", 2)
    building.move_car("east", 5)
    building.take_out_of_service("east")
    assert not building.is_in_service("east")
    assert building.get_car_floor("east") == 5


def test_service_moving_a_car_out_of_service_changes_nothing(building):
    building.call("ann", 3, 1)
    building.move_car("east", 2)
    building.take_out_of_service("east")
    before = state(building)
    with pytest.raises(CarOutOfService):
        building.move_car("east", 3)
    with pytest.raises(CarOutOfService):
        building.move_car("east", 2)  # not even on its own floor
    assert state(building) == before
    assert building.get_waiting(3) == ["ann"]


def test_service_unknown_car_and_bad_floor_come_first(building):
    building.take_out_of_service("east")
    with pytest.raises(KeyError):
        building.move_car("north", 2)
    with pytest.raises(ValueError):
        building.move_car("east", 99)
    with pytest.raises(ValueError):
        building.move_car("east", -1)


def test_service_car_out_of_service_is_an_elevator_error():
    assert issubclass(CarOutOfService, ElevatorError)


def test_service_cars_in_service_keep_the_order_they_were_added():
    b = Building(TOP)
    for car in ["c", "a", "b"]:
        b.add_car(car)
    b.take_out_of_service("c")
    b.take_out_of_service("a")
    assert b.get_cars_in_service() == ["b"]
    b.return_to_service("a")
    b.return_to_service("c")
    assert b.get_cars_in_service() == ["c", "a", "b"]


def test_service_a_car_out_of_service_can_still_be_inspected(building):
    building.move_car("west", 4)
    building.take_out_of_service("west")
    assert building.get_car_floor("west") == 4
    assert building.get_riders("west") == []
    building.set_capacity("west", 8)
    assert building.get_capacity("west") == 8


def test_service_other_cars_keep_working(building):
    building.take_out_of_service("east")
    building.call("ann", 2, 4)
    building.move_car("west", 2)
    building.move_car("west", 4)
    assert building.get_delivered() == ["ann"]


def test_service_a_returned_car_picks_people_up_again(building):
    building.take_out_of_service("east")
    building.call("ann", 0, 3)
    building.return_to_service("east")
    building.move_car("east", 0)
    assert building.get_riders("east") == ["ann"]
