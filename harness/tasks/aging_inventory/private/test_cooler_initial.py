"""Hidden tests for the initial aging_inventory spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with cooler.py importable, e.g. in the sandbox):
    python -m pytest private/test_cooler_initial.py
"""

import pytest
from cooler import CoolerError, FlowerCooler


@pytest.fixture
def cooler():
    c = FlowerCooler()
    c.add_batch("tulips", 20, 3)
    c.add_batch("roses", 12, 0)
    c.add_batch("lilies", 30, 10)
    return c


def state(c):
    """Every batch's values, to check that a failed call changed nothing."""
    return {b: (c.get_freshness(b), c.get_days_left(b)) for b in c.get_batches()}


def days(c, n):
    for _ in range(n):
        c.end_day()


# --- batches ----------------------------------------------------------------


def test_an_empty_cooler_has_no_batches():
    c = FlowerCooler()
    assert c.get_batches() == []
    assert c.get_wilted() == []
    c.end_day()  # nothing to update
    assert c.get_batches() == []


def test_batches_are_listed_in_the_order_added():
    c = FlowerCooler()
    for name in ["roses", "asters", "tulips"]:
        c.add_batch(name, 10, 2)
    assert c.get_batches() == ["roses", "asters", "tulips"]


@pytest.mark.parametrize("freshness, days_left", [(0, 0), (30, 0), (15, 100)])
def test_boundary_values_are_accepted(freshness, days_left):
    c = FlowerCooler()
    c.add_batch("x", freshness, days_left)
    assert (c.get_freshness("x"), c.get_days_left("x")) == (freshness, days_left)


@pytest.mark.parametrize(
    "freshness, days_left",
    [(-1, 2), (31, 2), (1.5, 2), ("10", 2), (None, 2), (10, -1), (10, 2.0), (10, "3"), (10, None)],
)
def test_invalid_values_are_rejected(cooler, freshness, days_left):
    before = state(cooler)
    with pytest.raises(ValueError):
        cooler.add_batch("asters", freshness, days_left)
    assert state(cooler) == before
    assert cooler.get_batches() == ["tulips", "roses", "lilies"]


def test_an_empty_id_is_rejected(cooler):
    with pytest.raises(ValueError):
        cooler.add_batch("", 10, 2)
    assert cooler.get_batches() == ["tulips", "roses", "lilies"]


def test_adding_an_id_twice_is_rejected(cooler):
    cooler.end_day()
    before = state(cooler)
    with pytest.raises(CoolerError):
        cooler.add_batch("tulips", 30, 5)
    assert state(cooler) == before


def test_a_bad_value_is_reported_before_a_repeated_id(cooler):
    with pytest.raises(ValueError):
        cooler.add_batch("tulips", 31, 5)


def test_removing_a_batch(cooler):
    cooler.remove_batch("roses")
    assert cooler.get_batches() == ["tulips", "lilies"]
    with pytest.raises(KeyError):
        cooler.get_freshness("roses")
    with pytest.raises(KeyError):
        cooler.remove_batch("roses")


def test_a_removed_id_can_be_added_again_as_a_new_batch(cooler):
    days(cooler, 2)
    cooler.remove_batch("tulips")
    cooler.add_batch("tulips", 25, 4)
    assert cooler.get_batches() == ["roses", "lilies", "tulips"]
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (25, 4)


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.get_freshness("asters"),
        lambda c: c.get_days_left("asters"),
        lambda c: c.remove_batch("asters"),
        lambda c: c.get_freshness(None),
        lambda c: c.get_days_left(1),
        lambda c: c.remove_batch(None),
    ],
)
def test_unknown_ids_raise_key_error_and_change_nothing(cooler, call):
    before = state(cooler)
    with pytest.raises(KeyError):
        call(cooler)
    assert state(cooler) == before


# --- ending a day -----------------------------------------------------------


def test_the_example_from_the_description():
    c = FlowerCooler()
    c.add_batch("x", 12, 1)
    seen = []
    for _ in range(4):
        c.end_day()
        seen.append((c.get_freshness("x"), c.get_days_left("x")))
    assert seen == [(10, 0), (5, -1), (0, -2), (0, -3)]


def test_the_loss_depends_on_the_days_left_before_the_day(cooler):
    # tulips: 3 days left -> three days at 2, then 5 a day.
    days(cooler, 3)
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (14, 0)
    cooler.end_day()
    assert (cooler.get_freshness("tulips"), cooler.get_days_left("tulips")) == (9, -1)


def test_every_batch_is_updated_on_its_own(cooler):
    days(cooler, 2)
    assert state(cooler) == {"tulips": (16, 1), "roses": (2, -2), "lilies": (26, 8)}


def test_freshness_never_goes_below_zero(cooler):
    days(cooler, 3)
    assert cooler.get_freshness("roses") == 0
    days(cooler, 5)
    assert cooler.get_freshness("roses") == 0
    assert cooler.get_days_left("roses") == -8


def test_a_batch_with_two_freshness_left_loses_exactly_two():
    c = FlowerCooler()
    c.add_batch("x", 3, 2)
    c.end_day()
    assert c.get_freshness("x") == 1
    c.end_day()
    assert c.get_freshness("x") == 0
    assert c.get_days_left("x") == 0


def test_a_batch_added_later_starts_from_its_own_values(cooler):
    days(cooler, 4)
    cooler.add_batch("asters", 10, 1)
    assert (cooler.get_freshness("asters"), cooler.get_days_left("asters")) == (10, 1)
    cooler.end_day()
    assert (cooler.get_freshness("asters"), cooler.get_days_left("asters")) == (8, 0)
    assert cooler.get_freshness("lilies") == 20


def test_a_batch_that_starts_wilted_is_listed(cooler):
    cooler.add_batch("asters", 0, 5)
    assert cooler.get_wilted() == ["asters"]
    cooler.end_day()
    assert cooler.get_days_left("asters") == 4
    assert cooler.get_freshness("asters") == 0


def test_wilted_batches_are_listed_in_the_order_added(cooler):
    cooler.add_batch("asters", 4, 0)
    assert cooler.get_wilted() == []
    days(cooler, 1)
    assert cooler.get_wilted() == ["asters"]
    days(cooler, 2)
    assert cooler.get_wilted() == ["roses", "asters"]
    cooler.remove_batch("roses")
    assert cooler.get_wilted() == ["asters"]


def test_coolers_do_not_share_batches():
    first, second = FlowerCooler(), FlowerCooler()
    first.add_batch("tulips", 20, 3)
    first.end_day()
    assert second.get_batches() == []
    second.add_batch("tulips", 20, 3)
    assert second.get_freshness("tulips") == 20
