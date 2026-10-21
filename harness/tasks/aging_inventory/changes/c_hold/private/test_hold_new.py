"""Hidden tests for the c_hold change (batches on hold). Never shown to the
writer or the editor.

Usage (with cooler.py importable, e.g. in the sandbox):
    python -m pytest changes/c_hold/private/test_hold_new.py
"""

import pytest
from cooler import BatchHeld, CoolerError, FlowerCooler


@pytest.fixture
def cooler():
    c = FlowerCooler()
    c.add_category("greens")
    c.add_batch("tulips", 20, 3)
    c.add_batch("fern", 15, 1, category="greens")
    c.add_batch("roses", 12, 0)
    c.add_batch("ivy", 9, 2, category="greens")
    return c


def state(c):
    batches = {b: (c.get_freshness(b), c.get_days_left(b), c.is_held(b)) for b in c.get_batches()}
    return batches, c.get_held()


def test_hold_is_a_cooler_error():
    assert issubclass(BatchHeld, CoolerError)


def test_hold_new_batches_are_not_held(cooler):
    assert cooler.get_held() == []
    assert [cooler.is_held(b) for b in cooler.get_batches()] == [False] * 4


def test_hold_twice_or_release_twice_does_nothing(cooler):
    cooler.hold("tulips")
    cooler.hold("tulips")
    assert cooler.get_held() == ["tulips"]
    cooler.release("tulips")
    cooler.release("tulips")
    cooler.release("roses")
    assert cooler.get_held() == []


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.hold("asters"),
        lambda c: c.release("asters"),
        lambda c: c.is_held("asters"),
        lambda c: c.hold(None),
        lambda c: c.is_held(1),
        lambda c: c.hold_category("mosses"),
    ],
)
def test_hold_unknown_ids_raise_key_error(cooler, call):
    before = state(cooler)
    with pytest.raises(KeyError):
        call(cooler)
    assert state(cooler) == before


def test_hold_freezes_values_for_several_days(cooler):
    cooler.end_day()  # tulips 18, 2
    cooler.hold("tulips")
    for _ in range(4):
        cooler.end_day()
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (18, 2)
    assert (cooler.get_freshness("ivy"), cooler.get_days_left("ivy")) == (0, -3)
    cooler.release("tulips")
    cooler.end_day()
    cooler.end_day()
    cooler.end_day()
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (9, -1)


def test_hold_blocks_removal_and_changes_nothing(cooler):
    cooler.hold("fern")
    before = state(cooler)
    with pytest.raises(BatchHeld):
        cooler.remove_batch("fern")
    with pytest.raises(KeyError):
        cooler.remove_batch("asters")
    assert state(cooler) == before
    cooler.release("fern")
    cooler.remove_batch("fern")
    assert cooler.get_batches() == ["tulips", "roses", "ivy"]


def test_hold_keeps_held_batches_in_the_lists(cooler):
    for _ in range(3):
        cooler.end_day()  # roses and ivy reach 0
    cooler.hold("roses")
    assert cooler.get_wilted() == ["roses", "ivy"]
    assert "roses" in cooler.get_batches()


def test_hold_list_follows_the_order_batches_were_added(cooler):
    cooler.hold("ivy")
    cooler.hold("tulips")
    cooler.hold("roses")
    assert cooler.get_held() == ["tulips", "roses", "ivy"]
    cooler.release("roses")
    assert cooler.get_held() == ["tulips", "ivy"]


def test_hold_category_holds_the_current_batches_only(cooler):
    cooler.hold_category("greens")
    assert cooler.get_held() == ["fern", "ivy"]
    cooler.add_batch("moss", 20, 5, category="greens")
    assert cooler.is_held("moss") is False
    cooler.end_day()
    assert (cooler.get_freshness("fern"), cooler.get_freshness("ivy")) == (15, 9)
    assert cooler.get_freshness("moss") == 18
    assert cooler.get_freshness("tulips") == 18


def test_hold_category_with_no_batches_does_nothing(cooler):
    cooler.add_category("bulbs")
    cooler.hold_category("bulbs")
    assert cooler.get_held() == []


def test_hold_does_not_carry_over_to_a_re_added_id(cooler):
    cooler.hold("tulips")
    cooler.release("tulips")
    cooler.remove_batch("tulips")
    cooler.add_batch("tulips", 10, 1)
    assert cooler.is_held("tulips") is False
    cooler.end_day()
    assert cooler.get_freshness("tulips") == 8
