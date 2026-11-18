"""Hidden tests for the c_max_setting change (adjustable limit). Never shown
to the writer or the editor.

Usage (with tours.py importable, e.g. in the sandbox):
    python -m pytest changes/c_max_setting/private/test_max_setting_new.py
"""

import pytest
from tours import TourFull, TourPlanner


def make(**kwargs):
    p = TourPlanner(**kwargs)
    for name in ["coast", "alps", "lakes"]:
        p.add_tour(name)
    for city in ["lisbon", "porto", "lyon"]:
        p.add_city("coast", city)
    return p


def state(p):
    return [(t, p.get_cities(t), p.get_max_cities(t)) for t in p.get_tours()]


def fill(p, tour, count, prefix="c"):
    for i in range(count):
        p.add_city(tour, f"{prefix}{i}")


# --- the planner's value --------------------------------------------------------


def test_every_new_tour_starts_with_8_by_default():
    p = make()
    assert [p.get_max_cities(t) for t in p.get_tours()] == [8, 8, 8]


def test_every_new_tour_starts_with_the_planner_value():
    p = make(max_cities=5)
    assert [p.get_max_cities(t) for t in p.get_tours()] == [5, 5, 5]
    fill(p, "alps", 5)
    with pytest.raises(TourFull):
        p.add_city("alps", "extra")
    assert len(p.get_cities("alps")) == 5


def test_none_means_no_limit():
    p = make(max_cities=None)
    assert p.get_max_cities("alps") is None
    fill(p, "alps", 12)
    assert len(p.get_cities("alps")) == 12


def test_a_larger_planner_value():
    p = make(max_cities=10)
    fill(p, "lakes", 10)
    with pytest.raises(TourFull):
        p.add_city("lakes", "extra")


@pytest.mark.parametrize("value", [0, -2, "8", 2.5])
def test_invalid_planner_values_are_rejected(value):
    with pytest.raises(ValueError):
        TourPlanner(max_cities=value)


# --- one tour's limit -------------------------------------------------------------


def test_set_max_cities_changes_only_that_tour():
    p = make()
    p.set_max_cities("alps", 3)
    assert [p.get_max_cities(t) for t in p.get_tours()] == [8, 3, 8]
    p.set_max_cities("alps", None)
    assert p.get_max_cities("alps") is None
    p.set_max_cities("alps", 12)
    assert p.get_max_cities("alps") == 12


def test_a_tour_limit_applies_to_add_city():
    p = make()
    p.set_max_cities("alps", 2)
    p.add_city("alps", "zurich")
    p.add_city("alps", "milan")
    with pytest.raises(TourFull):
        p.add_city("alps", "lyon")
    assert p.get_cities("alps") == ["zurich", "milan"]
    p.set_max_cities("alps", 3)
    p.add_city("alps", "lyon")
    assert p.get_cities("alps") == ["zurich", "milan", "lyon"]


def test_a_tour_without_a_limit_takes_more_than_8():
    p = make()
    p.set_max_cities("lakes", None)
    fill(p, "lakes", 11)
    assert len(p.get_cities("lakes")) == 11
    fill(p, "alps", 8)
    with pytest.raises(TourFull):
        p.add_city("alps", "extra")


def test_a_limit_equal_to_the_number_of_cities_is_allowed():
    p = make()
    p.set_max_cities("coast", 3)
    with pytest.raises(TourFull):
        p.add_city("coast", "rome")


@pytest.mark.parametrize("value", [0, -1, "3", 1.5])
def test_invalid_tour_limits_are_rejected(value):
    p = make()
    p.set_max_cities("alps", 4)
    with pytest.raises(ValueError):
        p.set_max_cities("alps", value)
    assert p.get_max_cities("alps") == 4


def test_a_limit_below_the_number_of_cities_is_rejected():
    p = make()
    before = state(p)
    with pytest.raises(ValueError):
        p.set_max_cities("coast", 2)
    assert state(p) == before


def test_tours_not_in_use_raise_key_error():
    p = make()
    p.merge_tours("coast", "lakes")
    for call in (
        lambda: p.set_max_cities("nordic", 3),
        lambda: p.get_max_cities("nordic"),
        lambda: p.set_max_cities("lakes", 3),
        lambda: p.get_max_cities("lakes"),
    ):
        with pytest.raises(KeyError):
            call()


def test_a_tour_added_again_does_not_keep_the_old_limit():
    p = make()
    p.set_max_cities("lakes", 2)
    p.merge_tours("coast", "lakes")
    p.add_tour("lakes")
    assert p.get_max_cities("lakes") == 8
    p = make(max_cities=4)
    p.set_max_cities("lakes", None)
    p.merge_tours("alps", "lakes")
    p.add_tour("lakes")
    assert p.get_max_cities("lakes") == 4


# --- merging --------------------------------------------------------------------


def test_merge_uses_the_limit_of_first():
    p = make()
    p.set_max_cities("coast", 5)
    p.add_city("alps", "zurich")
    p.add_city("alps", "milan")
    p.add_city("alps", "geneva")
    before = state(p)
    with pytest.raises(TourFull):
        p.merge_tours("coast", "alps")
    assert state(p) == before
    p.set_max_cities("coast", 6)
    assert p.merge_tours("coast", "alps") == 3
    assert p.get_cities("coast") == ["lisbon", "porto", "lyon", "zurich", "milan", "geneva"]


def test_the_limit_of_second_does_not_matter():
    p = make()
    p.set_max_cities("coast", 4)
    p.set_max_cities("alps", 1)
    p.add_city("alps", "zurich")
    assert p.merge_tours("coast", "alps") == 1
    assert p.get_cities("coast") == ["lisbon", "porto", "lyon", "zurich"]
    assert p.get_max_cities("coast") == 4


def test_a_merge_into_a_tour_without_a_limit():
    p = make()
    p.set_max_cities("lakes", None)
    fill(p, "lakes", 7)
    assert p.merge_tours("lakes", "coast") == 3
    assert len(p.get_cities("lakes")) == 10
