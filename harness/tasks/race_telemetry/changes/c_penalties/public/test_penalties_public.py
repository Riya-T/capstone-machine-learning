"""Public checks for the c_penalties change (time penalties). Shown to the
editor, never to the writer.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_penalties/public/test_penalties_public.py
"""

import pytest
from telemetry import RaceTelemetry


@pytest.fixture
def tel():
    t = RaceTelemetry(2)
    t.add_car("red")
    t.add_car("blue")
    return t


def results(t):
    return [tuple(pair) for pair in t.get_results()]


def test_penalty_adds_to_the_total_time(tel):
    tel.record_lap("red", 90000)
    tel.add_penalty("red", 5000)
    assert tel.get_total_time("red") == 95000
    assert tel.get_penalty("red") == 5000
    assert tel.get_lap_times("red") == [90000]
    assert results(tel) == []


def test_penalty_can_cost_a_place(tel):
    for car, lap in [("red", 90000), ("blue", 91000)]:
        tel.record_lap(car, lap)
        tel.record_lap(car, lap)
    assert results(tel) == [("red", 10), ("blue", 6)]
    tel.add_penalty("red", 3000)
    assert results(tel) == [("blue", 10), ("red", 6)]
