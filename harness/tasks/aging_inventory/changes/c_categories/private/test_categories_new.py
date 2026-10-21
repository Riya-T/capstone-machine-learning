"""Hidden tests for the c_categories change (batch categories). Never shown
to the writer or the editor.

Usage (with cooler.py importable, e.g. in the sandbox):
    python -m pytest changes/c_categories/private/test_categories_new.py
"""

import pytest
from cooler import CoolerError, FlowerCooler


@pytest.fixture
def cooler():
    c = FlowerCooler()
    c.add_category("greens", daily_loss=1, late_loss=1)
    c.add_category("roses")
    c.add_batch("fern", 20, 1, category="greens")
    c.add_batch("red", 12, 0, category="roses")
    c.add_batch("tulips", 20, 3)
    c.add_batch("ivy", 10, 0, category="greens")
    return c


def state(c):
    batches = {
        b: (c.get_freshness(b), c.get_days_left(b), c.get_losses(b), c.get_category(b))
        for b in c.get_batches()
    }
    return batches, c.get_categories()


def test_categories_start_empty():
    c = FlowerCooler()
    assert c.get_categories() == []
    c.add_batch("a", 10, 1)
    assert c.get_category("a") is None


def test_categories_are_listed_in_the_order_added(cooler):
    cooler.add_category("bulbs")
    assert cooler.get_categories() == ["greens", "roses", "bulbs"]


def test_categories_without_losses_use_the_cooler_values():
    c = FlowerCooler(daily_loss=3, late_loss=4)
    c.add_category("x", late_loss=1)
    c.add_category("y")
    c.add_batch("a", 20, 1, category="x")
    c.add_batch("b", 20, 1, category="y")
    assert c.get_losses("a") == (3, 1)
    assert c.get_losses("b") == (3, 4)
    c.end_day()
    c.end_day()
    assert (c.get_freshness("a"), c.get_freshness("b")) == (16, 13)


def test_categories_losses_are_used_by_end_day(cooler):
    cooler.end_day()
    cooler.end_day()
    assert state(cooler)[0] == {
        "fern": (18, -1, (1, 1), "greens"),
        "red": (2, -2, (2, 5), "roses"),
        "tulips": (16, 1, (2, 5), None),
        "ivy": (8, -2, (1, 1), "greens"),
    }


def test_categories_batch_values_come_before_category_values(cooler):
    cooler.add_batch("moss", 20, 2, daily_loss=6, category="greens")
    assert cooler.get_losses("moss") == (6, 1)
    cooler.set_losses("fern", 0, 0)
    assert cooler.get_losses("fern") == (0, 0)
    cooler.end_day()
    assert cooler.get_freshness("moss") == 14
    assert cooler.get_freshness("fern") == 20
    assert cooler.get_losses("ivy") == (1, 1)


@pytest.mark.parametrize("name", ["", 5, None])
def test_categories_bad_names_are_rejected(cooler, name):
    before = state(cooler)
    with pytest.raises(ValueError):
        cooler.add_category(name)
    assert state(cooler) == before


@pytest.mark.parametrize("bad", [-1, 1.5, "1", True])
@pytest.mark.parametrize("which", ["daily_loss", "late_loss"])
def test_categories_bad_losses_are_rejected(cooler, which, bad):
    before = state(cooler)
    with pytest.raises(ValueError):
        cooler.add_category("bulbs", **{which: bad})
    assert state(cooler) == before


def test_categories_cannot_be_added_twice(cooler):
    before = state(cooler)
    with pytest.raises(CoolerError):
        cooler.add_category("greens", daily_loss=3)
    with pytest.raises(ValueError):
        cooler.add_category("greens", daily_loss=-3)  # bad value before the repeated name
    assert state(cooler) == before
    assert cooler.get_losses("fern") == (1, 1)


def test_categories_add_batch_errors_come_in_order(cooler):
    before = state(cooler)
    with pytest.raises(ValueError):
        cooler.add_batch("moss", 31, 2, category="mosses")  # bad value first
    with pytest.raises(KeyError):
        cooler.add_batch("fern", 10, 2, category="mosses")  # unknown category before repeated id
    with pytest.raises(CoolerError):
        cooler.add_batch("fern", 10, 2, category="roses")
    assert state(cooler) == before


def test_categories_filter_batches_and_wilted(cooler):
    assert cooler.get_batches(category="greens") == ["fern", "ivy"]
    assert cooler.get_batches(category=None) == ["fern", "red", "tulips", "ivy"]
    cooler.add_category("bulbs")
    assert cooler.get_batches(category="bulbs") == []
    for _ in range(3):
        cooler.end_day()
    assert cooler.get_wilted() == ["red"]
    assert cooler.get_wilted(category="roses") == ["red"]
    assert cooler.get_wilted(category="greens") == []
    assert cooler.get_wilted(category="bulbs") == []


def test_categories_unknown_names_raise_key_error(cooler):
    with pytest.raises(KeyError):
        cooler.get_batches(category="mosses")
    with pytest.raises(KeyError):
        cooler.get_wilted(category="mosses")
    with pytest.raises(KeyError):
        cooler.get_category("asters")
    empty = FlowerCooler()
    with pytest.raises(KeyError):
        empty.get_batches(category="mosses")


def test_categories_a_re_added_batch_takes_its_new_category(cooler):
    cooler.remove_batch("fern")
    cooler.add_batch("fern", 20, 1, category="roses")
    assert cooler.get_category("fern") == "roses"
    assert cooler.get_losses("fern") == (2, 5)
    assert cooler.get_batches(category="greens") == ["ivy"]
