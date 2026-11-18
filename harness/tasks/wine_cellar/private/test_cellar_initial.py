"""Hidden tests for the initial wine_cellar spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with cellar.py importable, e.g. in the sandbox):
    python -m pytest private/test_cellar_initial.py
"""

import pytest
from cellar import Cellar, CellarError, NotEnoughBottles

BAD_COUNTS = [0, -3]


@pytest.fixture
def cellar():
    c = Cellar()
    for name in ["north", "south", "east"]:
        c.add_rack(name)
    c.store("north", 2015, 5)
    c.store("north", 2009, 2)
    return c


def state(c):
    """Every rack in order with its vintages and counts, to check that a
    failed call changed nothing."""
    return [(r, [(v, c.get_count(r, v)) for v in held(c, r)]) for r in c.get_racks()]


def held(c, rack):
    """The rack's vintages that still have bottles (whether get_vintages also
    lists the others is unspecified)."""
    return [v for v in c.get_vintages(rack) if c.get_count(rack, v) > 0]


# --- racks ------------------------------------------------------------------


def test_a_new_rack_is_empty():
    c = Cellar()
    c.add_rack("north")
    assert held(c, "north") == []
    assert c.get_count("north", 2015) == 0


def test_racks_are_listed_in_the_order_added():
    c = Cellar()
    for name in ["west", "north", "east"]:
        c.add_rack(name)
    assert c.get_racks() == ["west", "north", "east"]


def test_adding_a_name_in_use_is_rejected(cellar):
    before = state(cellar)
    with pytest.raises(CellarError):
        cellar.add_rack("north")
    assert state(cellar) == before


def test_a_decommissioned_name_can_be_added_again_as_a_new_empty_rack(cellar):
    cellar.decommission_rack("north", "east")
    cellar.add_rack("north")
    assert cellar.get_racks() == ["south", "east", "north"]
    assert held(cellar, "north") == []
    assert cellar.get_count("north", 2015) == 0
    assert cellar.get_count("east", 2015) == 5


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.store("west", 2015, 1),
        lambda c: c.take("west", 2015, 1),
        lambda c: c.relocate_all("west", "south"),
        lambda c: c.relocate_all("north", "west"),
        lambda c: c.decommission_rack("west", "south"),
        lambda c: c.decommission_rack("north", "west"),
        lambda c: c.get_count("west", 2015),
        lambda c: c.get_vintages("west"),
    ],
)
def test_racks_never_added_raise_key_error(cellar, call):
    before = state(cellar)
    with pytest.raises(KeyError):
        call(cellar)
    assert state(cellar) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.store("east", 2015, 1),
        lambda c: c.take("east", 2015, 1),
        lambda c: c.relocate_all("east", "north"),
        lambda c: c.relocate_all("north", "east"),
        lambda c: c.decommission_rack("east", "north"),
        lambda c: c.decommission_rack("north", "east"),
        lambda c: c.get_count("east", 2015),
        lambda c: c.get_vintages("east"),
    ],
)
def test_a_decommissioned_rack_is_not_in_use(cellar, call):
    cellar.decommission_rack("east", "south")  # east is empty
    before = state(cellar)
    with pytest.raises(KeyError):
        call(cellar)
    assert state(cellar) == before


# --- storing and taking -------------------------------------------------------


def test_storing_and_taking_change_the_count(cellar):
    cellar.store("north", 2015, 3)
    cellar.take("north", 2015, 6)
    cellar.store("south", 2015, 1)
    assert cellar.get_count("north", 2015) == 2
    assert cellar.get_count("south", 2015) == 1
    assert cellar.get_count("north", 2009) == 2


def test_vintages_are_listed_oldest_first(cellar):
    cellar.store("north", 2020, 1)
    cellar.store("north", 2001, 1)
    assert held(cellar, "north") == [2001, 2009, 2015, 2020]


def test_every_bottle_of_a_vintage_can_be_taken(cellar):
    cellar.take("north", 2009, 2)
    assert cellar.get_count("north", 2009) == 0
    assert held(cellar, "north") == [2015]


def test_taking_more_than_there_are_raises_and_changes_nothing(cellar):
    before = state(cellar)
    with pytest.raises(NotEnoughBottles):
        cellar.take("north", 2009, 3)
    with pytest.raises(NotEnoughBottles):
        cellar.take("north", 2018, 1)
    with pytest.raises(NotEnoughBottles):
        cellar.take("south", 2015, 1)
    assert state(cellar) == before


@pytest.mark.parametrize("count", BAD_COUNTS)
def test_storing_0_or_fewer_bottles_is_rejected(cellar, count):
    before = state(cellar)
    with pytest.raises(ValueError):
        cellar.store("north", 2015, count)
    assert state(cellar) == before


# --- relocate_all ------------------------------------------------------------


def test_relocate_all_moves_every_vintage(cellar):
    cellar.store("south", 2015, 1)
    cellar.store("south", 2020, 4)
    assert cellar.relocate_all("north", "south") == 7
    assert held(cellar, "north") == []
    assert held(cellar, "south") == [2009, 2015, 2020]
    assert cellar.get_count("south", 2015) == 6
    assert cellar.get_count("south", 2009) == 2
    assert cellar.get_racks() == ["north", "south", "east"]


def test_a_rack_emptied_by_relocate_all_can_be_filled_again(cellar):
    cellar.relocate_all("north", "east")
    cellar.store("north", 2018, 3)
    assert held(cellar, "north") == [2018]
    assert cellar.get_count("east", 2015) == 5


def test_relocate_all_from_an_empty_rack_moves_nothing(cellar):
    before = state(cellar)
    assert cellar.relocate_all("east", "north") == 0
    assert state(cellar) == before


# --- decommission_rack ------------------------------------------------------


def test_decommission_rack_moves_every_bottle_and_removes_it(cellar):
    cellar.store("east", 2015, 2)
    assert cellar.decommission_rack("north", "east") == 7
    assert cellar.get_racks() == ["south", "east"]
    assert cellar.get_count("east", 2015) == 7
    assert cellar.get_count("east", 2009) == 2


def test_decommissioning_an_empty_rack_moves_nothing(cellar):
    assert cellar.decommission_rack("south", "north") == 0
    assert cellar.get_racks() == ["north", "east"]
    assert cellar.get_count("north", 2015) == 5


def test_the_other_racks_keep_their_order_after_a_decommission(cellar):
    cellar.add_rack("west")
    cellar.decommission_rack("south", "west")
    assert cellar.get_racks() == ["north", "east", "west"]


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.relocate_all("north", "north"),
        lambda c: c.decommission_rack("north", "north"),
        lambda c: c.relocate_all("east", "east"),
    ],
    ids=["relocate_all", "decommission_rack", "relocate_all_empty"],
)
def test_the_same_rack_on_both_sides_is_rejected(cellar, call):
    before = state(cellar)
    with pytest.raises(ValueError):
        call(cellar)
    assert state(cellar) == before


# --- general ----------------------------------------------------------------


def test_not_enough_bottles_is_a_cellar_error():
    assert issubclass(NotEnoughBottles, CellarError)


def test_cellars_do_not_share_racks():
    first, second = Cellar(), Cellar()
    first.add_rack("north")
    first.store("north", 2015, 3)
    assert second.get_racks() == []
    second.add_rack("north")
    assert second.get_count("north", 2015) == 0
