"""Hidden tests for the c_lap_corrections change (versioned lap
corrections). Never shown to the writer or the editor.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lap_corrections/private/test_lap_corrections_new.py
"""

import pytest
from telemetry import RaceTelemetry, TelemetryError, VersionConflict

CARS = ["red", "blue", "green"]
RACES = ["spa", "monza"]


@pytest.fixture
def tel():
    t = RaceTelemetry()
    for car in CARS:
        t.add_car(car)
    t.add_race("spa", 2)
    t.add_race("monza", 1)
    t.record_lap("spa", "red", 90000)
    t.record_lap("spa", "red", 91000)
    t.record_lap("spa", "blue", 92000)
    return t


def state(t):
    return (
        {(r, c): t.get_lap_times(r, c) for r in RACES for c in CARS},
        {r: (t.get_results(r), t.get_version(r)) for r in RACES},
        {c: t.get_points(c) for c in CARS},
    )


def test_correction_versions_start_at_one_and_count_changes(tel):
    assert tel.get_version("monza") == 1
    assert tel.get_version("spa") == 4
    tel.record_lap("monza", "green", 80000)
    tel.correct_lap("monza", "green", 1, 80500)
    tel.correct_lap("monza", "green", 1, 80400)
    assert tel.get_version("monza") == 4
    assert tel.get_version("spa") == 4


def test_correction_of_each_lap_number(tel):
    tel.correct_lap("spa", "red", 1, 88000)
    tel.correct_lap("spa", "blue", 1, 93000)
    assert tel.get_lap_times("spa", "red") == [88000, 91000]
    assert tel.get_lap_times("spa", "blue") == [93000]


def test_correction_changes_results_and_points(tel):
    tel.record_lap("spa", "blue", 92000)  # blue 184000, red 181000
    assert tel.get_results("spa") == ["red", "blue"]
    tel.correct_lap("spa", "red", 2, 95000)  # red 185000
    assert tel.get_results("spa") == ["blue", "red"]
    assert (tel.get_points("blue"), tel.get_points("red")) == (10, 6)


def test_correction_with_the_right_version_works(tel):
    tel.correct_lap("spa", "blue", 1, 91500, expected_version=4)
    tel.record_lap("spa", "blue", 91500, expected_version=5)
    assert tel.get_version("spa") == 6
    assert tel.get_results("spa") == ["red", "blue"]


@pytest.mark.parametrize("version", [1, 3, 5])
def test_correction_conflicts_change_nothing(tel, version):
    before = state(tel)
    with pytest.raises(VersionConflict):
        tel.correct_lap("spa", "red", 1, 80000, expected_version=version)
    with pytest.raises(VersionConflict):
        tel.record_lap("spa", "blue", 80000, expected_version=version)
    assert state(tel) == before


def test_correction_conflict_is_a_telemetry_error():
    assert issubclass(VersionConflict, TelemetryError)


@pytest.mark.parametrize("lap_number", [0, 3, -1, 1.0, "1", None, True])
def test_correction_of_a_lap_that_is_not_recorded(tel, lap_number):
    before = state(tel)
    with pytest.raises(ValueError):
        tel.correct_lap("spa", "red", lap_number, 80000)
    assert state(tel) == before


def test_correction_of_a_car_without_laps(tel):
    with pytest.raises(ValueError):
        tel.correct_lap("spa", "green", 1, 80000)


@pytest.mark.parametrize("lap_time", [0, -5, 1.5, "90000", None])
def test_correction_lap_time_must_be_positive(tel, lap_time):
    before = state(tel)
    with pytest.raises(ValueError):
        tel.correct_lap("spa", "red", 1, lap_time)
    assert state(tel) == before


def test_correction_unknown_ids_raise_key_error(tel):
    before = state(tel)
    for call in (
        lambda: tel.correct_lap("imola", "red", 1, 80000),
        lambda: tel.correct_lap("spa", "pink", 1, 80000),
        lambda: tel.correct_lap("spa", None, 1, 80000, expected_version=9),
        lambda: tel.get_version("imola"),
        lambda: tel.get_version(None),
    ):
        with pytest.raises(KeyError):
            call()
    assert state(tel) == before


def test_correction_error_order(tel):
    with pytest.raises(KeyError):
        tel.correct_lap("spa", "pink", 9, 0, expected_version=9)
    with pytest.raises(ValueError):
        tel.correct_lap("spa", "red", 9, 80000, expected_version=9)
    with pytest.raises(ValueError):
        tel.correct_lap("spa", "red", 1, 0, expected_version=9)
    with pytest.raises(ValueError):
        tel.record_lap("spa", "red", 0, expected_version=9)
    # red has finished spa: the version is checked before that.
    with pytest.raises(VersionConflict):
        tel.record_lap("spa", "red", 80000, expected_version=9)
    with pytest.raises(TelemetryError):
        tel.record_lap("spa", "red", 80000, expected_version=4)
    assert tel.get_version("spa") == 4


def test_correction_failed_record_lap_keeps_the_version(tel):
    with pytest.raises(TelemetryError):
        tel.record_lap("spa", "red", 80000)
    with pytest.raises(ValueError):
        tel.record_lap("spa", "blue", -1)
    assert tel.get_version("spa") == 4
