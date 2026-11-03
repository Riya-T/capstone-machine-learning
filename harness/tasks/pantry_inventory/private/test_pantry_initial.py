"""Hidden tests for the initial pantry_inventory spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest private/test_pantry_initial.py
"""

import pytest
from pantry import Pantry

BAD_QUANTITIES = [0, -1, 1.5, "2", None]
BAD_DAYS = [-1, 1.5, "3", None]


@pytest.fixture
def pantry():
    pan = Pantry()
    pan.add_item("milk", 2, 3)
    pan.add_item("rice", 10, 30)
    return pan


def left(pan, name):
    """The item's batches that still have units. Whether a used-up batch is
    still listed, as (use_by, 0), is unspecified, so those are skipped."""
    return [batch for batch in pan.get_batches(name) if batch[1] != 0]


def state(pan):
    """Every item's batches, to check that a failed call changed nothing."""
    return {name: left(pan, name) for name in pan.get_items()}


# --- adding -----------------------------------------------------------------


def test_a_new_pantry_has_no_items():
    pan = Pantry()
    assert pan.get_items() == []
    assert pan.get_expiring_by(100) == []


def test_items_are_listed_in_the_order_first_added():
    pan = Pantry()
    pan.add_item("rice", 1, 5)
    pan.add_item("milk", 1, 5)
    pan.add_item("rice", 1, 2)
    pan.add_item("beans", 1, 5)
    assert pan.get_items() == ["rice", "milk", "beans"]


def test_a_new_item_has_one_batch(pantry):
    assert pantry.get_quantity("milk") == 2
    assert pantry.get_batches("milk") == [(3, 2)]


def test_quantity_adds_up_over_batches(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.add_item("milk", 1, 1)
    assert pantry.get_quantity("milk") == 8
    assert pantry.get_quantity("rice") == 10


def test_batches_are_listed_in_the_order_added(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.add_item("milk", 1, 1)
    assert pantry.get_batches("milk") == [(3, 2), (8, 5), (1, 1)]


def test_batches_with_the_same_day_stay_separate(pantry):
    pantry.add_item("milk", 7, 3)
    pantry.add_item("milk", 4, 1)
    pantry.add_item("milk", 6, 3)
    assert pantry.get_batches("milk") == [(3, 2), (3, 7), (1, 4), (3, 6)]
    assert pantry.get_quantity("milk") == 19


@pytest.mark.parametrize("bad_name", [""])
def test_invalid_names_are_rejected(bad_name):
    pan = Pantry()
    with pytest.raises(ValueError):
        pan.add_item(bad_name, 1, 1)
    assert pan.get_items() == []


@pytest.mark.parametrize("quantity", BAD_QUANTITIES)
def test_invalid_quantities_are_rejected_when_adding(pantry, quantity):
    before = state(pantry)
    with pytest.raises(ValueError):
        pantry.add_item("milk", quantity, 3)
    with pytest.raises(ValueError):
        pantry.add_item("eggs", quantity, 3)
    assert state(pantry) == before
    assert pantry.get_items() == ["milk", "rice"]


@pytest.mark.parametrize("use_by", BAD_DAYS)
def test_invalid_use_by_days_are_rejected_when_adding(pantry, use_by):
    before = state(pantry)
    with pytest.raises(ValueError):
        pantry.add_item("milk", 1, use_by)
    with pytest.raises(ValueError):
        pantry.add_item("eggs", 1, use_by)
    assert state(pantry) == before
    assert pantry.get_items() == ["milk", "rice"]


def test_a_use_by_day_of_zero_is_allowed(pantry):
    pantry.add_item("eggs", 6, 0)
    assert pantry.get_batches("eggs") == [(0, 6)]
    assert pantry.get_expiring_by(0) == [("eggs", 6)]


# --- using ------------------------------------------------------------------


def test_using_takes_from_the_batch_added_first(pantry):
    pantry.add_item("milk", 5, 1)  # added later, though it must be used sooner
    pantry.use_item("milk", 1)
    assert left(pantry, "milk") == [(3, 1), (1, 5)]
    assert pantry.get_quantity("milk") == 6


def test_using_spans_several_batches(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.add_item("milk", 1, 1)
    pantry.use_item("milk", 4)
    assert left(pantry, "milk") == [(8, 3), (1, 1)]
    assert pantry.get_quantity("milk") == 4


def test_using_spans_more_than_two_batches(pantry):
    pantry.add_item("milk", 1, 1)
    pantry.add_item("milk", 3, 9)
    pantry.add_item("milk", 4, 2)
    pantry.use_item("milk", 7)
    assert left(pantry, "milk") == [(2, 3)]
    assert pantry.get_quantity("milk") == 3


def test_using_exactly_what_the_first_batch_holds(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.use_item("milk", 2)
    assert left(pantry, "milk") == [(8, 5)]
    assert pantry.get_quantity("milk") == 5
    pantry.use_item("milk", 5)
    assert left(pantry, "milk") == []
    assert pantry.get_quantity("milk") == 0


def test_later_uses_go_on_past_used_up_batches(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.add_item("milk", 1, 1)
    pantry.use_item("milk", 2)
    assert left(pantry, "milk") == [(8, 5), (1, 1)]
    pantry.use_item("milk", 3)
    assert left(pantry, "milk") == [(8, 2), (1, 1)]
    pantry.use_item("milk", 3)
    assert left(pantry, "milk") == []
    assert pantry.get_quantity("milk") == 0


def test_using_one_unit_at_a_time(pantry):
    pantry.add_item("milk", 1, 9)
    pantry.add_item("milk", 2, 4)
    for expected in ([(3, 1), (9, 1), (4, 2)], [(9, 1), (4, 2)], [(4, 2)], [(4, 1)], []):
        pantry.use_item("milk", 1)
        assert left(pantry, "milk") == expected
    assert pantry.get_quantity("milk") == 0


def test_using_only_changes_the_item_used(pantry):
    pantry.use_item("milk", 1)
    assert pantry.get_batches("rice") == [(30, 10)]
    assert left(pantry, "milk") == [(3, 1)]


def test_everything_can_be_used_and_the_item_stays_listed(pantry):
    pantry.use_item("milk", 2)
    assert pantry.get_quantity("milk") == 0
    assert left(pantry, "milk") == []
    assert pantry.get_items() == ["milk", "rice"]
    pantry.add_item("milk", 3, 9)
    assert left(pantry, "milk") == [(9, 3)]
    pantry.use_item("milk", 1)
    assert left(pantry, "milk") == [(9, 2)]
    assert pantry.get_quantity("milk") == 2


def test_using_more_than_there_is_takes_everything_left(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.use_item("milk", 10)
    assert pantry.get_quantity("milk") == 0
    assert left(pantry, "milk") == []
    assert pantry.get_items() == ["milk", "rice"]
    assert pantry.get_quantity("rice") == 10


def test_using_from_an_item_with_nothing_left_takes_nothing(pantry):
    pantry.use_item("milk", 2)
    pantry.use_item("milk", 4)
    assert left(pantry, "milk") == []
    assert pantry.get_quantity("milk") == 0
    assert pantry.get_items() == ["milk", "rice"]
    pantry.add_item("milk", 3, 9)
    pantry.use_item("milk", 1)
    assert left(pantry, "milk") == [(9, 2)]


def test_a_used_up_batch_if_listed_has_nothing_left(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.use_item("milk", 4)
    assert all(units >= 0 for _, units in pantry.get_batches("milk"))
    assert sum(units for _, units in pantry.get_batches("milk")) == 3


@pytest.mark.parametrize("quantity", BAD_QUANTITIES)
def test_invalid_quantities_are_rejected_when_using(pantry, quantity):
    before = state(pantry)
    with pytest.raises(ValueError):
        pantry.use_item("milk", quantity)
    assert state(pantry) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda pan: pan.use_item("eggs", 1),
        lambda pan: pan.get_quantity("eggs"),
        lambda pan: pan.get_batches("eggs"),
        lambda pan: pan.get_quantity(None),
        lambda pan: pan.get_quantity(1),
        lambda pan: pan.use_item(None, 1),
    ],
)
def test_names_that_are_not_items_raise_key_error(pantry, call):
    before = state(pantry)
    with pytest.raises(KeyError):
        call(pantry)
    assert state(pantry) == before


# --- expiring ---------------------------------------------------------------


def test_expiring_by_includes_the_day_itself(pantry):
    assert pantry.get_expiring_by(2) == []
    assert pantry.get_expiring_by(3) == [("milk", 2)]
    assert pantry.get_expiring_by(29) == [("milk", 2)]
    assert pantry.get_expiring_by(30) == [("milk", 2), ("rice", 10)]


def test_expiring_by_lists_items_in_the_order_first_added(pantry):
    pantry.add_item("beans", 1, 1)
    pantry.add_item("rice", 1, 2)
    assert pantry.get_expiring_by(5) == [("milk", 2), ("rice", 1), ("beans", 1)]


def test_expiring_by_looks_at_every_batch(pantry):
    pantry.add_item("rice", 1, 2)  # rice's second batch is the one that expires soon
    assert pantry.get_expiring_by(2) == [("rice", 1)]


def test_expiring_by_adds_up_only_the_batches_due(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.add_item("milk", 1, 1)
    pantry.add_item("milk", 4, 3)
    assert pantry.get_expiring_by(1) == [("milk", 1)]
    assert pantry.get_expiring_by(3) == [("milk", 7)]
    assert pantry.get_expiring_by(8) == [("milk", 12)]


def test_expiring_by_ignores_batches_that_are_used_up(pantry):
    pantry.add_item("milk", 5, 8)
    pantry.use_item("milk", 3)
    assert pantry.get_expiring_by(3) == []
    assert pantry.get_expiring_by(8) == [("milk", 4)]


def test_a_batch_used_part_way_counts_what_is_left(pantry):
    pantry.use_item("milk", 1)
    assert pantry.get_expiring_by(3) == [("milk", 1)]


def test_an_item_with_nothing_left_is_not_expiring(pantry):
    pantry.use_item("milk", 2)
    assert pantry.get_expiring_by(100) == [("rice", 10)]


@pytest.mark.parametrize("day", BAD_DAYS)
def test_invalid_days_are_rejected(pantry, day):
    with pytest.raises(ValueError):
        pantry.get_expiring_by(day)


def test_pantries_do_not_share_items():
    first, second = Pantry(), Pantry()
    first.add_item("milk", 1, 1)
    assert second.get_items() == []
    second.add_item("milk", 5, 5)
    assert second.get_batches("milk") == [(5, 5)]
    assert first.get_batches("milk") == [(1, 1)]
