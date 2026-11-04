"""Hidden tests for the c_penalties change (time penalties). Never shown to
the writer or the editor.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_penalties/private/test_penalties_new.py
"""

import pytest
from telemetry import RaceTelemetry

CARS = ["red", "blue", "green"]
BAD_PENALTIES = [0, -1000]


@pytest.fixture
def tel():
    t = RaceTelemetry(2)
    for car in CARS:
        t.add_car(car)
    return t


def results(t):
    return [tuple(pair) for pair in t.get_results()]


def state(t):
    return (
        {c: (t.get_lap_times(c), t.get_penalty(c), t.get_total_time(c)) for c in CARS},
        results(t),
    )


def test_penalty_starts_at_zero(tel):
    assert tel.get_penalty("red") == 0
    assert tel.get_total_time("red") == 0
    tel.record_lap("red", 90000)
    assert tel.get_total_time("red") == 90000


def test_penalty_amounts_add_up(tel):
    tel.add_penalty("red", 1000)
    tel.add_penalty("red", 2500)
    assert tel.get_penalty("red") == 3500
    assert tel.get_penalty("blue") == 0
    assert tel.get_total_time("blue") == 0


def test_penalty_before_the_first_lap_counts(tel):
    tel.add_penalty("red", 4000)
    assert tel.get_total_time("red") == 4000
    assert results(tel) == []
    tel.record_lap("red", 90000)
    tel.record_lap("red", 91000)
    assert tel.get_total_time("red") == 185000
    assert results(tel) == [("red", 10)]


def test_penalty_after_the_finish_reorders_results_and_points(tel):
    for car, lap in [("red", 90000), ("blue", 90500), ("green", 91000)]:
        tel.record_lap(car, lap)
        tel.record_lap(car, lap)
    assert results(tel) == [("red", 10), ("blue", 6), ("green", 4)]
    tel.add_penalty("red", 2500)  # 182500, behind green's 182000
    assert results(tel) == [("blue", 10), ("green", 6), ("red", 4)]


def test_penalty_ties_keep_the_order_cars_were_added(tel):
    tel.record_lap("green", 90000)
    tel.record_lap("green", 90000)  # 180000
    tel.record_lap("blue", 89000)
    tel.record_lap("blue", 90000)
    tel.add_penalty("blue", 1000)  # 180000 as well
    assert results(tel) == [("blue", 10), ("green", 6)]


def test_penalty_does_not_finish_a_car(tel):
    tel.record_lap("red", 90000)
    tel.add_penalty("red", 1000)
    assert results(tel) == []
    tel.record_lap("red", 90000)
    assert results(tel) == [("red", 10)]


def test_penalty_is_kept_per_car(tel):
    for car, lap in [("red", 90000), ("blue", 90100)]:
        tel.record_lap(car, lap)
        tel.record_lap(car, lap)
    tel.add_penalty("green", 9000)
    assert results(tel) == [("red", 10), ("blue", 6)]
    assert tel.get_total_time("red") == 180000
    assert tel.get_total_time("green") == 9000


@pytest.mark.parametrize("penalty", BAD_PENALTIES)
def test_penalty_amount_must_be_positive(tel, penalty):
    tel.record_lap("red", 90000)
    tel.add_penalty("red", 500)
    before = state(tel)
    with pytest.raises(ValueError):
        tel.add_penalty("red", penalty)
    assert state(tel) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda t: t.add_penalty("pink", 1000),
        lambda t: t.add_penalty(None, 1000),
        lambda t: t.get_penalty("pink"),
        lambda t: t.get_penalty(None),
        lambda t: t.get_total_time("pink"),
        lambda t: t.get_total_time(1),
    ],
)
def test_penalty_methods_raise_key_error_for_unknown_cars(tel, call):
    tel.record_lap("red", 90000)
    before = state(tel)
    with pytest.raises(KeyError):
        call(tel)
    assert state(tel) == before
