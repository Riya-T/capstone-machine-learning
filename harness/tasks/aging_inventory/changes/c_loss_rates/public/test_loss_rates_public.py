"""Public checks for the c_loss_rates change (adjustable freshness losses).
Shown to the editor, never to the writer.

Usage (with cooler.py importable, e.g. in the sandbox):
    python -m pytest changes/c_loss_rates/public/test_loss_rates_public.py
"""

import pytest
from cooler import FlowerCooler


def test_losses_for_the_whole_cooler():
    c = FlowerCooler(daily_loss=1, late_loss=3)
    c.add_batch("tulips", 20, 1)
    assert c.get_losses("tulips") == (1, 3)
    c.end_day()
    assert c.get_freshness("tulips") == 19
    c.end_day()
    assert c.get_freshness("tulips") == 16


def test_losses_for_one_batch():
    c = FlowerCooler()
    c.add_batch("ferns", 20, 2, daily_loss=4)
    c.add_batch("roses", 20, 2)
    assert c.get_losses("ferns") == (4, 5)
    c.end_day()
    assert c.get_freshness("ferns") == 16
    assert c.get_freshness("roses") == 18


def test_losses_must_not_be_negative():
    with pytest.raises(ValueError):
        FlowerCooler(daily_loss=-1)
    c = FlowerCooler()
    with pytest.raises(ValueError):
        c.add_batch("ferns", 20, 2, late_loss=-2)
    assert c.get_batches() == []
