"""Hidden tests for the initial race_telemetry spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest private/test_telemetry_initial.py
"""

import pytest
from telemetry import RaceTelemetry, TelemetryError

CARS = ["red", "blue", "green"]
BAD_NUMBERS = [0, -5]


@pytest.fixture
def tel():
    t = RaceTelemetry(2)
    for car in CARS:
        t.add_car(car)
    return t


def results(t):
    return [tuple(pair) for pair in t.get_results()]


def state(t):
    """Every car, lap time and result, to check that a failed call changed
    nothing."""
    cars = t.get_cars()
    return cars, {c: t.get_lap_times(c) for c in cars}, results(t)


def finish(t, car, *laps):
    for lap in laps:
        t.record_lap(car, lap)


# --- the race and its cars --------------------------------------------------


def test_cars_are_listed_in_the_order_they_were_added():
    t = RaceTelemetry(3)
    for car in ["green", "red", "blue"]:
        t.add_car(car)
    assert t.get_cars() == ["green", "red", "blue"]


def test_an_empty_car_id_is_rejected():
    t = RaceTelemetry(3)
    with pytest.raises(ValueError):
        t.add_car("")
    assert t.get_cars() == []


def test_entering_a_car_twice_is_rejected(tel):
    finish(tel, "red", 90000)
    before = state(tel)
    with pytest.raises(TelemetryError):
        tel.add_car("red")
    assert state(tel) == before


@pytest.mark.parametrize("laps", BAD_NUMBERS)
def test_invalid_lap_counts_are_rejected(laps):
    with pytest.raises(ValueError):
        RaceTelemetry(laps)


@pytest.mark.parametrize(
    "call",
    [
        lambda t: t.record_lap("pink", 80000),
        lambda t: t.get_lap_times("pink"),
        lambda t: t.record_lap(None, 80000),
        lambda t: t.get_lap_times(None),
        lambda t: t.record_lap(1, 80000),
        lambda t: t.get_lap_times(1),
    ],
)
def test_unknown_cars_raise_key_error(tel, call):
    finish(tel, "red", 80000)
    before = state(tel)
    with pytest.raises(KeyError):
        call(tel)
    assert state(tel) == before


# --- laps -------------------------------------------------------------------


def test_lap_times_are_kept_per_car(tel):
    finish(tel, "red", 81000, 80000)
    finish(tel, "blue", 83000)
    assert tel.get_lap_times("red") == [81000, 80000]
    assert tel.get_lap_times("blue") == [83000]
    assert tel.get_lap_times("green") == []


@pytest.mark.parametrize("lap_time", BAD_NUMBERS)
def test_invalid_lap_times_are_rejected(tel, lap_time):
    finish(tel, "red", 80000)
    before = state(tel)
    with pytest.raises(ValueError):
        tel.record_lap("red", lap_time)
    assert state(tel) == before


def test_a_finished_car_cannot_add_laps_and_nothing_changes(tel):
    finish(tel, "red", 80000, 81000)
    finish(tel, "blue", 82000, 82000)
    before = state(tel)
    with pytest.raises(TelemetryError):
        tel.record_lap("red", 1000)
    assert state(tel) == before
    tel.record_lap("green", 90000)  # other cars are unaffected
    assert tel.get_lap_times("green") == [90000]


def test_a_car_finishes_after_exactly_the_laps_of_the_race():
    t = RaceTelemetry(3)
    t.add_car("red")
    finish(t, "red", 80000, 80000)
    assert results(t) == []
    t.record_lap("red", 80000)
    assert results(t) == [("red", 10)]
    with pytest.raises(TelemetryError):
        t.record_lap("red", 80000)


def test_a_one_lap_race():
    t = RaceTelemetry(1)
    t.add_car("red")
    t.add_car("blue")
    t.record_lap("blue", 90000)
    assert results(t) == [("blue", 10)]
    with pytest.raises(TelemetryError):
        t.record_lap("blue", 1000)
    t.record_lap("red", 91000)
    assert results(t) == [("blue", 10), ("red", 6)]


# --- results and points -----------------------------------------------------


def test_results_hold_only_finished_cars_lowest_total_first(tel):
    assert results(tel) == []
    finish(tel, "red", 80000, 82000)  # 162000
    finish(tel, "blue", 81000, 80500)  # 161500
    finish(tel, "green", 60000)  # not finished
    assert results(tel) == [("blue", 10), ("red", 6)]


def test_equal_totals_keep_the_order_cars_were_added(tel):
    finish(tel, "green", 80000, 80000)
    finish(tel, "red", 79000, 81000)
    finish(tel, "blue", 81000, 79000)
    assert results(tel) == [("red", 10), ("blue", 6), ("green", 4)]


def test_points_for_every_place():
    t = RaceTelemetry(1)
    cars = [f"car{i}" for i in range(8)]
    for car in cars:
        t.add_car(car)
    for i, car in enumerate(cars):
        t.record_lap(car, 80000 + i)
    assert results(t) == list(zip(cars, [10, 6, 4, 3, 2, 1, 0, 0]))


def test_points_for_every_place_when_cars_finish_in_any_order():
    t = RaceTelemetry(1)
    cars = [f"car{i}" for i in range(7)]
    for car in cars:
        t.add_car(car)
    for i in [3, 6, 0, 5, 1, 4, 2]:
        t.record_lap(cars[i], 80000 + i)
    assert results(t) == list(zip(cars, [10, 6, 4, 3, 2, 1, 0]))


def test_points_move_when_a_faster_car_finishes_later(tel):
    finish(tel, "red", 80000, 80000)
    finish(tel, "blue", 81000, 81000)
    assert results(tel) == [("red", 10), ("blue", 6)]
    finish(tel, "green", 70000, 70000)
    assert results(tel) == [("green", 10), ("red", 6), ("blue", 4)]


def test_telemetry_objects_do_not_share_data():
    first, second = RaceTelemetry(1), RaceTelemetry(1)
    first.add_car("red")
    first.record_lap("red", 90000)
    assert second.get_cars() == []
    second.add_car("red")
    assert second.get_lap_times("red") == []
    assert results(second) == []
