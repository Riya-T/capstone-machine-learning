"""Hidden tests for the c_undo_day change (taking back ended days). Never
shown to the writer or the editor.

Usage (with cooler.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo_day/private/test_undo_day_new.py
"""

import pytest
from cooler import CoolerError, FlowerCooler


@pytest.fixture
def cooler():
    c = FlowerCooler()
    c.add_batch("tulips", 20, 3)
    c.add_batch("roses", 4, 0)
    return c


def state(c):
    return {b: (c.get_freshness(b), c.get_days_left(b)) for b in c.get_batches()}, c.get_day()


def test_undo_day_counter_starts_at_zero():
    assert FlowerCooler().get_day() == 0


def test_undo_day_walks_back_one_day_at_a_time(cooler):
    seen = [state(cooler)]
    for _ in range(3):
        cooler.end_day()
        seen.append(state(cooler))
    assert seen[-1] == ({"tulips": (14, 0), "roses": (0, -3)}, 3)
    for expected in reversed(seen[:-1]):
        cooler.undo_day()
        assert state(cooler) == expected


def test_undo_day_restores_values_lost_to_the_floor(cooler):
    cooler.end_day()  # roses 0, -1
    cooler.end_day()  # roses 0, -2
    cooler.undo_day()
    assert (cooler.get_freshness("roses"), cooler.get_days_left("roses")) == (0, -1)
    cooler.undo_day()
    assert (cooler.get_freshness("roses"), cooler.get_days_left("roses")) == (4, 0)


def test_undo_day_with_nothing_left_raises_and_changes_nothing(cooler):
    cooler.end_day()
    cooler.undo_day()
    before = state(cooler)
    with pytest.raises(CoolerError):
        cooler.undo_day()
    assert state(cooler) == before


def test_undo_day_then_end_day_works_as_before(cooler):
    cooler.end_day()
    cooler.end_day()
    cooler.undo_day()
    cooler.end_day()
    assert state(cooler) == ({"tulips": (16, 1), "roses": (0, -2)}, 2)
    cooler.undo_day()
    cooler.undo_day()
    assert state(cooler) == ({"tulips": (20, 3), "roses": (4, 0)}, 0)


def test_undo_day_leaves_batches_added_after_that_day(cooler):
    cooler.end_day()
    cooler.add_batch("asters", 10, 1)
    cooler.end_day()  # asters 8, 0
    cooler.undo_day()
    assert (cooler.get_freshness("asters"), cooler.get_days_left("asters")) == (10, 1)
    cooler.undo_day()  # asters was not in the cooler on the first day
    assert (cooler.get_freshness("asters"), cooler.get_days_left("asters")) == (10, 1)
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (20, 3)


def test_undo_day_does_not_bring_back_removed_batches(cooler):
    cooler.end_day()
    cooler.remove_batch("roses")
    cooler.undo_day()
    assert cooler.get_batches() == ["tulips"]
    with pytest.raises(KeyError):
        cooler.get_freshness("roses")
    assert cooler.get_freshness("tulips") == 20


def test_undo_day_leaves_a_new_batch_that_reuses_an_id(cooler):
    cooler.end_day()  # tulips 18, 2
    cooler.remove_batch("tulips")
    cooler.add_batch("tulips", 25, 4)
    cooler.undo_day()
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (25, 4)
    assert (cooler.get_freshness("roses"), cooler.get_days_left("roses")) == (4, 0)


def test_undo_day_on_an_empty_cooler(cooler):
    empty = FlowerCooler()
    empty.end_day()
    assert empty.get_day() == 1
    empty.undo_day()
    assert empty.get_day() == 0
    with pytest.raises(CoolerError):
        empty.undo_day()
