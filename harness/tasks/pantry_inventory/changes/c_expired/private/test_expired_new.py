"""Hidden tests for the c_expired change (the current day and expired
batches). Never shown to the writer or the editor.

Usage (with pantry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_expired/private/test_expired_new.py
"""

import pytest
from pantry import Pantry


@pytest.fixture
def pantry():
    pan = Pantry()
    pan.add_item("milk", 2, 3)
    pan.add_item("milk", 5, 8)
    pan.add_item("rice", 10, 30)
    return pan


def left(pan, name):
    """The item's batches that still have units. Whether a used-up batch is
    still listed, as (use_by, 0), is unspecified, so those are skipped."""
    return [batch for batch in pan.get_batches(name) if batch[1] != 0]


def usable(pan, name):
    """The item's batches that are not expired and still have units."""
    return [b for b in left(pan, name) if b[0] >= pan.get_day()]


def expired(pan, name):
    """The item's expired batches that are still listed."""
    return [b for b in left(pan, name) if b[0] < pan.get_day()]


def kept_or_thrown_away(after, before):
    """use_item may throw away expired batches or keep them: each expired
    batch is still listed with all its units, in its place, or gone."""
    rest = iter(before)
    return all(any(batch == b for b in rest) for batch in after)


def state(pan):
    return {name: left(pan, name) for name in pan.get_items()}


def test_nothing_is_expired_on_day_zero(pantry):
    assert pantry.get_day() == 0
    assert pantry.get_usable_quantity("milk") == 7
    assert pantry.get_expired_quantity("milk") == 0
    assert pantry.get_expired_quantity("rice") == 0


def test_a_batch_is_usable_on_its_use_by_day_and_expired_after(pantry):
    pantry.set_day(3)
    assert pantry.get_usable_quantity("milk") == 7
    assert pantry.get_expired_quantity("milk") == 0
    pantry.set_day(4)
    assert pantry.get_usable_quantity("milk") == 5
    assert pantry.get_expired_quantity("milk") == 2


def test_a_batch_used_by_today_can_be_used_today(pantry):
    pantry.set_day(3)
    pantry.use_item("milk", 1)
    assert left(pantry, "milk") == [(3, 1), (8, 5)]


def test_usable_and_expired_add_up_to_the_quantity(pantry):
    pantry.set_day(9)
    assert pantry.get_usable_quantity("milk") == 0
    assert pantry.get_expired_quantity("milk") == 7
    assert pantry.get_quantity("milk") == 7
    assert pantry.get_batches("milk") == [(3, 2), (8, 5)]


def test_usable_and_expired_count_only_units_left(pantry):
    pantry.use_item("milk", 3)  # the day-3 batch is used up, 1 unit of day 8 taken
    pantry.set_day(4)
    assert pantry.get_usable_quantity("milk") == 4
    assert pantry.get_expired_quantity("milk") == 0


def test_using_skips_expired_batches(pantry):
    pantry.set_day(4)
    pantry.use_item("milk", 1)
    assert usable(pantry, "milk") == [(8, 4)]
    assert expired(pantry, "milk") in ([(3, 2)], [])
    assert pantry.get_usable_quantity("milk") == 4


def test_using_skips_an_expired_batch_between_usable_ones():
    pan = Pantry()
    pan.add_item("milk", 4, 8)
    pan.add_item("milk", 2, 3)
    pan.add_item("milk", 3, 6)
    pan.set_day(4)
    pan.use_item("milk", 6)
    assert usable(pan, "milk") == [(6, 1)]
    assert expired(pan, "milk") in ([(3, 2)], [])
    assert pan.get_usable_quantity("milk") == 1


def test_using_stays_first_in_first_out_among_usable_batches(pantry):
    pantry.add_item("milk", 3, 6)
    pantry.set_day(4)
    pantry.use_item("milk", 4)
    assert usable(pantry, "milk") == [(8, 1), (6, 3)]


def test_using_more_than_the_usable_amount_takes_only_usable_units(pantry):
    pantry.set_day(4)
    pantry.use_item("milk", 6)
    assert usable(pantry, "milk") == []
    assert expired(pantry, "milk") in ([(3, 2)], [])
    assert pantry.get_usable_quantity("milk") == 0


def test_using_when_everything_is_expired_takes_nothing(pantry):
    pantry.set_day(9)
    before = left(pantry, "milk")
    pantry.use_item("milk", 1)
    assert kept_or_thrown_away(left(pantry, "milk"), before)
    assert pantry.get_usable_quantity("milk") == 0
    assert pantry.get_batches("rice") == [(30, 10)]


def test_quantities_add_up_after_using_with_expired_batches(pantry):
    pantry.add_item("milk", 4, 1)
    pantry.add_item("milk", 3, 9)
    pantry.set_day(4)
    pantry.use_item("milk", 6)
    assert usable(pantry, "milk") == [(9, 2)]
    expired_units = pantry.get_expired_quantity("milk")
    assert expired_units == sum(units for _, units in expired(pantry, "milk"))
    assert pantry.get_usable_quantity("milk") + expired_units == pantry.get_quantity("milk")
    assert pantry.discard_expired("milk") == expired_units
    assert left(pantry, "milk") == [(9, 2)]


def test_using_one_item_leaves_the_expired_batches_of_others(pantry):
    pantry.add_item("rice", 4, 2)
    pantry.set_day(4)
    pantry.use_item("milk", 1)
    assert left(pantry, "rice") == [(30, 10), (2, 4)]
    pantry.use_item("rice", 1)
    assert expired(pantry, "milk") in ([(3, 2)], [])
    assert usable(pantry, "rice") == [(30, 9)]


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "2", None])
def test_a_use_that_raises_throws_nothing_away(pantry, quantity):
    pantry.set_day(4)
    with pytest.raises(ValueError):
        pantry.use_item("milk", quantity)
    assert pantry.get_batches("milk") == [(3, 2), (8, 5)]
    assert pantry.get_expired_quantity("milk") == 2


def test_discarding_returns_the_units_thrown_away(pantry):
    pantry.add_item("milk", 3, 1)
    pantry.set_day(4)
    assert pantry.discard_expired("milk") == 5
    assert pantry.get_batches("milk") == [(8, 5)]
    assert pantry.get_quantity("milk") == 5
    assert pantry.get_expired_quantity("milk") == 0
    assert pantry.discard_expired("milk") == 0


def test_discarding_keeps_the_order_of_the_batches_left():
    pan = Pantry()
    pan.add_item("milk", 4, 8)
    pan.add_item("milk", 2, 3)
    pan.add_item("milk", 3, 6)
    pan.set_day(4)
    assert pan.discard_expired("milk") == 2
    assert pan.get_batches("milk") == [(8, 4), (6, 3)]


def test_discarding_after_using_counts_only_units_left(pantry):
    pantry.add_item("milk", 1, 2)
    pantry.use_item("milk", 6)  # the day-3 batch is used up, 4 units of day 8 taken
    pantry.set_day(4)
    assert pantry.discard_expired("milk") == 1
    assert left(pantry, "milk") == [(8, 1)]
    assert pantry.get_quantity("milk") == 1


def test_discarding_leaves_other_items_alone(pantry):
    pantry.set_day(4)
    before = list(pantry.get_batches("rice"))
    pantry.discard_expired("milk")
    assert pantry.get_batches("rice") == before
    assert pantry.discard_expired("rice") == 0


def test_discarding_everything_leaves_the_item_listed(pantry):
    pantry.set_day(20)
    assert pantry.discard_expired("milk") == 7
    assert pantry.get_items() == ["milk", "rice"]
    assert pantry.get_batches("milk") == []
    pantry.add_item("milk", 2, 25)
    assert pantry.get_batches("milk") == [(25, 2)]


def test_the_day_can_stay_but_never_go_back(pantry):
    pantry.set_day(5)
    pantry.set_day(5)
    with pytest.raises(ValueError):
        pantry.set_day(4)
    assert pantry.get_day() == 5
    pantry.set_day(6)
    assert pantry.get_day() == 6


@pytest.mark.parametrize("day", [-1, 1.5, "3", None])
def test_invalid_days_are_rejected_when_setting(pantry, day):
    pantry.set_day(2)
    with pytest.raises(ValueError):
        pantry.set_day(day)
    assert pantry.get_day() == 2


def test_setting_the_day_changes_no_batches(pantry):
    before = state(pantry)
    pantry.set_day(10)
    assert state(pantry) == before


@pytest.mark.parametrize("method", ["get_usable_quantity", "get_expired_quantity", "discard_expired"])
@pytest.mark.parametrize("name", ["eggs", None, 1])
def test_new_methods_raise_key_error_for_names_that_are_not_items(pantry, method, name):
    pantry.set_day(4)
    with pytest.raises(KeyError):
        getattr(pantry, method)(name)
    assert pantry.get_batches("milk") == [(3, 2), (8, 5)]


def test_batches_added_on_the_current_day_are_usable(pantry):
    pantry.set_day(10)
    pantry.add_item("milk", 4, 10)
    assert pantry.get_usable_quantity("milk") == 4
    pantry.use_item("milk", 4)
    assert usable(pantry, "milk") == []
    assert pantry.get_usable_quantity("milk") == 0
    assert pantry.get_expired_quantity("milk") in (0, 2, 5, 7)
