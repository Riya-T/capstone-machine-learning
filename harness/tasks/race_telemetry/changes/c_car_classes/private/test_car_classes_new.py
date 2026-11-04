"""Hidden tests for the c_car_classes change (car classes). Never shown to
the writer or the editor.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_car_classes/private/test_car_classes_new.py
"""

import pytest
from telemetry import RaceTelemetry, TelemetryError

CARS = [("red", "pro"), ("blue", "amateur"), ("green", "pro"), ("pink", "amateur"), ("gold", "pro")]


def make(**kwargs):
    t = RaceTelemetry(1, **kwargs)
    for car, car_class in CARS:
        t.add_car(car, car_class=car_class)
    return t


@pytest.fixture
def tel():
    return make()


def results(t, **kwargs):
    return [tuple(pair) for pair in t.get_results(**kwargs)]


def run(t, order):
    """Finish the one-lap race with the cars in `order`, fastest first."""
    for i, car in enumerate(order):
        t.record_lap(car, 90000 + 100 * i)


def test_class_default_is_open():
    t = RaceTelemetry(1)
    t.add_car("red")
    t.add_car("blue", car_class="pro")
    assert t.get_car_class("red") == "open"
    assert t.get_classes() == ["open", "pro"]
    assert t.get_cars() == ["red", "blue"]
    assert t.get_cars(car_class="open") == ["red"]


def test_class_of_each_car(tel):
    assert [tel.get_car_class(c) for c, _ in CARS] == [k for _, k in CARS]
    assert tel.get_classes() == ["pro", "amateur"]


def test_class_filter_on_cars(tel):
    assert tel.get_cars(car_class="pro") == ["red", "green", "gold"]
    assert tel.get_cars(car_class="amateur") == ["blue", "pink"]
    assert tel.get_cars(car_class="rookie") == []
    assert tel.get_cars(car_class=None) == ["red", "blue", "green", "pink", "gold"]


def test_class_filter_on_results(tel):
    run(tel, ["pink", "gold", "blue", "red"])  # green has not finished
    assert results(tel) == [("pink", 10), ("gold", 6), ("blue", 4), ("red", 3)]
    assert results(tel, car_class="pro") == [("gold", 10), ("red", 6)]
    assert results(tel, car_class="amateur") == [("pink", 10), ("blue", 6)]
    assert results(tel, car_class="rookie") == []
    assert results(tel, car_class=None) == results(tel)


def test_class_results_use_the_points_table():
    t = make(points_table=[20, 12])
    run(t, ["red", "blue", "green", "gold", "pink"])
    assert results(t, car_class="pro") == [("red", 20), ("green", 12), ("gold", 0)]
    assert results(t, car_class="amateur") == [("blue", 20), ("pink", 12)]
    t.set_points_table([1])
    assert results(t, car_class="pro") == [("red", 1), ("green", 0), ("gold", 0)]


def test_class_results_include_penalties(tel):
    run(tel, ["red", "green", "gold"])
    tel.add_penalty("red", 150)  # 90150, behind green's 90100
    assert results(tel, car_class="pro") == [("green", 10), ("red", 6), ("gold", 4)]


def test_class_ties_keep_the_order_cars_were_added(tel):
    for car in ["gold", "green", "red"]:
        tel.record_lap(car, 90000)
    assert results(tel, car_class="pro") == [("red", 10), ("green", 6), ("gold", 4)]


@pytest.mark.parametrize("car_class", ["", None])
def test_class_must_be_a_non_empty_string(tel, car_class):
    with pytest.raises(ValueError):
        tel.add_car("white", car_class=car_class)
    assert "white" not in tel.get_cars()
    assert tel.get_classes() == ["pro", "amateur"]


def test_class_a_car_id_in_use_is_still_refused(tel):
    with pytest.raises(TelemetryError):
        tel.add_car("red", car_class="amateur")
    assert tel.get_car_class("red") == "pro"
    assert tel.get_cars(car_class="amateur") == ["blue", "pink"]


def test_class_of_an_unknown_car_raises_key_error(tel):
    with pytest.raises(KeyError):
        tel.get_car_class("white")
    with pytest.raises(KeyError):
        tel.get_car_class(None)
