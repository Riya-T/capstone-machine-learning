"""Public checks for the c_car_classes change (car classes). Shown to the
editor, never to the writer.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_car_classes/public/test_car_classes_public.py
"""

from telemetry import RaceTelemetry


def make():
    t = RaceTelemetry()
    t.add_car("red", car_class="pro")
    t.add_car("blue", car_class="amateur")
    t.add_car("green", car_class="pro")
    t.add_car("grey")
    t.add_race("spa", 1)
    return t


def test_class_lists():
    t = make()
    assert t.get_car_class("grey") == "open"
    assert t.get_classes() == ["pro", "amateur", "open"]
    assert t.get_cars(car_class="pro") == ["red", "green"]


def test_class_results_and_points():
    t = make()
    for car, lap in [("blue", 90000), ("green", 91000), ("red", 92000)]:
        t.record_lap("spa", car, lap)
    assert t.get_results("spa", car_class="pro") == ["green", "red"]
    assert t.get_class_points("green") == 10
    assert t.get_points("green") == 6
