"""Public checks for telemetry.py.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest public/test_telemetry_public.py
"""

import pytest
from telemetry import RaceTelemetry, TelemetryError


@pytest.fixture
def tel():
    t = RaceTelemetry(2)
    for car in ["red", "blue", "green"]:
        t.add_car(car)
    return t


def results(t):
    return [tuple(pair) for pair in t.get_results()]


def test_lap_times_are_kept_in_order(tel):
    tel.record_lap("red", 80500)
    tel.record_lap("red", 79900)
    assert tel.get_lap_times("red") == [80500, 79900]
    assert tel.get_lap_times("blue") == []


def test_results_list_finished_cars_fastest_first(tel):
    tel.record_lap("red", 82000)
    tel.record_lap("red", 81000)  # total 163000
    tel.record_lap("blue", 80000)
    tel.record_lap("blue", 80000)  # total 160000
    tel.record_lap("green", 70000)  # only one of two laps
    assert results(tel) == [("blue", 10), ("red", 6)]


def test_equal_totals_are_listed_in_the_order_cars_were_added(tel):
    tel.record_lap("green", 80000)
    tel.record_lap("green", 80000)  # total 160000
    tel.record_lap("blue", 79000)
    tel.record_lap("blue", 81000)  # total 160000
    assert results(tel) == [("blue", 10), ("green", 6)]


def test_points_follow_the_places(tel):
    for car, lap in [("red", 81000), ("blue", 80000), ("green", 82000)]:
        tel.record_lap(car, lap)
        tel.record_lap(car, lap)
    assert results(tel) == [("blue", 10), ("red", 6), ("green", 4)]


def test_a_faster_late_finisher_takes_the_points(tel):
    tel.record_lap("red", 81000)
    tel.record_lap("red", 81000)
    assert results(tel) == [("red", 10)]
    tel.record_lap("blue", 79000)
    tel.record_lap("blue", 79000)
    assert results(tel) == [("blue", 10), ("red", 6)]


def test_a_finished_car_cannot_record_more_laps(tel):
    tel.record_lap("red", 81000)
    tel.record_lap("red", 81000)
    with pytest.raises(TelemetryError):
        tel.record_lap("red", 81000)
    assert tel.get_lap_times("red") == [81000, 81000]


def test_unknown_cars_raise_key_error(tel):
    with pytest.raises(KeyError):
        tel.record_lap("pink", 80000)
    with pytest.raises(KeyError):
        tel.get_lap_times("pink")
