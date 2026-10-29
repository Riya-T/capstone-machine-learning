"""Public checks for cooler.py.

Usage (with cooler.py importable, e.g. in the sandbox):
    python -m pytest public/test_cooler_public.py
"""

import pytest
from cooler import FlowerCooler


@pytest.fixture
def cooler():
    c = FlowerCooler()
    c.add_batch("tulips", 20, 3)
    c.add_batch("roses", 12, 0)
    return c


def test_a_new_batch_keeps_its_values(cooler):
    assert cooler.get_freshness("tulips") == 20
    assert cooler.get_days_left("tulips") == 3
    assert cooler.get_batches() == ["tulips", "roses"]


def test_a_day_costs_two_freshness_while_days_are_left(cooler):
    cooler.end_day()
    assert cooler.get_freshness("tulips") == 18
    assert cooler.get_days_left("tulips") == 2


def test_a_day_costs_five_freshness_once_no_days_are_left(cooler):
    cooler.end_day()
    assert cooler.get_freshness("roses") == 7
    assert cooler.get_days_left("roses") == -1


def test_freshness_stops_at_zero_and_the_batch_is_wilted(cooler):
    for _ in range(3):
        cooler.end_day()
    assert cooler.get_freshness("roses") == 0
    assert cooler.get_days_left("roses") == -3
    assert cooler.get_wilted() == ["roses"]


def test_freshness_must_be_in_range(cooler):
    with pytest.raises(ValueError):
        cooler.add_batch("lilies", -1, 2)
    assert cooler.get_batches() == ["tulips", "roses"]


def test_unknown_batches_raise_key_error(cooler):
    with pytest.raises(KeyError):
        cooler.get_freshness("daisies")
    with pytest.raises(KeyError):
        cooler.remove_batch("daisies")


def test_wilted_batches_are_listed_in_the_order_added():
    c = FlowerCooler()
    c.add_batch("asters", 6, 5)
    c.add_batch("daisies", 2, 5)
    c.add_batch("irises", 0, 5)
    assert c.get_wilted() == ["irises"]
    c.end_day()
    assert c.get_wilted() == ["daisies", "irises"]
    c.end_day()
    c.end_day()
    assert c.get_wilted() == ["asters", "daisies", "irises"]
