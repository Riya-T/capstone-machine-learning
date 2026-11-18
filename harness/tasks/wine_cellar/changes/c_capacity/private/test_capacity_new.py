"""Hidden tests for the c_capacity change (rack capacity). Never shown to the
writer or the editor.

Usage (with cellar.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from cellar import Cellar, CellarError, NotEnoughBottles, RackFull

BAD_CAPACITIES = [0, -5, "12", 2.5, [12]]


@pytest.fixture
def cellar():
    c = Cellar()
    for name in ["north", "south", "east"]:
        c.add_rack(name)
    c.store("north", 2009, 3)
    c.store("north", 2015, 4)
    c.store("south", 2015, 2)
    return c


def state(c):
    return [(r, [(v, c.get_count(r, v)) for v in held(c, r)]) for r in c.get_racks()]


def held(c, rack):
    """The rack's vintages that still have bottles (whether get_vintages also
    lists the others is unspecified)."""
    return [v for v in c.get_vintages(rack) if c.get_count(rack, v) > 0]


# --- the setting ------------------------------------------------------------


def test_every_rack_starts_without_a_limit(cellar):
    assert [cellar.get_capacity(r) for r in cellar.get_racks()] == [None, None, None]
    cellar.store("east", 2015, 500)
    assert cellar.get_count("east", 2015) == 500


def test_a_rack_added_again_after_decommissioning_has_no_limit(cellar):
    cellar.set_capacity("east", 3)
    cellar.decommission_rack("east", "south")
    cellar.add_rack("east")
    assert cellar.get_capacity("east") is None
    cellar.store("east", 2015, 10)
    assert cellar.get_count("east", 2015) == 10


def test_each_setting_replaces_the_one_before(cellar):
    cellar.set_capacity("east", 3)
    cellar.set_capacity("east", 5)
    assert cellar.get_capacity("east") == 5
    cellar.store("east", 2015, 5)
    cellar.set_capacity("east", None)
    assert cellar.get_capacity("east") is None
    cellar.store("east", 2015, 5)
    assert cellar.get_count("east", 2015) == 10


def test_a_capacity_equal_to_the_bottles_there_is_allowed(cellar):
    cellar.set_capacity("north", 7)
    assert cellar.get_capacity("north") == 7
    with pytest.raises(RackFull):
        cellar.store("north", 2020, 1)


def test_a_capacity_below_the_bottles_there_is_rejected(cellar):
    cellar.set_capacity("north", 10)
    with pytest.raises(ValueError):
        cellar.set_capacity("north", 6)
    assert cellar.get_capacity("north") == 10


@pytest.mark.parametrize("capacity", BAD_CAPACITIES)
def test_invalid_capacities_are_rejected_and_keep_the_old_one(cellar, capacity):
    cellar.set_capacity("east", 8)
    with pytest.raises(ValueError):
        cellar.set_capacity("east", capacity)
    assert cellar.get_capacity("east") == 8


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.set_capacity("west", 5),
        lambda c: c.set_capacity("west", None),
        lambda c: c.get_capacity("west"),
        lambda c: c.set_capacity("east", 5),  # decommissioned below
        lambda c: c.get_capacity("east"),
    ],
)
def test_racks_not_in_use_raise_key_error(cellar, call):
    cellar.decommission_rack("east", "south")
    with pytest.raises(KeyError):
        call(cellar)


def test_a_setting_changes_no_counts(cellar):
    before = state(cellar)
    cellar.set_capacity("north", 7)
    cellar.set_capacity("east", 1)
    assert state(cellar) == before


# --- store ------------------------------------------------------------------


def test_store_up_to_the_capacity_works(cellar):
    cellar.set_capacity("south", 6)
    cellar.store("south", 2018, 3)
    cellar.store("south", 2015, 1)
    assert cellar.get_count("south", 2015) == 3
    assert cellar.get_count("south", 2018) == 3


def test_store_above_the_capacity_changes_nothing(cellar):
    cellar.set_capacity("south", 6)
    before = state(cellar)
    with pytest.raises(RackFull):
        cellar.store("south", 2018, 5)
    assert state(cellar) == before


def test_bottles_of_every_vintage_count_toward_the_capacity(cellar):
    cellar.set_capacity("north", 8)
    with pytest.raises(RackFull):
        cellar.store("north", 2020, 2)
    cellar.store("north", 2020, 1)
    assert held(cellar, "north") == [2009, 2015, 2020]


def test_taking_bottles_makes_room(cellar):
    cellar.set_capacity("north", 7)
    cellar.take("north", 2009, 3)
    cellar.store("north", 2020, 3)
    assert cellar.get_count("north", 2020) == 3


# --- relocate_all and decommission_rack -------------------------------------


def test_relocate_all_into_a_rack_with_room(cellar):
    cellar.set_capacity("south", 9)
    assert cellar.relocate_all("north", "south") == 7
    assert cellar.get_count("south", 2015) == 6


def test_relocate_all_into_a_rack_without_room_moves_nothing(cellar):
    cellar.set_capacity("south", 8)
    before = state(cellar)
    with pytest.raises(RackFull):
        cellar.relocate_all("north", "south")
    assert state(cellar) == before
    assert cellar.get_count("south", 2009) == 0


def test_decommission_into_a_rack_with_room(cellar):
    cellar.set_capacity("east", 7)
    assert cellar.decommission_rack("north", "east") == 7
    assert cellar.get_racks() == ["south", "east"]


def test_decommission_into_a_rack_without_room_keeps_the_rack(cellar):
    cellar.set_capacity("east", 6)
    before = state(cellar)
    with pytest.raises(RackFull):
        cellar.decommission_rack("north", "east")
    assert state(cellar) == before
    assert cellar.get_racks() == ["north", "south", "east"]


def test_a_refused_decommission_can_be_retried_with_more_room(cellar):
    cellar.set_capacity("south", 5)
    with pytest.raises(RackFull):
        cellar.decommission_rack("north", "south")
    cellar.set_capacity("south", None)
    assert cellar.decommission_rack("north", "south") == 7
    assert cellar.get_count("south", 2015) == 6


def test_an_empty_rack_never_raises_rack_full(cellar):
    cellar.set_capacity("north", 7)
    assert cellar.relocate_all("east", "north") == 0
    assert cellar.decommission_rack("east", "north") == 0
    assert cellar.get_racks() == ["north", "south"]


def test_the_capacity_of_the_rack_bottles_leave_is_not_checked(cellar):
    cellar.set_capacity("north", 7)
    cellar.set_capacity("south", 2)
    assert cellar.relocate_all("south", "east") == 2
    assert cellar.decommission_rack("north", "east") == 7
    assert cellar.get_count("east", 2015) == 6


def test_a_capacity_only_applies_to_its_own_rack(cellar):
    cellar.set_capacity("south", 2)
    cellar.store("east", 2015, 9)
    assert cellar.relocate_all("north", "east") == 7
    assert cellar.get_count("east", 2015) == 13


def test_rack_full_is_a_cellar_error_but_not_not_enough_bottles():
    assert issubclass(RackFull, CellarError)
    assert not issubclass(RackFull, NotEnoughBottles)
