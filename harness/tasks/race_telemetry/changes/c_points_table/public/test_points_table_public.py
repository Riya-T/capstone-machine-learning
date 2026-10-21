"""Public checks for the c_points_table change (adjustable points tables).
Shown to the editor, never to the writer.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_points_table/public/test_points_table_public.py
"""

from telemetry import RaceTelemetry


def make(**kwargs):
    t = RaceTelemetry(**kwargs)
    for car in ["red", "blue", "green"]:
        t.add_car(car)
    return t


def test_table_for_the_whole_series():
    t = make(points_table=(25, 18))
    t.add_race("spa", 1)
    for car, lap in [("red", 90000), ("blue", 91000), ("green", 92000)]:
        t.record_lap("spa", car, lap)
    assert [t.get_points(c) for c in ["red", "blue", "green"]] == [25, 18, 0]
    assert t.get_points_table() == [25, 18]


def test_table_for_one_race():
    t = make()
    t.add_race("finale", 1, points_table=[20, 12])
    t.record_lap("finale", "blue", 90000)
    t.record_lap("finale", "red", 91000)
    assert (t.get_points("blue"), t.get_points("red")) == (20, 12)
    assert t.get_points_table("finale") == [20, 12]
    assert t.get_points_table() == [10, 6, 4, 3, 2, 1]
