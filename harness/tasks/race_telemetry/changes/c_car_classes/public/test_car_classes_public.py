"""Public checks for the c_car_classes change (car classes). Shown to the
editor, never to the writer.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_car_classes/public/test_car_classes_public.py
"""

from telemetry import RaceTelemetry


def make():
    t = RaceTelemetry(1)
    t.add_car("red", car_class="pro")
    t.add_car("blue", car_class="amateur")
    t.add_car("green", car_class="pro")
    t.add_car("grey")
    return t


def results(t, **kwargs):
    return [tuple(pair) for pair in t.get_results(**kwargs)]


def test_class_lists():
    t = make()
    assert t.get_car_class("grey") == "open"
    assert t.get_classes() == ["pro", "amateur", "open"]
    assert t.get_cars(car_class="pro") == ["red", "green"]
    assert t.get_cars() == ["red", "blue", "green", "grey"]


def test_class_results_score_places_within_the_class():
    t = make()
    for car, lap in [("blue", 90000), ("green", 91000), ("red", 92000)]:
        t.record_lap(car, lap)
    assert results(t, car_class="pro") == [("green", 10), ("red", 6)]
    assert results(t) == [("blue", 10), ("green", 6), ("red", 4)]
