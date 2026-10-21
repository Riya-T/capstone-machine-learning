"""Hidden tests for the c_car_classes change (car classes). Never shown to
the writer or the editor.

Usage (with telemetry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_car_classes/private/test_car_classes_new.py
"""

import pytest
from telemetry import RaceTelemetry, TelemetryError

CARS = [("red", "pro"), ("blue", "amateur"), ("green", "pro"), ("pink", "amateur"), ("gold", "pro")]


@pytest.fixture
def tel():
    t = RaceTelemetry()
    for car, car_class in CARS:
        t.add_car(car, car_class=car_class)
    t.add_race("spa", 1)
    t.add_race("finale", 1, points_table=[20, 12, 8])
    return t


def run(t, race, order):
    """Finish a one-lap race with the cars in `order`, fastest first."""
    for i, car in enumerate(order):
        t.record_lap(race, car, 90000 + 100 * i)


def test_class_default_is_open():
    t = RaceTelemetry()
    t.add_car("red")
    t.add_car("blue", car_class="pro")
    assert t.get_car_class("red") == "open"
    assert t.get_classes() == ["open", "pro"]
    assert t.get_cars() == ["red", "blue"]


def test_class_of_each_car(tel):
    assert [tel.get_car_class(c) for c, _ in CARS] == [k for _, k in CARS]
    assert tel.get_classes() == ["pro", "amateur"]


def test_class_filter_on_cars(tel):
    assert tel.get_cars(car_class="pro") == ["red", "green", "gold"]
    assert tel.get_cars(car_class="amateur") == ["blue", "pink"]
    assert tel.get_cars(car_class="rookie") == []
    assert tel.get_cars(car_class=None) == ["red", "blue", "green", "pink", "gold"]


def test_class_filter_on_results(tel):
    run(tel, "spa", ["pink", "gold", "blue", "red"])  # green has not finished
    assert tel.get_results("spa") == ["pink", "gold", "blue", "red"]
    assert tel.get_results("spa", car_class="pro") == ["gold", "red"]
    assert tel.get_results("spa", car_class="amateur") == ["pink", "blue"]
    assert tel.get_results("spa", car_class="rookie") == []


def test_class_points_use_places_within_the_class(tel):
    run(tel, "spa", ["pink", "gold", "blue", "red", "green"])
    assert [tel.get_class_points(c) for c, _ in CARS] == [6, 6, 4, 10, 10]
    assert [tel.get_points(c) for c, _ in CARS] == [3, 4, 2, 10, 6]


def test_class_points_use_each_race_table(tel):
    run(tel, "spa", ["red", "blue", "green"])
    run(tel, "finale", ["green", "pink", "red", "blue"])
    # spa: pro red 1st, green 2nd; amateur blue 1st.
    # finale: pro green 1st, red 2nd; amateur pink 1st, blue 2nd.
    assert tel.get_class_points("red") == 10 + 12
    assert tel.get_class_points("green") == 6 + 20
    assert tel.get_class_points("blue") == 10 + 12
    assert tel.get_class_points("pink") == 20
    assert tel.get_class_points("gold") == 0


def test_class_ties_keep_the_order_cars_were_added(tel):
    for car in ["gold", "green", "red"]:
        tel.record_lap("spa", car, 90000)
    assert tel.get_results("spa", car_class="pro") == ["red", "green", "gold"]
    assert [tel.get_class_points(c) for c in ["red", "green", "gold"]] == [10, 6, 4]


@pytest.mark.parametrize("car_class", ["", None, 3])
def test_class_must_be_a_non_empty_string(tel, car_class):
    with pytest.raises(ValueError):
        tel.add_car("white", car_class=car_class)
    assert "white" not in tel.get_cars()


def test_class_errors_come_before_a_car_id_in_use(tel):
    with pytest.raises(ValueError):
        tel.add_car("red", car_class="")
    with pytest.raises(TelemetryError):
        tel.add_car("red", car_class="amateur")
    assert tel.get_car_class("red") == "pro"
    assert tel.get_classes() == ["pro", "amateur"]


def test_class_methods_raise_key_error_for_unknown_ids(tel):
    with pytest.raises(KeyError):
        tel.get_car_class("white")
    with pytest.raises(KeyError):
        tel.get_class_points(None)
    with pytest.raises(KeyError):
        tel.get_results("imola", car_class="pro")
