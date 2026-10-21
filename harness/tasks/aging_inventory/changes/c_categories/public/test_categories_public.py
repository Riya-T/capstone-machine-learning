"""Public checks for the c_categories change (batch categories). Shown to the
editor, never to the writer.

Usage (with cooler.py importable, e.g. in the sandbox):
    python -m pytest changes/c_categories/public/test_categories_public.py
"""

import pytest
from cooler import FlowerCooler


@pytest.fixture
def cooler():
    c = FlowerCooler()
    c.add_category("greens", daily_loss=1)
    c.add_batch("fern", 20, 3, category="greens")
    c.add_batch("roses", 20, 3)
    return c


def test_categories_set_the_losses_of_their_batches(cooler):
    assert cooler.get_category("fern") == "greens"
    assert cooler.get_losses("fern") == (1, 5)
    cooler.end_day()
    assert cooler.get_freshness("fern") == 19
    assert cooler.get_freshness("roses") == 18


def test_categories_filter_the_batch_list(cooler):
    assert cooler.get_categories() == ["greens"]
    assert cooler.get_batches(category="greens") == ["fern"]
    assert cooler.get_batches() == ["fern", "roses"]


def test_categories_must_exist_before_use(cooler):
    with pytest.raises(KeyError):
        cooler.add_batch("moss", 10, 2, category="mosses")
    assert cooler.get_batches() == ["fern", "roses"]
