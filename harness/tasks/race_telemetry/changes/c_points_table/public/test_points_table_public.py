"""Public checks for the c_points_table change (an adjustable points table).
Shown to the editor, never to the writer.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_points_table/public/test_points_table_public.py
"""

from telemetry import RaceTelemetry


def make(**kwargs):
    t = RaceTelemetry(1, **kwargs)
    for car in ["red", "blue", "green"]:
        t.add_car(car)
    return t


def results(t):
    return [tuple(pair) for pair in t.get_results()]


def test_table_chosen_for_the_race():
    t = make(points_table=(25, 18))
    for car, lap in [("red", 90000), ("blue", 91000), ("green", 92000)]:
        t.record_lap(car, lap)
    assert results(t) == [("red", 25), ("blue", 18), ("green", 0)]
    assert t.get_points_table() == [25, 18]


def test_table_set_later_applies_to_cars_already_finished():
    t = make()
    assert t.get_points_table() == [10, 6, 4, 3, 2, 1]
    t.record_lap("blue", 90000)
    t.record_lap("red", 91000)
    t.set_points_table([20, 12])
    assert results(t) == [("blue", 20), ("red", 12)]
    assert t.get_points_table() == [20, 12]
