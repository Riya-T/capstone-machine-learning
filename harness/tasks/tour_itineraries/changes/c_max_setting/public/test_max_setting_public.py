"""Public checks for the c_max_setting change (adjustable limit). Shown to
the editor, never to the writer.

Usage (with tours.py importable, e.g. in the sandbox):
    python -m pytest changes/c_max_setting/public/test_max_setting_public.py
"""

import pytest
from tours import TourFull, TourPlanner


def test_the_limit_is_8_by_default():
    p = TourPlanner()
    p.add_tour("coast")
    assert p.get_max_cities("coast") == 8


def test_a_planner_with_a_smaller_limit():
    p = TourPlanner(max_cities=2)
    p.add_tour("coast")
    p.add_city("coast", "lisbon")
    p.add_city("coast", "porto")
    with pytest.raises(TourFull):
        p.add_city("coast", "lyon")
    assert p.get_cities("coast") == ["lisbon", "porto"]


def test_one_tour_can_get_its_own_limit():
    p = TourPlanner()
    p.add_tour("coast")
    p.set_max_cities("coast", None)
    assert p.get_max_cities("coast") is None
