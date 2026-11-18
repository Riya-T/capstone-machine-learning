"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with cellar.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from cellar import Cellar, CellarError, NotEnoughBottles


@pytest.fixture
def cellar():
    c = Cellar()
    for name in ["north", "south", "east"]:
        c.add_rack(name)
    c.store("north", 2015, 3)
    c.store("north", 2009, 2)
    c.store("south", 2015, 4)
    return c  # 6 recorded calls


def state(c):
    return [(r, [(v, c.get_count(r, v)) for v in held(c, r)]) for r in c.get_racks()]


def held(c, rack):
    """The rack's vintages that still have bottles (whether get_vintages also
    lists the others is unspecified)."""
    return [v for v in c.get_vintages(rack) if c.get_count(rack, v) > 0]


# --- each call can be undone ------------------------------------------------


def test_undo_of_storing_a_new_vintage(cellar):
    before = state(cellar)
    cellar.store("east", 2020, 2)
    cellar.undo()
    assert state(cellar) == before
    assert held(cellar, "east") == []


def test_undo_of_storing_more_of_a_vintage(cellar):
    cellar.store("north", 2015, 5)
    cellar.undo()
    assert cellar.get_count("north", 2015) == 3


def test_undo_of_taking_every_bottle_of_a_vintage(cellar):
    before = state(cellar)
    cellar.take("north", 2009, 2)
    cellar.undo()
    assert state(cellar) == before
    assert held(cellar, "north") == [2009, 2015]


def test_undo_of_relocate_all_restores_both_racks(cellar):
    before = state(cellar)
    assert cellar.relocate_all("north", "south") == 5
    cellar.undo()
    assert state(cellar) == before
    assert cellar.get_count("south", 2015) == 4
    assert held(cellar, "south") == [2015]


def test_undo_of_relocate_all_into_an_empty_rack(cellar):
    before = state(cellar)
    cellar.relocate_all("south", "east")
    cellar.undo()
    assert state(cellar) == before
    assert held(cellar, "east") == []


def test_undo_of_decommission_brings_the_rack_back_with_its_bottles(cellar):
    before = state(cellar)
    assert cellar.decommission_rack("north", "south") == 5
    cellar.undo()
    assert state(cellar) == before
    assert cellar.get_racks() == ["north", "south", "east"]
    assert cellar.get_count("south", 2015) == 4
    assert cellar.get_count("south", 2009) == 0


def test_undo_of_decommission_keeps_its_place_in_the_list(cellar):
    cellar.add_rack("west")
    before = state(cellar)
    cellar.decommission_rack("south", "west")
    assert cellar.get_racks() == ["north", "east", "west"]
    cellar.undo()
    assert cellar.get_racks() == ["north", "south", "east", "west"]
    assert state(cellar) == before


def test_a_rack_brought_back_is_in_use_again(cellar):
    cellar.decommission_rack("north", "east")
    cellar.undo()
    cellar.store("north", 2015, 1)
    assert cellar.get_count("north", 2015) == 4
    with pytest.raises(CellarError):
        cellar.add_rack("north")
    assert cellar.decommission_rack("north", "south") == 6
    assert cellar.get_racks() == ["south", "east"]


def test_undo_of_add_rack_removes_it_and_frees_the_name(cellar):
    cellar.add_rack("west")
    cellar.undo()
    assert cellar.get_racks() == ["north", "south", "east"]
    with pytest.raises(KeyError):
        cellar.get_vintages("west")
    cellar.add_rack("west")
    assert cellar.get_racks() == ["north", "south", "east", "west"]
    assert held(cellar, "west") == []


def test_undo_through_a_name_that_was_decommissioned_and_added_again(cellar):
    cellar.add_rack("west")
    cellar.store("west", 2001, 2)
    cellar.decommission_rack("west", "east")
    cellar.add_rack("west")  # a new, empty west
    cellar.store("west", 2022, 1)
    cellar.undo()  # the 2022 bottle
    cellar.undo()  # the new west
    assert cellar.get_racks() == ["north", "south", "east"]
    cellar.undo()  # the decommission: the old west comes back with its bottles
    assert cellar.get_racks() == ["north", "south", "east", "west"]
    assert held(cellar, "west") == [2001]
    assert cellar.get_count("east", 2001) == 0
    cellar.undo()  # the 2001 bottles
    cellar.undo()  # the first west
    assert cellar.get_racks() == ["north", "south", "east"]


# --- calls that move nothing ------------------------------------------------


def test_a_relocate_all_of_nothing_is_still_a_call(cellar):
    cellar.store("east", 2020, 1)
    cellar.take("east", 2020, 1)
    assert cellar.relocate_all("east", "north") == 0
    cellar.undo()  # the relocate_all, which changed nothing
    assert held(cellar, "east") == []
    cellar.undo()  # the take
    assert cellar.get_count("east", 2020) == 1


def test_decommissioning_an_empty_rack_can_be_undone(cellar):
    cellar.store("south", 2015, 1)
    assert cellar.decommission_rack("east", "south") == 0
    cellar.undo()
    assert cellar.get_racks() == ["north", "south", "east"]
    assert cellar.get_count("south", 2015) == 5
    cellar.undo()
    assert cellar.get_count("south", 2015) == 4


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    c = Cellar()
    calls = [
        lambda: c.add_rack("north"),
        lambda: c.add_rack("south"),
        lambda: c.store("north", 2015, 5),
        lambda: c.store("north", 2009, 2),
        lambda: c.add_rack("east"),
        lambda: c.store("south", 2018, 4),
        lambda: c.take("north", 2015, 1),
        lambda: c.store("south", 2015, 2),
        lambda: c.relocate_all("south", "east"),
        lambda: c.decommission_rack("north", "east"),
        lambda: c.add_rack("west"),
        lambda: c.store("west", 2001, 1),
        lambda: c.relocate_all("south", "west"),
        lambda: c.decommission_rack("west", "south"),
    ]
    states = [state(c)]
    for call in calls:
        call()
        states.append(state(c))
    assert c.get_racks() == ["south", "east"]
    assert c.get_count("east", 2015) == 6
    assert c.get_count("south", 2001) == 1
    for expected in reversed(states[:-1]):
        c.undo()
        assert state(c) == expected
    with pytest.raises(CellarError):
        c.undo()
    assert c.get_racks() == []


def test_failed_calls_are_not_recorded(cellar):
    cellar.store("east", 2020, 2)
    for call in (
        lambda: cellar.take("north", 2015, 99),
        lambda: cellar.take("north", 2020, 1),
        lambda: cellar.relocate_all("north", "north"),
        lambda: cellar.relocate_all("north", "west"),
        lambda: cellar.decommission_rack("north", "north"),
        lambda: cellar.add_rack("north"),
        lambda: cellar.store("west", 2015, 1),
        lambda: cellar.store("north", 2015, 0),
    ):
        with pytest.raises((ValueError, KeyError, CellarError)):
            call()
    cellar.undo()  # the 2020 bottles
    assert held(cellar, "east") == []
    assert cellar.get_count("north", 2015) == 3


def test_get_calls_are_not_recorded(cellar):
    cellar.store("east", 2020, 2)
    cellar.get_count("east", 2020)
    cellar.get_vintages("east")
    cellar.get_racks()
    cellar.undo()
    assert held(cellar, "east") == []
    assert cellar.get_count("south", 2015) == 4


def test_there_is_no_redo():
    c = Cellar()
    c.add_rack("north")
    c.store("north", 2015, 3)
    c.undo()
    c.undo()
    assert c.get_racks() == []
    with pytest.raises(CellarError):
        c.undo()


def test_new_calls_after_an_undo_are_undone_first(cellar):
    cellar.store("east", 2020, 2)
    cellar.undo()
    cellar.store("east", 2001, 1)
    cellar.undo()
    assert held(cellar, "east") == []
    cellar.undo()  # the bottles stored in south in the fixture
    assert held(cellar, "south") == []
    assert held(cellar, "north") == [2009, 2015]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    c = Cellar()
    with pytest.raises(CellarError):
        c.undo()
    c.add_rack("north")
    c.undo()
    with pytest.raises(CellarError):
        c.undo()
    assert c.get_racks() == []
    c.add_rack("north")
    c.store("north", 2015, 1)
    assert c.get_count("north", 2015) == 1


def test_the_whole_fixture_can_be_undone(cellar):
    for _ in range(6):
        cellar.undo()
    assert cellar.get_racks() == []
    with pytest.raises(CellarError):
        cellar.undo()


def test_undo_restores_counts_that_a_later_call_checks(cellar):
    cellar.take("north", 2015, 3)
    cellar.undo()
    assert cellar.relocate_all("north", "east") == 5
    assert cellar.get_count("east", 2015) == 3
    with pytest.raises(NotEnoughBottles):
        cellar.take("north", 2015, 1)
