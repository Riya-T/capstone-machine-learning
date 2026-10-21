"""Public checks for telemetry.py.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest public/test_telemetry_public.py
"""

import pytest
from telemetry import RaceTelemetry, TelemetryError


@pytest.fixture
def tel():
    t = RaceTelemetry()
    for car in ["red", "blue", "green"]:
        t.add_car(car)
    t.add_race("monza", 2)
    return t


def test_lap_times_are_kept_in_order(tel):
    tel.record_lap("monza", "red", 80500)
    tel.record_lap("monza", "red", 79900)
    assert tel.get_lap_times("monza", "red") == [80500, 79900]
    assert tel.get_lap_times("monza", "blue") == []


def test_results_list_finished_cars_fastest_first(tel):
    tel.record_lap("monza", "red", 82000)
    tel.record_lap("monza", "red", 81000)  # total 163000
    tel.record_lap("monza", "blue", 80000)
    tel.record_lap("monza", "blue", 80000)  # total 160000
    tel.record_lap("monza", "green", 70000)  # only one of two laps
    assert tel.get_results("monza") == ["blue", "red"]


def test_points_follow_the_places(tel):
    for car, lap in [("red", 81000), ("blue", 80000), ("green", 82000)]:
        tel.record_lap("monza", car, lap)
        tel.record_lap("monza", car, lap)
    assert [tel.get_points(c) for c in ["blue", "red", "green"]] == [10, 6, 4]


def test_a_faster_late_finisher_takes_the_points(tel):
    tel.record_lap("monza", "red", 81000)
    tel.record_lap("monza", "red", 81000)
    assert tel.get_points("red") == 10
    tel.record_lap("monza", "blue", 79000)
    tel.record_lap("monza", "blue", 79000)
    assert tel.get_points("blue") == 10
    assert tel.get_points("red") == 6


def test_a_finished_car_cannot_record_more_laps(tel):
    tel.record_lap("monza", "red", 81000)
    tel.record_lap("monza", "red", 81000)
    with pytest.raises(TelemetryError):
        tel.record_lap("monza", "red", 81000)
    assert tel.get_lap_times("monza", "red") == [81000, 81000]


def test_unknown_race_or_car_raises_key_error(tel):
    with pytest.raises(KeyError):
        tel.get_results("spa")
    with pytest.raises(KeyError):
        tel.record_lap("monza", "pink", 80000)
