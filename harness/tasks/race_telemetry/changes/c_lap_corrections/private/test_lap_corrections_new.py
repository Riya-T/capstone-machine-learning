"""Hidden tests for the c_lap_corrections change (versioned lap
corrections). Never shown to the writer or the editor.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lap_corrections/private/test_lap_corrections_new.py
"""

import pytest
from telemetry import RaceTelemetry, TelemetryError, VersionConflict

CARS = ["red", "blue", "green"]


@pytest.fixture
def tel():
    t = RaceTelemetry(2)
    for car in CARS:
        t.add_car(car)
    t.record_lap("red", 90000)
    t.record_lap("red", 91000)
    t.record_lap("blue", 92000)
    return t  # version 4


def results(t):
    return [tuple(pair) for pair in t.get_results()]


def state(t):
    return {c: t.get_lap_times(c) for c in CARS}, results(t), t.get_version()


def test_correction_versions_start_at_one_and_count_changes(tel):
    assert tel.get_version() == 4
    t = RaceTelemetry(1)
    t.add_car("green")
    assert t.get_version() == 1
    t.record_lap("green", 80000)
    t.correct_lap("green", 1, 80500)
    t.correct_lap("green", 1, 80400)
    assert t.get_version() == 4
    assert t.get_lap_times("green") == [80400]


def test_correction_of_each_lap_number(tel):
    tel.correct_lap("red", 1, 88000)
    tel.correct_lap("blue", 1, 93000)
    tel.correct_lap("red", 2, 89000)
    assert tel.get_lap_times("red") == [88000, 89000]
    assert tel.get_lap_times("blue") == [93000]
    assert tel.get_version() == 7


def test_correction_changes_results_and_points(tel):
    tel.record_lap("blue", 92000)  # blue 184000, red 181000
    assert results(tel) == [("red", 10), ("blue", 6)]
    tel.correct_lap("red", 2, 95000)  # red 185000
    assert results(tel) == [("blue", 10), ("red", 6)]


def test_correction_with_the_right_version_works(tel):
    tel.correct_lap("blue", 1, 91500, expected_version=4)
    tel.record_lap("blue", 91500, expected_version=5)
    assert tel.get_version() == 6
    assert results(tel) == [("red", 10), ("blue", 6)]


@pytest.mark.parametrize("version", [1, 3, 5])
def test_correction_conflicts_change_nothing(tel, version):
    before = state(tel)
    with pytest.raises(VersionConflict):
        tel.correct_lap("red", 1, 80000, expected_version=version)
    with pytest.raises(VersionConflict):
        tel.record_lap("blue", 80000, expected_version=version)
    assert state(tel) == before


def test_correction_conflict_is_a_telemetry_error():
    assert issubclass(VersionConflict, TelemetryError)


@pytest.mark.parametrize("lap_number", [0, 3, -1])
def test_correction_of_a_lap_that_is_not_recorded(tel, lap_number):
    before = state(tel)
    with pytest.raises(ValueError):
        tel.correct_lap("red", lap_number, 80000)
    assert state(tel) == before


def test_correction_of_a_car_without_laps(tel):
    before = state(tel)
    with pytest.raises(ValueError):
        tel.correct_lap("green", 1, 80000)
    with pytest.raises(ValueError):
        tel.correct_lap("blue", 2, 80000)
    assert state(tel) == before


@pytest.mark.parametrize("lap_time", [0, -5])
def test_correction_lap_time_must_be_positive(tel, lap_time):
    before = state(tel)
    with pytest.raises(ValueError):
        tel.correct_lap("red", 1, lap_time)
    assert state(tel) == before


def test_correction_unknown_cars_raise_key_error(tel):
    before = state(tel)
    for call in (
        lambda: tel.correct_lap("pink", 1, 80000),
        lambda: tel.correct_lap(None, 1, 80000, expected_version=4),
    ):
        with pytest.raises(KeyError):
            call()
    assert state(tel) == before


def test_correction_a_finished_car_is_still_refused_with_the_right_version(tel):
    with pytest.raises(TelemetryError):  # red has finished; the race is at version 4
        tel.record_lap("red", 80000, expected_version=4)
    assert tel.get_version() == 4


def test_correction_failed_record_lap_keeps_the_version(tel):
    with pytest.raises(TelemetryError):
        tel.record_lap("red", 80000)
    with pytest.raises(ValueError):
        tel.record_lap("blue", -1)
    with pytest.raises(KeyError):
        tel.record_lap("pink", 80000)
    assert tel.get_version() == 4
