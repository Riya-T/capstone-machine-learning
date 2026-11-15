"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with depot.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from depot import Depot, DepotError


@pytest.fixture
def depot():
    dep = Depot()
    dep.add_tank("north")
    dep.add_tank("south")
    return dep


def state(dep):
    """The tank list, every level and every log."""
    tanks = dep.get_tanks()
    return tanks, {t: (dep.get_level(t), dep.get_log(t)) for t in tanks}


# --- each kind of call ------------------------------------------------------


def test_undo_reverses_a_drain(depot):
    depot.fill("north", 100)
    depot.drain("north", 40)
    assert depot.undo() is None
    assert depot.get_level("north") == 100
    assert depot.get_log("north") == [("fill", 100)]


def test_undo_reverses_a_pump_in_either_direction(depot):
    depot.fill("north", 100)
    depot.pump("north", "south", 60)
    depot.pump("south", "north", 25)
    depot.undo()
    assert (depot.get_level("north"), depot.get_level("south")) == (40, 60)
    assert depot.get_log("north") == [("fill", 100), ("out", 60)]
    assert depot.get_log("south") == [("in", 60)]


def test_undo_reverses_a_pump_down(depot):
    depot.fill("north", 100)
    depot.fill("south", 5)
    assert depot.pump_down("north", "south", 30) == 70
    depot.undo()
    assert (depot.get_level("north"), depot.get_level("south")) == (100, 5)
    assert depot.get_log("north") == [("fill", 100)]
    assert depot.get_log("south") == [("fill", 5)]


def test_a_pump_down_that_moved_nothing_still_counts(depot):
    depot.fill("north", 10)
    depot.fill("south", 3)
    assert depot.pump_down("north", "south", 20) == 0
    depot.undo()  # reverses the pump_down, which changed nothing
    assert (depot.get_level("north"), depot.get_level("south")) == (10, 3)
    depot.undo()  # then the fill of south
    assert (depot.get_level("north"), depot.get_level("south")) == (10, 0)
    assert depot.get_log("south") == []


def test_undo_brings_a_retired_tank_back_in_its_place():
    dep = Depot()
    for name in ["a", "b", "c"]:
        dep.add_tank(name)
    dep.fill("b", 30)
    dep.fill("c", 5)
    assert dep.retire_tank("b", "c") == 30
    dep.undo()
    assert dep.get_tanks() == ["a", "b", "c"]
    assert (dep.get_level("b"), dep.get_level("c")) == (30, 5)
    assert dep.get_log("b") == [("fill", 30)]
    assert dep.get_log("c") == [("fill", 5)]


def test_a_retire_tank_that_moved_nothing_still_counts():
    dep = Depot()
    for name in ["a", "b", "c"]:
        dep.add_tank(name)
    dep.fill("c", 5)
    assert dep.retire_tank("a", "c") == 0
    assert dep.get_tanks() == ["b", "c"]
    dep.undo()  # reverses the retire_tank
    assert dep.get_tanks() == ["a", "b", "c"]
    assert dep.get_log("a") == []
    dep.undo()  # then the fill of c
    assert dep.get_level("c") == 0


def test_a_tank_brought_back_works_normally(depot):
    depot.add_tank("east")
    depot.fill("east", 40)
    depot.retire_tank("east", "north")
    depot.undo()
    with pytest.raises(DepotError):
        depot.add_tank("east")  # it is in use again
    depot.fill("east", 10)
    depot.drain("east", 5)
    depot.pump("east", "south", 5)
    depot.pump("south", "east", 1)
    assert depot.pump_down("east", "south", 20) == 21
    assert depot.get_log("east") == [
        ("fill", 40),
        ("fill", 10),
        ("drain", 5),
        ("out", 5),
        ("in", 1),
        ("out", 21),
    ]
    assert depot.retire_tank("east", "north") == 20
    assert depot.get_tanks() == ["north", "south"]
    with pytest.raises(KeyError):
        depot.get_level("east")  # retired again


def test_undo_removes_an_added_tank_and_frees_its_id(depot):
    depot.add_tank("east")
    depot.undo()
    assert depot.get_tanks() == ["north", "south"]
    with pytest.raises(KeyError):
        depot.get_level("east")
    with pytest.raises(KeyError):
        depot.fill("east", 5)
    depot.add_tank("east")
    assert depot.get_tanks() == ["north", "south", "east"]
    assert depot.get_level("east") == 0
    assert depot.get_log("east") == []


def test_undoing_a_retire_and_then_the_add_frees_the_id(depot):
    depot.fill("south", 8)
    depot.retire_tank("south", "north")
    depot.undo()  # the retire_tank
    depot.undo()  # the fill of south
    depot.undo()  # the add_tank of south
    assert depot.get_tanks() == ["north"]
    assert depot.get_level("north") == 0
    depot.add_tank("south")
    assert depot.get_tanks() == ["north", "south"]
    assert depot.get_level("south") == 0
    assert depot.get_log("south") == []


# --- going back step by step ------------------------------------------------


def test_each_undo_goes_one_call_further_back():
    dep = Depot()
    calls = [
        lambda: dep.add_tank("north"),
        lambda: dep.add_tank("south"),
        lambda: dep.add_tank("east"),
        lambda: dep.fill("north", 100),
        lambda: dep.drain("north", 10),
        lambda: dep.pump("north", "south", 30),
        lambda: dep.pump_down("north", "east", 20),
        lambda: dep.pump_down("south", "east", 50),
        lambda: dep.retire_tank("east", "south"),
        lambda: dep.fill("south", 7),
        lambda: dep.retire_tank("north", "south"),
        lambda: dep.add_tank("west"),
    ]
    states = [state(dep)]
    for call in calls:
        call()
        states.append(state(dep))
    south_log = [("in", 30), ("in", 40), ("fill", 7), ("in", 20)]
    assert states[-1] == (["south", "west"], {"south": (97, south_log), "west": (0, [])})
    for expected in reversed(states[:-1]):
        dep.undo()
        assert state(dep) == expected
    with pytest.raises(DepotError):
        dep.undo()
    assert state(dep) == ([], {})


def test_failed_calls_are_not_recorded(depot):
    depot.fill("north", 10)
    for call in (
        lambda: depot.drain("north", 11),
        lambda: depot.fill("north", 0),
        lambda: depot.pump("north", "south", 11),
        lambda: depot.pump("north", "north", 5),
        lambda: depot.pump_down("north", "south", -1),
        lambda: depot.pump_down("north", "north", 0),
        lambda: depot.retire_tank("north", "east"),
        lambda: depot.retire_tank("north", "north"),
        lambda: depot.add_tank("north"),
    ):
        with pytest.raises((ValueError, KeyError, DepotError)):
            call()
    depot.undo()  # reverses the fill
    assert state(depot) == (["north", "south"], {"north": (0, []), "south": (0, [])})


def test_get_calls_are_not_recorded(depot):
    depot.fill("north", 10)
    depot.get_level("north")
    depot.get_log("north")
    depot.get_tanks()
    depot.undo()
    assert depot.get_level("north") == 0
    depot.undo()  # the add_tank of south
    assert depot.get_tanks() == ["north"]


def test_there_is_no_redo(depot):
    depot.fill("north", 10)
    depot.fill("north", 20)
    depot.undo()
    depot.undo()
    assert depot.get_level("north") == 0
    depot.fill("north", 5)
    depot.undo()
    assert depot.get_level("north") == 0
    assert depot.get_log("north") == []
    depot.undo()  # the add_tank of south, not a redo of a fill
    assert depot.get_tanks() == ["north"]
    assert depot.get_level("north") == 0


def test_undo_with_nothing_left_raises_and_changes_nothing():
    dep = Depot()
    with pytest.raises(DepotError):
        dep.undo()
    dep.add_tank("north")
    dep.undo()
    with pytest.raises(DepotError):
        dep.undo()
    assert dep.get_tanks() == []
    dep.add_tank("north")
    dep.fill("north", 3)
    assert dep.get_level("north") == 3


def test_depots_undo_separately():
    first, second = Depot(), Depot()
    first.add_tank("north")
    second.add_tank("north")
    second.fill("north", 5)
    first.undo()
    assert first.get_tanks() == []
    assert second.get_level("north") == 5
