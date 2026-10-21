"""Hidden tests for the c_points_table change (adjustable points tables).
Never shown to the writer or the editor.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_points_table/private/test_points_table_new.py
"""

import pytest
from telemetry import RaceTelemetry, TelemetryError

BAD_TABLES = [10, "10,6", {1: 10}, [10, -1], [10, 1.5], [10, "6"], (True, 1)]
CARS = ["red", "blue", "green", "pink"]


@pytest.fixture
def tel():
    t = RaceTelemetry()
    for car in CARS:
        t.add_car(car)
    t.add_race("spa", 1)
    t.add_race("finale", 1, points_table=(20, 12, 8))
    return t


def run(t, race, order):
    """Finish a one-lap race with the cars in `order`, fastest first."""
    for i, car in enumerate(order):
        t.record_lap(race, car, 90000 + 100 * i)


def points(t):
    return [t.get_points(c) for c in CARS]


def test_table_default_is_the_old_table():
    t = RaceTelemetry()
    assert t.get_points_table() == [10, 6, 4, 3, 2, 1]
    t.add_race("spa", 1)
    assert t.get_points_table("spa") == [10, 6, 4, 3, 2, 1]


def test_table_places_past_the_end_score_nothing():
    t = RaceTelemetry(points_table=[7])
    for car in CARS:
        t.add_car(car)
    t.add_race("spa", 1)
    run(t, "spa", ["green", "red", "blue"])
    assert points(t) == [0, 0, 7, 0]


def test_table_can_be_longer_than_six_places():
    cars = [f"car{i}" for i in range(8)]
    t = RaceTelemetry(points_table=list(range(16, 0, -2)))
    for car in cars:
        t.add_car(car)
    t.add_race("spa", 1)
    run(t, "spa", cars)
    assert [t.get_points(c) for c in cars] == [16, 14, 12, 10, 8, 6, 4, 2]


def test_table_can_be_empty(tel):
    tel.add_race("friendly", 1, points_table=[])
    run(tel, "friendly", ["red", "blue"])
    assert points(tel) == [0, 0, 0, 0]
    assert tel.get_points_table("friendly") == []


def test_table_of_a_race_is_used_only_for_that_race(tel):
    run(tel, "spa", ["red", "blue", "green"])
    run(tel, "finale", ["blue", "green", "red", "pink"])
    assert points(tel) == [10 + 8, 6 + 20, 4 + 12, 0]


def test_table_set_for_the_series_applies_to_earlier_races(tel):
    run(tel, "spa", ["red", "blue"])
    run(tel, "finale", ["red", "blue"])
    tel.set_points_table((3, 2, 1))
    assert tel.get_points_table() == [3, 2, 1]
    assert tel.get_points_table("spa") == [3, 2, 1]
    assert tel.get_points_table("finale") == [20, 12, 8]
    assert points(tel) == [3 + 20, 2 + 12, 0, 0]
    tel.add_race("monza", 1)
    run(tel, "monza", ["green"])
    assert tel.get_points("green") == 3


@pytest.mark.parametrize("table", BAD_TABLES)
def test_table_invalid_in_the_constructor(table):
    with pytest.raises(ValueError):
        RaceTelemetry(points_table=table)


@pytest.mark.parametrize("table", BAD_TABLES)
def test_table_invalid_when_adding_a_race(tel, table):
    with pytest.raises(ValueError):
        tel.add_race("monza", 1, points_table=table)
    with pytest.raises(KeyError):
        tel.get_points_table("monza")


@pytest.mark.parametrize("table", BAD_TABLES)
def test_table_invalid_when_setting(tel, table):
    run(tel, "spa", ["red"])
    with pytest.raises(ValueError):
        tel.set_points_table(table)
    assert tel.get_points_table() == [10, 6, 4, 3, 2, 1]
    assert tel.get_points("red") == 10


def test_table_errors_come_before_a_race_id_in_use(tel):
    with pytest.raises(ValueError):
        tel.add_race("spa", 1, points_table=[-1])
    assert tel.get_points_table("spa") == [10, 6, 4, 3, 2, 1]
    with pytest.raises(TelemetryError):
        tel.add_race("spa", 2, points_table=[1])
    assert tel.get_points_table("spa") == [10, 6, 4, 3, 2, 1]


def test_table_of_an_unknown_race_raises_key_error(tel):
    with pytest.raises(KeyError):
        tel.get_points_table("monza")
    with pytest.raises(KeyError):
        tel.get_points_table(1)
