"""Hidden tests for the initial race_telemetry spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest private/test_telemetry_initial.py
"""

import pytest
from telemetry import RaceTelemetry, TelemetryError

CARS = ["red", "blue", "green"]
RACES = ["monza", "spa"]
BAD_NUMBERS = [0, -5, 1.5, "10", None]


@pytest.fixture
def tel():
    t = RaceTelemetry()
    for car in CARS:
        t.add_car(car)
    t.add_race("monza", 2)
    t.add_race("spa", 1)
    return t


def state(t):
    """Every car, lap time, result and points total, to check that a failed
    call changed nothing."""
    cars = t.get_cars()
    return (
        cars,
        {(r, c): t.get_lap_times(r, c) for r in RACES for c in cars},
        {r: t.get_results(r) for r in RACES},
        {c: t.get_points(c) for c in cars},
    )


def finish(t, race, car, *laps):
    for lap in laps:
        t.record_lap(race, car, lap)


# --- cars and races ---------------------------------------------------------


def test_cars_are_listed_in_the_order_they_were_added():
    t = RaceTelemetry()
    for car in ["green", "red", "blue"]:
        t.add_car(car)
    assert t.get_cars() == ["green", "red", "blue"]


def test_an_empty_car_id_is_rejected():
    t = RaceTelemetry()
    with pytest.raises(ValueError):
        t.add_car("")
    assert t.get_cars() == []


def test_entering_a_car_twice_is_rejected(tel):
    finish(tel, "spa", "red", 90000)
    before = state(tel)
    with pytest.raises(TelemetryError):
        tel.add_car("red")
    assert state(tel) == before


def test_an_empty_race_id_is_rejected(tel):
    with pytest.raises(ValueError):
        tel.add_race("", 3)
    with pytest.raises(KeyError):
        tel.get_results("")


@pytest.mark.parametrize("laps", BAD_NUMBERS)
def test_invalid_lap_counts_are_rejected(tel, laps):
    with pytest.raises(ValueError):
        tel.add_race("imola", laps)
    with pytest.raises(KeyError):
        tel.get_results("imola")


def test_adding_a_race_twice_is_rejected_and_keeps_the_old_race(tel):
    with pytest.raises(TelemetryError):
        tel.add_race("spa", 5)
    finish(tel, "spa", "red", 90000)  # still one lap long
    assert tel.get_results("spa") == ["red"]


@pytest.mark.parametrize(
    "call",
    [
        lambda t: t.record_lap("imola", "red", 80000),
        lambda t: t.record_lap("monza", "pink", 80000),
        lambda t: t.get_lap_times("imola", "red"),
        lambda t: t.get_lap_times("monza", "pink"),
        lambda t: t.get_results("imola"),
        lambda t: t.get_points("pink"),
        lambda t: t.get_results(None),
        lambda t: t.get_points(1),
        lambda t: t.record_lap(None, "red", 80000),
        lambda t: t.get_lap_times("monza", 1),
    ],
)
def test_unknown_races_and_cars_raise_key_error(tel, call):
    finish(tel, "monza", "red", 80000)
    before = state(tel)
    with pytest.raises(KeyError):
        call(tel)
    assert state(tel) == before


# --- laps -------------------------------------------------------------------


def test_lap_times_are_kept_per_race_and_car(tel):
    finish(tel, "monza", "red", 81000, 80000)
    finish(tel, "spa", "red", 95000)
    finish(tel, "monza", "blue", 83000)
    assert tel.get_lap_times("monza", "red") == [81000, 80000]
    assert tel.get_lap_times("spa", "red") == [95000]
    assert tel.get_lap_times("monza", "blue") == [83000]
    assert tel.get_lap_times("spa", "blue") == []


@pytest.mark.parametrize("lap_time", BAD_NUMBERS)
def test_invalid_lap_times_are_rejected(tel, lap_time):
    finish(tel, "monza", "red", 80000)
    before = state(tel)
    with pytest.raises(ValueError):
        tel.record_lap("monza", "red", lap_time)
    assert state(tel) == before


def test_a_finished_car_cannot_add_laps_and_nothing_changes(tel):
    finish(tel, "monza", "red", 80000, 81000)
    finish(tel, "monza", "blue", 82000, 82000)
    before = state(tel)
    with pytest.raises(TelemetryError):
        tel.record_lap("monza", "red", 1000)
    assert state(tel) == before
    tel.record_lap("spa", "red", 90000)  # other races are unaffected
    assert tel.get_lap_times("spa", "red") == [90000]


def test_an_unknown_car_is_reported_before_a_bad_lap_time(tel):
    with pytest.raises(KeyError):
        tel.record_lap("monza", "pink", -1)
    with pytest.raises(KeyError):
        tel.record_lap("imola", "red", 0)


def test_a_bad_lap_time_is_reported_before_a_finished_car(tel):
    finish(tel, "spa", "red", 90000)
    with pytest.raises(ValueError):
        tel.record_lap("spa", "red", 0)


# --- results ----------------------------------------------------------------


def test_results_hold_only_finished_cars_lowest_total_first(tel):
    finish(tel, "monza", "red", 80000, 82000)  # 162000
    finish(tel, "monza", "blue", 81000, 80500)  # 161500
    finish(tel, "monza", "green", 60000)  # not finished
    assert tel.get_results("monza") == ["blue", "red"]
    assert tel.get_results("spa") == []


def test_equal_totals_keep_the_order_cars_were_added(tel):
    finish(tel, "monza", "green", 80000, 80000)
    finish(tel, "monza", "red", 79000, 81000)
    finish(tel, "monza", "blue", 81000, 79000)
    assert tel.get_results("monza") == ["red", "blue", "green"]


def test_results_are_kept_per_race(tel):
    finish(tel, "monza", "red", 80000, 80000)
    finish(tel, "monza", "blue", 79000, 79000)
    finish(tel, "spa", "blue", 99000)
    finish(tel, "spa", "red", 98000)
    assert tel.get_results("monza") == ["blue", "red"]
    assert tel.get_results("spa") == ["red", "blue"]


# --- points -----------------------------------------------------------------


def test_points_for_every_place():
    t = RaceTelemetry()
    cars = [f"car{i}" for i in range(8)]
    for car in cars:
        t.add_car(car)
    t.add_race("monza", 1)
    for i, car in enumerate(cars):
        t.record_lap("monza", car, 80000 + i)
    assert [t.get_points(c) for c in cars] == [10, 6, 4, 3, 2, 1, 0, 0]


def test_points_add_up_over_races(tel):
    finish(tel, "monza", "red", 80000, 80000)
    finish(tel, "monza", "blue", 81000, 81000)
    finish(tel, "spa", "blue", 90000)
    finish(tel, "spa", "red", 91000)
    finish(tel, "spa", "green", 92000)
    assert tel.get_points("red") == 16
    assert tel.get_points("blue") == 16
    assert tel.get_points("green") == 4


def test_a_car_without_a_finish_has_no_points(tel):
    finish(tel, "monza", "red", 50000)
    assert tel.get_points("red") == 0
    assert tel.get_points("green") == 0


def test_points_move_when_a_faster_car_finishes_later(tel):
    finish(tel, "monza", "red", 80000, 80000)
    finish(tel, "monza", "blue", 81000, 81000)
    assert (tel.get_points("red"), tel.get_points("blue")) == (10, 6)
    finish(tel, "monza", "green", 70000, 70000)
    assert [tel.get_points(c) for c in ["green", "red", "blue"]] == [10, 6, 4]


def test_telemetry_objects_do_not_share_data():
    first, second = RaceTelemetry(), RaceTelemetry()
    first.add_car("red")
    first.add_race("spa", 1)
    first.record_lap("spa", "red", 90000)
    assert second.get_cars() == []
    second.add_car("red")
    second.add_race("spa", 1)
    assert second.get_results("spa") == []
    assert second.get_points("red") == 0
