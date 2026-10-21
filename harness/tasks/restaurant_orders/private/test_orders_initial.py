"""Hidden tests for the initial restaurant_orders spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with orders.py importable, e.g. in the sandbox):
    python -m pytest private/test_orders_initial.py
"""

import pytest
from orders import Restaurant, RestaurantError

BAD_COUNTS = [0, -3, 1.5, "2", None]


@pytest.fixture
def rest():
    r = Restaurant()
    r.add_dish("soup", 650)
    r.add_dish("steak", 2400)
    r.add_dish("cake", 700)
    r.open_table("t1")
    r.open_table("t2")
    return r


def state(r):
    """Every open table's order and bill, to check that a failed call changed nothing."""
    return {t: (r.get_order(t), r.get_bill(t)) for t in r.get_open_tables()}


# --- menu -------------------------------------------------------------------


def test_dishes_on_the_menu_can_be_ordered(rest):
    rest.order("t1", "cake", 1)
    assert rest.get_bill("t1") == 700


@pytest.mark.parametrize("name", [""])
def test_empty_dish_names_are_rejected(rest, name):
    with pytest.raises(ValueError):
        rest.add_dish(name, 100)
    with pytest.raises(KeyError):
        rest.order("t1", name, 1)


@pytest.mark.parametrize("price", BAD_COUNTS)
def test_invalid_prices_are_rejected(rest, price):
    with pytest.raises(ValueError):
        rest.add_dish("pie", price)
    with pytest.raises(KeyError):
        rest.order("t1", "pie", 1)


def test_adding_a_dish_twice_is_rejected_and_keeps_the_price(rest):
    with pytest.raises(RestaurantError):
        rest.add_dish("soup", 900)
    rest.order("t1", "soup", 1)
    assert rest.get_bill("t1") == 650


def test_a_bad_price_is_reported_before_a_duplicate_name(rest):
    with pytest.raises(ValueError):
        rest.add_dish("soup", 0)


# --- tables -----------------------------------------------------------------


def test_a_new_table_has_nothing_ordered(rest):
    assert rest.get_order("t1") == []
    assert rest.get_bill("t1") == 0


def test_open_tables_are_listed_in_opening_order():
    r = Restaurant()
    for table in ["t3", "t1", "t2"]:
        r.open_table(table)
    assert r.get_open_tables() == ["t3", "t1", "t2"]


@pytest.mark.parametrize("table", [""])
def test_empty_table_names_are_rejected(rest, table):
    with pytest.raises(ValueError):
        rest.open_table(table)
    assert rest.get_open_tables() == ["t1", "t2"]


def test_opening_an_open_table_is_rejected_and_keeps_its_order(rest):
    rest.order("t1", "soup", 2)
    with pytest.raises(RestaurantError):
        rest.open_table("t1")
    assert rest.get_order("t1") == [("soup", 2)]
    assert rest.get_open_tables() == ["t1", "t2"]


def test_closing_removes_the_table_from_the_open_list(rest):
    rest.close_table("t1")
    assert rest.get_open_tables() == ["t2"]
    rest.close_table("t2")
    assert rest.get_open_tables() == []


def test_a_table_with_nothing_ordered_can_be_closed(rest):
    rest.close_table("t2")
    assert rest.get_open_tables() == ["t1"]


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.order("t1", "soup", 1),
        lambda r: r.get_order("t1"),
        lambda r: r.get_bill("t1"),
        lambda r: r.close_table("t1"),
    ],
)
def test_a_closed_table_is_treated_as_not_open(rest, call):
    rest.order("t1", "soup", 1)
    rest.close_table("t1")
    with pytest.raises(KeyError):
        call(rest)
    assert rest.get_open_tables() == ["t2"]


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.order("t9", "soup", 1),
        lambda r: r.get_order("t9"),
        lambda r: r.get_bill("t9"),
        lambda r: r.close_table("t9"),
        lambda r: r.get_bill(None),
        lambda r: r.get_order(1),
        lambda r: r.close_table(None),
    ],
)
def test_tables_that_were_never_opened_raise_key_error(rest, call):
    rest.order("t1", "soup", 1)
    before = state(rest)
    with pytest.raises(KeyError):
        call(rest)
    assert state(rest) == before


def test_a_reopened_table_starts_empty_and_goes_last(rest):
    rest.order("t1", "steak", 2)
    rest.close_table("t1")
    rest.open_table("t1")
    assert rest.get_open_tables() == ["t2", "t1"]
    assert rest.get_order("t1") == []
    assert rest.get_bill("t1") == 0


# --- orders -----------------------------------------------------------------


def test_each_dish_is_listed_once_in_first_ordered_order(rest):
    rest.order("t1", "cake", 1)
    rest.order("t1", "soup", 2)
    rest.order("t1", "cake", 3)
    rest.order("t1", "steak", 1)
    rest.order("t1", "soup", 1)
    assert rest.get_order("t1") == [("cake", 4), ("soup", 3), ("steak", 1)]


def test_the_bill_sums_quantity_times_price(rest):
    rest.order("t1", "soup", 3)
    rest.order("t1", "steak", 2)
    rest.order("t1", "soup", 1)
    assert rest.get_bill("t1") == 4 * 650 + 2 * 2400


def test_tables_keep_separate_orders(rest):
    rest.order("t1", "soup", 1)
    rest.order("t2", "steak", 1)
    assert rest.get_order("t1") == [("soup", 1)]
    assert rest.get_order("t2") == [("steak", 1)]
    assert (rest.get_bill("t1"), rest.get_bill("t2")) == (650, 2400)


@pytest.mark.parametrize("quantity", BAD_COUNTS)
def test_invalid_quantities_are_rejected(rest, quantity):
    rest.order("t1", "soup", 1)
    before = state(rest)
    with pytest.raises(ValueError):
        rest.order("t1", "steak", quantity)
    assert state(rest) == before


@pytest.mark.parametrize("dish", ["pizza", None, 3])
def test_dishes_not_on_the_menu_are_rejected(rest, dish):
    rest.order("t1", "soup", 1)
    before = state(rest)
    with pytest.raises(KeyError):
        rest.order("t1", dish, 1)
    assert state(rest) == before


def test_a_missing_table_or_dish_is_reported_before_a_bad_quantity(rest):
    with pytest.raises(KeyError):
        rest.order("t9", "soup", 0)
    with pytest.raises(KeyError):
        rest.order("t1", "pizza", -1)


def test_failed_orders_add_nothing(rest):
    rest.order("t1", "soup", 1)
    for call in (
        lambda: rest.order("t1", "soup", 0),
        lambda: rest.order("t1", "pizza", 1),
        lambda: rest.order("t9", "soup", 1),
    ):
        with pytest.raises((ValueError, KeyError)):
            call()
    assert rest.get_order("t1") == [("soup", 1)]
    assert rest.get_bill("t1") == 650


def test_restaurants_do_not_share_menus_or_tables():
    first, second = Restaurant(), Restaurant()
    first.add_dish("soup", 650)
    first.open_table("t1")
    assert second.get_open_tables() == []
    second.open_table("t1")
    with pytest.raises(KeyError):
        second.order("t1", "soup", 1)
