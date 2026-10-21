"""Hidden tests for the c_penalties change (time penalties). Never shown to
the writer or the editor.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_penalties/private/test_penalties_new.py
"""

import pytest
from telemetry import RaceTelemetry

CARS = ["red", "blue", "green"]
BAD_PENALTIES = [0, -1000, 2.5, "500", None]


@pytest.fixture
def tel():
    t = RaceTelemetry()
    for car in CARS:
        t.add_car(car)
    t.add_race("spa", 2)
    t.add_race("monza", 1)
    return t


def state(t):
    return (
        {(r, c): (t.get_lap_times(r, c), t.get_penalty(r, c), t.get_total_time(r, c))
         for r in ["spa", "monza"] for c in CARS},
        {r: t.get_results(r) for r in ["spa", "monza"]},
        {c: t.get_points(c) for c in CARS},
    )


def test_penalty_starts_at_zero(tel):
    assert tel.get_penalty("spa", "red") == 0
    assert tel.get_total_time("spa", "red") == 0
    tel.record_lap("spa", "red", 90000)
    assert tel.get_total_time("spa", "red") == 90000


def test_penalty_amounts_add_up(tel):
    tel.add_penalty("spa", "red", 1000)
    tel.add_penalty("spa", "red", 2500)
    assert tel.get_penalty("spa", "red") == 3500
    assert tel.get_penalty("monza", "red") == 0
    assert tel.get_penalty("spa", "blue") == 0


def test_penalty_before_the_first_lap_counts(tel):
    tel.add_penalty("spa", "red", 4000)
    assert tel.get_total_time("spa", "red") == 4000
    assert tel.get_results("spa") == []
    tel.record_lap("spa", "red", 90000)
    tel.record_lap("spa", "red", 91000)
    assert tel.get_total_time("spa", "red") == 185000
    assert tel.get_results("spa") == ["red"]


def test_penalty_after_the_finish_reorders_results_and_points(tel):
    for car, lap in [("red", 90000), ("blue", 90500), ("green", 91000)]:
        tel.record_lap("spa", car, lap)
        tel.record_lap("spa", car, lap)
    assert tel.get_results("spa") == ["red", "blue", "green"]
    tel.add_penalty("spa", "red", 2500)  # 182500, behind green's 182000
    assert tel.get_results("spa") == ["blue", "green", "red"]
    assert [tel.get_points(c) for c in CARS] == [4, 10, 6]


def test_penalty_ties_keep_the_order_cars_were_added(tel):
    tel.record_lap("monza", "green", 90000)
    tel.record_lap("monza", "blue", 89000)
    tel.add_penalty("monza", "blue", 1000)
    assert tel.get_results("monza") == ["blue", "green"]


def test_penalty_does_not_finish_a_car(tel):
    tel.record_lap("spa", "red", 90000)
    tel.add_penalty("spa", "red", 1000)
    assert tel.get_results("spa") == []
    assert tel.get_points("red") == 0


def test_penalty_is_kept_per_race(tel):
    tel.record_lap("monza", "red", 90000)
    tel.record_lap("monza", "blue", 90100)
    tel.add_penalty("spa", "red", 9000)
    assert tel.get_results("monza") == ["red", "blue"]
    assert tel.get_total_time("monza", "red") == 90000


@pytest.mark.parametrize("penalty", BAD_PENALTIES)
def test_penalty_amount_must_be_positive(tel, penalty):
    tel.record_lap("monza", "red", 90000)
    before = state(tel)
    with pytest.raises(ValueError):
        tel.add_penalty("monza", "red", penalty)
    assert state(tel) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda t: t.add_penalty("imola", "red", 1000),
        lambda t: t.add_penalty("spa", "pink", 1000),
        lambda t: t.add_penalty("spa", "pink", -1),
        lambda t: t.add_penalty(None, "red", 0),
        lambda t: t.get_penalty("imola", "red"),
        lambda t: t.get_penalty("spa", None),
        lambda t: t.get_total_time("imola", "red"),
        lambda t: t.get_total_time("spa", 1),
    ],
)
def test_penalty_methods_raise_key_error_for_unknown_ids(tel, call):
    tel.record_lap("monza", "red", 90000)
    before = state(tel)
    with pytest.raises(KeyError):
        call(tel)
    assert state(tel) == before
