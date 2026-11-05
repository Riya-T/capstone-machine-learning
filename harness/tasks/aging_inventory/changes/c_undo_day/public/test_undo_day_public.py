"""Public checks for the c_undo_day change (taking back ended days). Shown to
the editor, never to the writer.

Usage (with cooler.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo_day/public/test_undo_day_public.py
"""

import pytest
from cooler import CoolerError, FlowerCooler


@pytest.fixture
def cooler():
    c = FlowerCooler()
    c.add_batch("tulips", 20, 3)
    c.add_batch("roses", 3, 0)
    return c


def test_undo_day_restores_the_values(cooler):
    cooler.end_day()
    assert cooler.get_day() == 1
    cooler.undo_day()
    assert cooler.get_day() == 0
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (20, 3)


def test_undo_day_brings_back_a_wilted_batch(cooler):
    cooler.end_day()
    assert cooler.get_wilted() == ["roses"]
    cooler.undo_day()
    assert cooler.get_freshness("roses") == 3
    assert cooler.get_wilted() == []


def test_undo_day_needs_a_day_to_take_back(cooler):
    with pytest.raises(CoolerError):
        cooler.undo_day()


def test_undo_day_leaves_batches_added_since_that_day(cooler):
    cooler.end_day()
    cooler.add_batch("lilies", 15, 4)
    cooler.remove_batch("roses")
    cooler.add_batch("roses", 9, 2)  # a new batch that reuses the id
    cooler.undo_day()
    assert cooler.get_batches() == ["tulips", "lilies", "roses"]
    assert (cooler.get_freshness("lilies"), cooler.get_days_left("lilies")) == (15, 4)
    assert (cooler.get_freshness("roses"), cooler.get_days_left("roses")) == (9, 2)
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (20, 3)
