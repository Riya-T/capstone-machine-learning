"""Hidden tests for the c_points_table change (an adjustable points table).
Never shown to the writer or the editor.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_points_table/private/test_points_table_new.py
"""

import pytest
from telemetry import RaceTelemetry, TelemetryError

BAD_TABLES = [10, "10,6", {1: 10}, [10, -1], (-2,)]
CARS = ["red", "blue", "green", "pink"]


def make(**kwargs):
    t = RaceTelemetry(1, **kwargs)
    for car in CARS:
        t.add_car(car)
    return t


def results(t):
    return [tuple(pair) for pair in t.get_results()]


def run(t, order):
    """Finish the one-lap race with the cars in `order`, fastest first."""
    for i, car in enumerate(order):
        t.record_lap(car, 90000 + 100 * i)


def test_table_default_is_the_old_table():
    t = make()
    assert t.get_points_table() == [10, 6, 4, 3, 2, 1]
    run(t, ["green", "red", "blue", "pink"])
    assert results(t) == [("green", 10), ("red", 6), ("blue", 4), ("pink", 3)]


def test_table_places_past_the_end_score_nothing():
    t = make(points_table=[7])
    run(t, ["green", "red", "blue"])
    assert results(t) == [("green", 7), ("red", 0), ("blue", 0)]


def test_table_can_be_longer_than_six_places():
    cars = [f"car{i}" for i in range(8)]
    t = RaceTelemetry(1, points_table=list(range(16, 0, -2)))
    for car in cars:
        t.add_car(car)
    run(t, cars)
    assert results(t) == list(zip(cars, [16, 14, 12, 10, 8, 6, 4, 2]))


def test_table_can_be_empty():
    t = make(points_table=[])
    run(t, ["red", "blue"])
    assert results(t) == [("red", 0), ("blue", 0)]
    assert t.get_points_table() == []


def test_table_set_later_applies_to_every_finished_car():
    t = make()
    run(t, ["red", "blue"])
    t.set_points_table((3, 2, 1))
    assert t.get_points_table() == [3, 2, 1]
    assert results(t) == [("red", 3), ("blue", 2)]
    t.record_lap("green", 80000)  # the fastest of all
    assert results(t) == [("green", 3), ("red", 2), ("blue", 1)]


def test_table_can_be_set_more_than_once():
    t = make(points_table=[1])
    t.set_points_table([5, 4])
    t.set_points_table([9])
    run(t, ["pink", "red"])
    assert results(t) == [("pink", 9), ("red", 0)]
    assert t.get_points_table() == [9]


@pytest.mark.parametrize("table", BAD_TABLES)
def test_table_invalid_in_the_constructor(table):
    with pytest.raises(ValueError):
        RaceTelemetry(1, points_table=table)


@pytest.mark.parametrize("table", BAD_TABLES)
def test_table_invalid_when_setting(table):
    t = make(points_table=[8, 4])
    run(t, ["red"])
    with pytest.raises(ValueError):
        t.set_points_table(table)
    assert t.get_points_table() == [8, 4]
    assert results(t) == [("red", 8)]


def test_table_leaves_the_other_rules_alone():
    with pytest.raises(ValueError):
        RaceTelemetry(0, points_table=[5])
    t = make(points_table=[5])
    run(t, ["red"])
    with pytest.raises(TelemetryError):
        t.record_lap("red", 1000)
    assert results(t) == [("red", 5)]
