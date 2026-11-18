"""Hidden tests for the c_max_cities change (at most 8 cities per tour).
Never shown to the writer or the editor.

Usage (with tours.py importable, e.g. in the sandbox):
    python -m pytest changes/c_max_cities/private/test_max_cities_new.py
"""

import pytest
from tours import TourError, TourFull, TourPlanner

CITIES = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"]


@pytest.fixture
def planner():
    p = TourPlanner()
    for name in ["grand", "short", "other"]:
        p.add_tour(name)
    for city in CITIES:
        p.add_city("grand", city)  # grand is full
    for city in ["c1", "x1", "x2"]:
        p.add_city("short", city)
    return p


def state(p):
    return [(t, p.get_cities(t)) for t in p.get_tours()]


def test_tour_full_is_a_tour_error():
    assert issubclass(TourFull, TourError)


def test_add_city_on_a_full_tour_is_rejected(planner):
    before = state(planner)
    with pytest.raises(TourFull):
        planner.add_city("grand", "x1")
    assert state(planner) == before


def test_other_tours_are_not_affected(planner):
    planner.add_city("short", "x3")
    planner.add_city("other", "x1")
    assert planner.get_cities("short") == ["c1", "x1", "x2", "x3"]
    assert planner.get_cities("other") == ["x1"]


def test_removing_a_city_makes_room_again(planner):
    planner.remove_city("grand", "c3")
    planner.add_city("grand", "x1")
    assert planner.get_cities("grand") == ["c1", "c2", "c4", "c5", "c6", "c7", "c8", "x1"]
    with pytest.raises(TourFull):
        planner.add_city("grand", "x2")


def test_cancelling_a_city_makes_room_again(planner):
    assert planner.cancel_city("c1") == 2
    planner.add_city("grand", "c1")
    assert planner.get_cities("grand") == ["c2", "c3", "c4", "c5", "c6", "c7", "c8", "c1"]


def test_a_full_tour_still_works_otherwise(planner):
    planner.remove_city("grand", "c8")
    planner.add_city("grand", "c8")
    assert planner.cancel_city("c4") == 1
    assert len(planner.get_cities("grand")) == 7


def test_a_merge_that_would_overfill_first_is_rejected(planner):
    for city in ["y1", "y2", "y3", "y4", "y5", "y6"]:
        planner.add_city("other", city)
    before = state(planner)
    # short has 3 cities and other would add 6: 9
    with pytest.raises(TourFull):
        planner.merge_tours("short", "other")
    # grand is full and short would add x1 and x2 (c1 is skipped)
    with pytest.raises(TourFull):
        planner.merge_tours("grand", "short")
    assert state(planner) == before


def test_a_merge_that_fits_exactly_is_allowed():
    p = TourPlanner()
    p.add_tour("first")
    p.add_tour("second")
    for city in ["a", "b", "c", "d", "e"]:
        p.add_city("first", city)
    for city in ["f", "g", "h"]:
        p.add_city("second", city)
    assert p.merge_tours("first", "second") == 3
    assert p.get_cities("first") == ["a", "b", "c", "d", "e", "f", "g", "h"]
    assert p.get_tours() == ["first"]


def test_cities_first_already_has_do_not_count(planner):
    # grand is full, but every city of this tour is already on grand
    planner.add_city("other", "c2")
    planner.add_city("other", "c7")
    assert planner.merge_tours("grand", "other") == 0
    assert planner.get_tours() == ["grand", "short"]
    # 3 + 6 = 9 cities, but c1 is shared, so 8 fit
    p = TourPlanner()
    p.add_tour("first")
    p.add_tour("second")
    for city in ["c1", "a", "b"]:
        p.add_city("first", city)
    for city in ["c1", "d", "e", "f", "g", "h"]:
        p.add_city("second", city)
    assert p.merge_tours("first", "second") == 5
    assert p.get_cities("first") == ["c1", "a", "b", "d", "e", "f", "g", "h"]


def test_a_rejected_merge_keeps_second(planner):
    with pytest.raises(TourFull):
        planner.merge_tours("grand", "short")
    assert planner.get_tours() == ["grand", "short", "other"]
    planner.remove_city("grand", "c7")
    planner.remove_city("grand", "c8")
    assert planner.merge_tours("grand", "short") == 2
    assert planner.get_cities("grand") == CITIES[:6] + ["x1", "x2"]
    assert planner.get_tours() == ["grand", "other"]
