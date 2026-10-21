"""Hidden tests for the initial elevator_dispatch spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with elevators.py importable, e.g. in the sandbox):
    python -m pytest private/test_elevators_initial.py
"""

import pytest
from elevators import Building, ElevatorError

TOP = 6
CARS = ["east", "west"]
BAD_FLOORS = [-1, TOP + 1, 1.5, "2", None]


@pytest.fixture
def building():
    b = Building(TOP)
    for car in CARS:
        b.add_car(car)
    return b


def state(b, cars=CARS, top=TOP):
    """Every car, waiting list and arrival, to check that a failed call changed nothing."""
    return (
        {c: (b.get_car_floor(c), b.get_riders(c)) for c in cars},
        [b.get_waiting(f) for f in range(top + 1)],
        b.get_delivered(),
    )


# --- floors and cars --------------------------------------------------------


@pytest.mark.parametrize("top", [0, -3, 2.5, "6", None])
def test_top_floor_must_be_an_int_of_at_least_one(top):
    with pytest.raises(ValueError):
        Building(top)


def test_a_building_with_two_floors_works():
    b = Building(1)
    b.add_car("solo")
    b.call("ann", 1, 0)
    b.move_car("solo", 1)
    b.move_car("solo", 0)
    assert b.get_delivered() == ["ann"]
    with pytest.raises(ValueError):
        b.move_car("solo", 2)


def test_new_cars_start_empty_on_floor_zero(building):
    for car in CARS:
        assert building.get_car_floor(car) == 0
        assert building.get_riders(car) == []
    assert building.get_delivered() == []


def test_an_empty_car_id_is_rejected():
    b = Building(TOP)
    with pytest.raises(ValueError):
        b.add_car("")


def test_adding_an_existing_car_is_rejected(building):
    building.call("ann", 2, 5)
    building.move_car("east", 2)
    before = state(building)
    with pytest.raises(ElevatorError):
        building.add_car("east")
    assert state(building) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda b: b.move_car("north", 1),
        lambda b: b.get_car_floor("north"),
        lambda b: b.get_riders("north"),
        lambda b: b.get_car_floor(None),
        lambda b: b.get_riders(1),
        lambda b: b.move_car(None, 1),
    ],
)
def test_cars_that_do_not_exist_raise_key_error(building, call):
    building.call("ann", 1, 3)
    before = state(building)
    with pytest.raises(KeyError):
        call(building)
    assert state(building) == before


@pytest.mark.parametrize("floor", BAD_FLOORS)
@pytest.mark.parametrize(
    "call",
    [
        lambda b, f: b.call("zed", f, 3),
        lambda b, f: b.call("zed", 3, f),
        lambda b, f: b.move_car("east", f),
        lambda b, f: b.get_waiting(f),
    ],
    ids=["call_floor", "call_destination", "move_car", "get_waiting"],
)
def test_invalid_floors_are_rejected(building, call, floor):
    building.call("ann", 1, 3)
    before = state(building)
    with pytest.raises(ValueError):
        call(building, floor)
    assert state(building) == before


def test_an_unknown_car_is_reported_before_a_bad_floor(building):
    with pytest.raises(KeyError):
        building.move_car("north", 99)


def test_moving_changes_only_that_cars_floor(building):
    building.move_car("east", 5)
    building.move_car("east", 2)
    assert building.get_car_floor("east") == 2
    assert building.get_car_floor("west") == 0


# --- calls ------------------------------------------------------------------


def test_an_empty_passenger_id_is_rejected(building):
    before = state(building)
    with pytest.raises(ValueError):
        building.call("", 1, 2)
    assert state(building) == before


def test_a_call_to_the_same_floor_is_rejected(building):
    before = state(building)
    with pytest.raises(ValueError):
        building.call("ann", 3, 3)
    assert state(building) == before


def test_waiting_passengers_are_listed_in_call_order(building):
    building.call("cy", 2, 0)
    building.call("ann", 2, 5)
    building.call("bo", 4, 1)
    building.call("dee", 2, 6)
    assert building.get_waiting(2) == ["cy", "ann", "dee"]
    assert building.get_waiting(4) == ["bo"]
    assert building.get_waiting(0) == []


def test_a_call_puts_nobody_in_a_car(building):
    building.call("ann", 0, 4)
    assert building.get_riders("east") == []
    assert building.get_riders("west") == []
    assert building.get_waiting(0) == ["ann"]


def test_a_passenger_id_is_used_up_once_called(building):
    building.call("wait", 1, 3)
    building.call("ride", 2, 5)
    building.call("done", 2, 4)
    building.move_car("east", 2)
    building.move_car("east", 4)
    assert building.get_delivered() == ["done"]
    before = state(building)
    for name in ["wait", "ride", "done"]:
        with pytest.raises(ElevatorError):
            building.call(name, 6, 0)
    assert state(building) == before


def test_value_errors_come_before_a_used_id(building):
    building.call("ann", 1, 3)
    with pytest.raises(ValueError):
        building.call("ann", 2, 2)
    with pytest.raises(ValueError):
        building.call("ann", 99, 1)
    with pytest.raises(ValueError):
        building.call("ann", 1, -1)


# --- moving and boarding ----------------------------------------------------


def test_a_car_only_picks_up_on_the_floor_it_stops_at(building):
    building.call("ann", 3, 6)
    building.call("ben", 4, 6)
    building.move_car("east", 4)
    assert building.get_riders("east") == ["ben"]
    assert building.get_waiting(3) == ["ann"]


def test_only_four_get_in_and_the_rest_keep_their_order(building):
    names = ["p1", "p2", "p3", "p4", "p5", "p6"]
    for name in names:
        building.call(name, 2, 5)
    building.move_car("east", 2)
    assert building.get_riders("east") == names[:4]
    assert building.get_waiting(2) == ["p5", "p6"]
    building.move_car("west", 2)
    assert building.get_riders("west") == ["p5", "p6"]
    assert building.get_waiting(2) == []


def test_a_full_car_picks_up_nobody(building):
    for name in ["p1", "p2", "p3", "p4"]:
        building.call(name, 0, 6)
    building.move_car("east", 0)
    building.call("late", 3, 5)
    building.move_car("east", 3)
    assert building.get_riders("east") == ["p1", "p2", "p3", "p4"]
    assert building.get_waiting(3) == ["late"]


def test_riders_get_out_before_new_passengers_get_in(building):
    for name, dest in [("p1", 6), ("p2", 3), ("p3", 6), ("p4", 6)]:
        building.call(name, 0, dest)
    building.move_car("east", 0)
    building.call("q1", 3, 5)
    building.call("q2", 3, 5)
    building.move_car("east", 3)
    assert building.get_riders("east") == ["p1", "p3", "p4", "q1"]
    assert building.get_waiting(3) == ["q2"]
    assert building.get_delivered() == ["p2"]


def test_riders_for_other_floors_stay_aboard(building):
    building.call("ann", 1, 5)
    building.call("ben", 1, 3)
    building.move_car("east", 1)
    building.move_car("east", 2)
    assert building.get_riders("east") == ["ann", "ben"]
    assert building.get_delivered() == []


def test_riders_leaving_together_are_listed_in_boarding_order(building):
    building.call("ann", 1, 4)
    building.call("ben", 1, 6)
    building.move_car("east", 1)
    building.call("cy", 2, 4)
    building.move_car("east", 2)
    building.move_car("east", 4)
    assert building.get_delivered() == ["ann", "cy"]
    assert building.get_riders("east") == ["ben"]


def test_arrivals_from_all_cars_are_listed_oldest_first(building):
    building.call("ann", 5, 1)
    building.call("ben", 2, 3)
    building.move_car("east", 5)
    building.move_car("west", 2)
    building.move_car("west", 3)
    building.move_car("east", 1)
    assert building.get_delivered() == ["ben", "ann"]
    assert building.get_riders("east") == []
    assert building.get_riders("west") == []


def test_a_passenger_rides_only_in_the_car_that_stopped(building):
    building.move_car("west", 2)
    building.call("ann", 2, 4)
    building.move_car("east", 2)
    assert building.get_riders("east") == ["ann"]
    assert building.get_riders("west") == []
    building.move_car("west", 4)
    assert building.get_riders("east") == ["ann"]
    assert building.get_delivered() == []


def test_buildings_do_not_share_cars_or_passengers():
    first, second = Building(3), Building(3)
    first.add_car("east")
    first.call("ann", 1, 2)
    second.add_car("east")
    second.call("ann", 1, 2)
    assert second.get_waiting(1) == ["ann"]
    first.move_car("east", 1)
    assert second.get_waiting(1) == ["ann"]
    assert second.get_riders("east") == []
