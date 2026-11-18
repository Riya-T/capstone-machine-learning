"""Public checks for tours.py.

Usage (with tours.py importable, e.g. in the sandbox):
    python -m pytest public/test_tours_public.py
"""

import pytest
from tours import TourError, TourPlanner


@pytest.fixture
def planner():
    p = TourPlanner()
    p.add_tour("coast")
    p.add_tour("alps")
    for city in ["lisbon", "porto", "lyon"]:
        p.add_city("coast", city)
    for city in ["zurich", "lyon"]:
        p.add_city("alps", city)
    return p


def test_tours_and_cities_are_listed_in_order(planner):
    assert planner.get_tours() == ["coast", "alps"]
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]
    assert planner.get_cities("alps") == ["zurich", "lyon"]


def test_a_city_is_on_a_tour_at_most_once(planner):
    with pytest.raises(TourError):
        planner.add_city("coast", "porto")
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]


def test_remove_city_keeps_the_order_of_the_others(planner):
    planner.remove_city("coast", "porto")
    assert planner.get_cities("coast") == ["lisbon", "lyon"]


def test_cancel_city_removes_it_from_every_tour(planner):
    assert planner.cancel_city("lyon") == 2
    assert planner.get_cities("coast") == ["lisbon", "porto"]
    assert planner.get_cities("alps") == ["zurich"]
    assert planner.cancel_city("rome") == 0


def test_merge_tours_appends_the_new_cities_and_removes_the_second(planner):
    assert planner.merge_tours("coast", "alps") == 1
    assert planner.get_tours() == ["coast"]
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon", "zurich"]
    with pytest.raises(KeyError):
        planner.get_cities("alps")
