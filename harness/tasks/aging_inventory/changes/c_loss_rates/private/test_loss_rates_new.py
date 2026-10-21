"""Hidden tests for the c_loss_rates change (adjustable freshness losses).
Never shown to the writer or the editor.

Usage (with cooler.py importable, e.g. in the sandbox):
    python -m pytest changes/c_loss_rates/private/test_loss_rates_new.py
"""

import pytest
from cooler import FlowerCooler

BAD_LOSSES = [-1, 1.5, "2", True]


@pytest.fixture
def cooler():
    c = FlowerCooler()
    c.add_batch("tulips", 20, 3)
    c.add_batch("roses", 12, 0)
    return c


def state(c):
    return {
        b: (c.get_freshness(b), c.get_days_left(b), c.get_losses(b)) for b in c.get_batches()
    }


def test_losses_default_to_two_and_five(cooler):
    assert cooler.get_losses("tulips") == (2, 5)
    assert cooler.get_losses("roses") == (2, 5)


def test_losses_can_be_set_one_at_a_time():
    c = FlowerCooler(daily_loss=3, late_loss=4)
    c.add_batch("a", 20, 1, late_loss=1)
    c.add_batch("b", 20, 1, daily_loss=0)
    c.add_batch("c", 20, 1)
    assert [c.get_losses(b) for b in "abc"] == [(3, 1), (0, 4), (3, 4)]
    c.end_day()
    c.end_day()
    assert [c.get_freshness(b) for b in "abc"] == [16, 16, 13]


def test_losses_of_zero_keep_the_freshness_but_not_the_days():
    c = FlowerCooler(daily_loss=0, late_loss=0)
    c.add_batch("a", 9, 1)
    for _ in range(3):
        c.end_day()
    assert (c.get_freshness("a"), c.get_days_left("a")) == (9, -2)


def test_losses_larger_than_the_freshness_stop_at_zero():
    c = FlowerCooler()
    c.add_batch("a", 30, 0, late_loss=50)
    c.add_batch("b", 30, 1, daily_loss=31)
    c.end_day()
    assert c.get_freshness("a") == 0
    assert c.get_freshness("b") == 0
    assert c.get_wilted() == ["a", "b"]


@pytest.mark.parametrize("bad", BAD_LOSSES + [None])
@pytest.mark.parametrize("which", ["daily_loss", "late_loss"])
def test_losses_invalid_for_the_cooler(which, bad):
    with pytest.raises(ValueError):
        FlowerCooler(**{which: bad})


@pytest.mark.parametrize("bad", BAD_LOSSES)
@pytest.mark.parametrize("which", ["daily_loss", "late_loss"])
def test_losses_invalid_for_a_batch(cooler, which, bad):
    before = state(cooler)
    with pytest.raises(ValueError):
        cooler.add_batch("ferns", 20, 2, **{which: bad})
    assert state(cooler) == before
    assert cooler.get_batches() == ["tulips", "roses"]


def test_losses_set_later_apply_from_the_next_day(cooler):
    cooler.end_day()  # tulips 18, 2 days left
    cooler.set_losses("tulips", 1, 7)
    assert cooler.get_losses("tulips") == (1, 7)
    assert cooler.get_freshness("tulips") == 18
    cooler.end_day()
    cooler.end_day()
    assert cooler.get_freshness("tulips") == 16
    cooler.end_day()
    assert cooler.get_freshness("tulips") == 9
    assert cooler.get_losses("roses") == (2, 5)


@pytest.mark.parametrize("daily, late", [(-1, 2), (2, -1), (1.5, 2), (2, "5"), (True, 2), (None, 2), (2, None)])
def test_losses_invalid_when_setting(cooler, daily, late):
    before = state(cooler)
    with pytest.raises(ValueError):
        cooler.set_losses("tulips", daily, late)
    assert state(cooler) == before


def test_losses_of_unknown_batches_raise_key_error(cooler):
    with pytest.raises(KeyError):
        cooler.get_losses("asters")
    with pytest.raises(KeyError):
        cooler.get_losses(None)
    with pytest.raises(KeyError):
        cooler.set_losses("asters", -1, 2)  # unknown batch before a bad value
