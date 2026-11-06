"""Public checks for the c_void change (voiding the most recent order). Shown
to the editor, never to the writer.

Usage (with orders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_void/public/test_void_public.py
"""

import pytest
from orders import Restaurant, RestaurantError


def test_voiding_removes_the_most_recent_order():
    r = Restaurant()
    r.add_dish("soup", 650)
    r.add_dish("steak", 2400)
    r.open_table("t1")
    r.order("t1", "soup", 2)
    r.order("t1", "steak", 1)
    assert r.void_last("t1") == ("steak", 1)
    assert r.get_order("t1") == [("soup", 2)]
    assert r.get_bill("t1") == 1300
    assert r.get_voided("t1") == [("steak", 1)]


def test_voiding_takes_back_one_call_not_the_whole_dish():
    r = Restaurant()
    r.add_dish("soup", 650)
    r.add_dish("cake", 700)
    r.open_table("t1")
    r.order("t1", "soup", 1)
    r.order("t1", "cake", 2)
    r.order("t1", "soup", 3)
    assert r.void_last("t1") == ("soup", 3)
    assert r.get_order("t1") == [("soup", 1), ("cake", 2)]
    assert r.get_bill("t1") == 650 + 1400


def test_a_dish_voided_away_and_ordered_again_goes_last():
    r = Restaurant()
    r.add_dish("soup", 650)
    r.add_dish("cake", 700)
    r.open_table("t1")
    r.order("t1", "soup", 1)
    r.void_last("t1")
    r.order("t1", "cake", 2)
    r.order("t1", "soup", 1)
    assert r.get_order("t1") == [("cake", 2), ("soup", 1)]
    assert r.get_bill("t1") == 1400 + 650


def test_nothing_left_to_void_raises():
    r = Restaurant()
    r.open_table("t1")
    with pytest.raises(RestaurantError):
        r.void_last("t1")
    assert r.get_voided("t1") == []
