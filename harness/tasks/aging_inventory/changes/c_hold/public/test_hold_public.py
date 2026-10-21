"""Public checks for the c_hold change (batches on hold). Shown to the
editor, never to the writer.

Usage (with cooler.py importable, e.g. in the sandbox):
    python -m pytest changes/c_hold/public/test_hold_public.py
"""

import pytest
from cooler import BatchHeld, FlowerCooler


@pytest.fixture
def cooler():
    c = FlowerCooler()
    c.add_batch("tulips", 20, 3)
    c.add_batch("roses", 12, 0)
    return c


def test_hold_stops_a_batch_from_ageing(cooler):
    cooler.hold("tulips")
    cooler.end_day()
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (20, 3)
    assert cooler.get_freshness("roses") == 7
    cooler.release("tulips")
    cooler.end_day()
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (18, 2)


def test_hold_blocks_removal(cooler):
    cooler.hold("roses")
    with pytest.raises(BatchHeld):
        cooler.remove_batch("roses")
    assert cooler.get_batches() == ["tulips", "roses"]


def test_hold_list_and_flag(cooler):
    assert cooler.is_held("tulips") is False
    cooler.hold("roses")
    assert cooler.is_held("roses") is True
    assert cooler.get_held() == ["roses"]
