"""Public checks for the c_max_cities change (at most 8 cities per tour).
Shown to the editor, never to the writer.

Usage (with tours.py importable, e.g. in the sandbox):
    python -m pytest changes/c_max_cities/public/test_max_cities_public.py
"""

import pytest
from tours import TourFull, TourPlanner

EIGHT = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"]


def test_a_tour_takes_eight_cities_but_not_nine():
    p = TourPlanner()
    p.add_tour("grand")
    for city in EIGHT:
        p.add_city("grand", city)
    with pytest.raises(TourFull):
        p.add_city("grand", "c9")
    assert p.get_cities("grand") == EIGHT


def test_a_merge_that_would_go_over_eight_is_rejected():
    p = TourPlanner()
    p.add_tour("grand")
    p.add_tour("extra")
    for city in EIGHT[:7]:
        p.add_city("grand", city)
    p.add_city("extra", "x1")
    p.add_city("extra", "x2")
    with pytest.raises(TourFull):
        p.merge_tours("grand", "extra")
    assert p.get_tours() == ["grand", "extra"]
    assert p.get_cities("grand") == EIGHT[:7]
