"""Public checks for the c_penalties change (time penalties). Shown to the
editor, never to the writer.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_penalties/public/test_penalties_public.py
"""

import pytest
from telemetry import RaceTelemetry


@pytest.fixture
def tel():
    t = RaceTelemetry()
    t.add_car("red")
    t.add_car("blue")
    t.add_race("spa", 2)
    return t


def test_penalty_adds_to_the_total_time(tel):
    tel.record_lap("spa", "red", 90000)
    tel.add_penalty("spa", "red", 5000)
    assert tel.get_total_time("spa", "red") == 95000
    assert tel.get_penalty("spa", "red") == 5000
    assert tel.get_lap_times("spa", "red") == [90000]


def test_penalty_can_cost_a_place(tel):
    for car, lap in [("red", 90000), ("blue", 91000)]:
        tel.record_lap("spa", car, lap)
        tel.record_lap("spa", car, lap)
    tel.add_penalty("spa", "red", 3000)
    assert tel.get_results("spa") == ["blue", "red"]
    assert (tel.get_points("blue"), tel.get_points("red")) == (10, 6)
