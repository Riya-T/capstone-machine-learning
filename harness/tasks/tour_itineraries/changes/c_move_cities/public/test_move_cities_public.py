"""Public checks for the c_move_cities change (moving several cities as one
call). Shown to the editor, never to the writer.

Usage (with tours.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move_cities/public/test_move_cities_public.py
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
    p.add_city("alps", "zurich")
    return p


def test_cities_move_in_the_order_of_the_list(planner):
    planner.move_cities("coast", "alps", ["lyon", "lisbon"])
    assert planner.get_cities("coast") == ["porto"]
    assert planner.get_cities("alps") == ["zurich", "lyon", "lisbon"]


def test_a_bad_city_means_nothing_moves(planner):
    with pytest.raises(TourError):
        planner.move_cities("coast", "alps", ["porto", "rome"])
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]
    assert planner.get_cities("alps") == ["zurich"]
