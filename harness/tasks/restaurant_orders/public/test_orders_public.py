"""Public checks for orders.py.

Usage (with orders.py importable, e.g. in the sandbox):
    python -m pytest public/test_orders_public.py
"""

import pytest
from orders import Restaurant


@pytest.fixture
def rest():
    r = Restaurant()
    r.add_dish("soup", 650)
    r.add_dish("steak", 2400)
    r.open_table("t1")
    r.open_table("t2")
    return r


def test_bill_adds_up_prices_times_quantities(rest):
    rest.order("t1", "soup", 2)
    rest.order("t1", "steak", 1)
    assert rest.get_bill("t1") == 3700
    assert rest.get_bill("t2") == 0


def test_repeated_orders_of_a_dish_are_added_together(rest):
    rest.order("t1", "steak", 1)
    rest.order("t1", "soup", 1)
    rest.order("t1", "steak", 2)
    assert rest.get_order("t1") == [("steak", 3), ("soup", 1)]


def test_a_closed_table_is_no_longer_open(rest):
    rest.order("t1", "soup", 1)
    rest.close_table("t1")
    assert rest.get_open_tables() == ["t2"]
    with pytest.raises(KeyError):
        rest.get_bill("t1")


def test_a_table_can_be_opened_again_after_closing(rest):
    rest.order("t1", "soup", 1)
    rest.close_table("t1")
    rest.open_table("t1")
    assert rest.get_open_tables() == ["t2", "t1"]
    assert rest.get_order("t1") == []


def test_quantities_must_be_positive(rest):
    with pytest.raises(ValueError):
        rest.order("t1", "soup", 0)
    with pytest.raises(ValueError):
        rest.order("t1", "soup", -2)
    assert rest.get_order("t1") == []


def test_unknown_tables_and_dishes_raise_key_error(rest):
    with pytest.raises(KeyError):
        rest.order("t9", "soup", 1)
    with pytest.raises(KeyError):
        rest.order("t1", "pizza", 1)
