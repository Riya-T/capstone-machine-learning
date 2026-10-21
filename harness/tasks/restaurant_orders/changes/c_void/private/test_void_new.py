"""Hidden tests for the c_void change (voiding the most recent order). Never
shown to the writer or the editor.

Usage (with orders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_void/private/test_void_new.py
"""

import pytest
from orders import Restaurant, RestaurantError


@pytest.fixture
def rest():
    r = Restaurant()
    r.add_dish("soup", 650)
    r.add_dish("steak", 2400)
    r.add_dish("cake", 700)
    r.open_table("t1")
    r.open_table("t2")
    r.order("t1", "soup", 2)
    r.order("t1", "steak", 1)
    r.order("t1", "soup", 1)
    return r


def state(r):
    return {t: (r.get_order(t), r.get_bill(t), r.get_voided(t)) for t in r.get_open_tables()}


def test_voids_walk_back_one_call_at_a_time(rest):
    assert rest.void_last("t1") == ("soup", 1)
    assert rest.get_order("t1") == [("soup", 2), ("steak", 1)]
    assert rest.void_last("t1") == ("steak", 1)
    assert rest.get_order("t1") == [("soup", 2)]
    assert rest.void_last("t1") == ("soup", 2)
    assert rest.get_order("t1") == []
    assert rest.get_bill("t1") == 0


def test_the_bill_drops_by_the_voided_amount(rest):
    assert rest.get_bill("t1") == 3 * 650 + 2400
    rest.void_last("t1")
    assert rest.get_bill("t1") == 2 * 650 + 2400
    rest.void_last("t1")
    assert rest.get_bill("t1") == 2 * 650


def test_voided_calls_are_listed_in_voiding_order(rest):
    assert rest.get_voided("t1") == []
    rest.void_last("t1")
    rest.void_last("t1")
    assert rest.get_voided("t1") == [("soup", 1), ("steak", 1)]
    assert rest.get_voided("t2") == []


def test_only_part_of_a_dish_total_can_be_voided(rest):
    rest.void_last("t1")  # the second soup
    assert rest.get_order("t1") == [("soup", 2), ("steak", 1)]


def test_a_fully_voided_dish_comes_back_at_the_end(rest):
    rest.void_last("t1")
    rest.void_last("t1")
    rest.void_last("t1")  # table is now empty
    rest.order("t1", "cake", 1)
    rest.order("t1", "soup", 1)
    assert rest.get_order("t1") == [("cake", 1), ("soup", 1)]


def test_orders_after_a_void_can_be_voided_too(rest):
    rest.void_last("t1")
    rest.order("t1", "cake", 2)
    assert rest.void_last("t1") == ("cake", 2)
    assert rest.void_last("t1") == ("steak", 1)
    assert rest.get_order("t1") == [("soup", 2)]
    assert rest.get_voided("t1") == [("soup", 1), ("cake", 2), ("steak", 1)]


def test_voiding_everything_then_once_more_raises(rest):
    for _ in range(3):
        rest.void_last("t1")
    before = state(rest)
    with pytest.raises(RestaurantError):
        rest.void_last("t1")
    assert state(rest) == before


def test_an_empty_table_has_nothing_to_void(rest):
    before = state(rest)
    with pytest.raises(RestaurantError):
        rest.void_last("t2")
    assert state(rest) == before


@pytest.mark.parametrize("table", ["t9", None, 1])
def test_void_on_a_table_that_is_not_open_raises_key_error(rest, table):
    before = state(rest)
    with pytest.raises(KeyError):
        rest.void_last(table)
    with pytest.raises(KeyError):
        rest.get_voided(table)
    assert state(rest) == before


def test_a_closed_table_cannot_be_voided_and_reopens_clean(rest):
    rest.void_last("t1")
    rest.close_table("t1")
    with pytest.raises(KeyError):
        rest.void_last("t1")
    rest.open_table("t1")
    assert rest.get_voided("t1") == []
    with pytest.raises(RestaurantError):
        rest.void_last("t1")


def test_voids_on_one_table_leave_the_others_alone(rest):
    rest.order("t2", "cake", 1)
    rest.void_last("t1")
    assert rest.get_order("t2") == [("cake", 1)]
    assert rest.get_voided("t2") == []
