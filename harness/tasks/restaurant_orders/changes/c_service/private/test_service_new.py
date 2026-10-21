"""Hidden tests for the c_service change (service charge and takings). Never
shown to the writer or the editor.

Usage (with orders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_service/private/test_service_new.py
"""

import pytest
from orders import Restaurant


@pytest.fixture
def rest():
    r = Restaurant(service_percent=15)
    r.add_dish("soup", 650)
    r.add_dish("steak", 2400)
    r.add_dish("cake", 333)
    r.open_table("t1")
    r.open_table("t2")
    return r


def test_subtotal_is_the_plain_sum_of_the_order(rest):
    rest.order("t1", "soup", 2)
    rest.order("t1", "steak", 1)
    assert rest.get_subtotal("t1") == 3700
    assert rest.get_subtotal("t2") == 0


def test_the_service_charge_is_rounded_down(rest):
    rest.order("t1", "cake", 1)  # 333 * 15 / 100 = 49.95
    assert rest.get_service_charge("t1") == 49
    assert rest.get_bill("t1") == 382
    rest.order("t1", "cake", 1)  # 666 * 15 / 100 = 99.9
    assert rest.get_service_charge("t1") == 99
    assert rest.get_bill("t1") == 765


def test_an_empty_table_owes_nothing(rest):
    assert rest.get_service_charge("t1") == 0
    assert rest.get_bill("t1") == 0


def test_the_charge_follows_the_order_as_it_grows(rest):
    rest.order("t1", "soup", 1)
    assert rest.get_service_charge("t1") == 97
    rest.order("t1", "steak", 1)
    assert rest.get_service_charge("t1") == 457
    assert rest.get_bill("t1") == 3050 + 457


@pytest.mark.parametrize("percent", [-1, 2.5, "10", True, None])
def test_invalid_percentages_are_rejected(percent):
    with pytest.raises(ValueError):
        Restaurant(service_percent=percent)


def test_a_zero_percentage_charges_nothing():
    r = Restaurant(service_percent=0)
    r.add_dish("soup", 650)
    r.open_table("t1")
    r.order("t1", "soup", 3)
    r.close_table("t1")
    assert r.get_takings() == 1950


def test_takings_start_at_zero_and_ignore_open_tables(rest):
    rest.order("t1", "steak", 2)
    assert rest.get_takings() == 0


def test_closing_adds_the_full_bill_to_the_takings(rest):
    rest.order("t1", "soup", 2)
    rest.order("t2", "steak", 1)
    rest.close_table("t1")
    assert rest.get_takings() == 1300 + 195
    rest.close_table("t2")
    assert rest.get_takings() == 1300 + 195 + 2400 + 360


def test_each_sitting_of_a_table_counts_once(rest):
    rest.order("t1", "soup", 1)
    rest.close_table("t1")
    rest.open_table("t1")
    rest.order("t1", "steak", 1)
    assert rest.get_takings() == 650 + 97
    rest.close_table("t1")
    assert rest.get_takings() == 650 + 97 + 2400 + 360


def test_closing_an_empty_table_adds_nothing(rest):
    rest.close_table("t2")
    assert rest.get_takings() == 0


def test_later_orders_do_not_change_past_takings(rest):
    rest.order("t1", "soup", 1)
    rest.close_table("t1")
    rest.order("t2", "steak", 3)
    assert rest.get_takings() == 747


@pytest.mark.parametrize("table", ["t9", None, 1])
def test_subtotal_and_charge_need_an_open_table(rest, table):
    with pytest.raises(KeyError):
        rest.get_subtotal(table)
    with pytest.raises(KeyError):
        rest.get_service_charge(table)
    rest.close_table("t1")
    with pytest.raises(KeyError):
        rest.get_service_charge("t1")
