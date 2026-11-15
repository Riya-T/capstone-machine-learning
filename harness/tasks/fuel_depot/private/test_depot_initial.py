"""Hidden tests for the initial fuel_depot spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with depot.py importable, e.g. in the sandbox):
    python -m pytest private/test_depot_initial.py
"""

import pytest
from depot import Depot, DepotError, NotEnoughFuel

# Amounts of the wrong type (1.5, "10", None, bools) are unspecified.
BAD_LITRES = [0, -5]
BAD_KEEPS = [-1, -20]


@pytest.fixture
def depot():
    dep = Depot()
    dep.add_tank("north")
    dep.add_tank("south")
    return dep


def state(dep):
    """The tank list, every level and every log, to check that a failed call
    changed nothing."""
    tanks = dep.get_tanks()
    return tanks, {t: (dep.get_level(t), dep.get_log(t)) for t in tanks}


# --- tanks ------------------------------------------------------------------


def test_a_new_tank_starts_empty(depot):
    assert depot.get_level("north") == 0
    assert depot.get_log("north") == []


def test_tanks_are_listed_in_the_order_added():
    dep = Depot()
    for name in ["west", "north", "east"]:
        dep.add_tank(name)
    assert dep.get_tanks() == ["west", "north", "east"]


def test_adding_an_id_in_use_is_rejected(depot):
    depot.fill("north", 100)
    before = state(depot)
    with pytest.raises(DepotError):
        depot.add_tank("north")
    assert state(depot) == before


def test_a_retired_id_can_be_added_again_as_a_new_tank(depot):
    depot.fill("north", 40)
    depot.drain("north", 5)
    depot.retire_tank("north", "south")
    depot.add_tank("north")
    assert depot.get_tanks() == ["south", "north"]
    assert depot.get_level("north") == 0
    assert depot.get_log("north") == []
    assert depot.get_level("south") == 35
    depot.fill("north", 3)
    assert depot.get_log("north") == [("fill", 3)]


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.fill("east", 10),
        lambda d: d.drain("east", 10),
        lambda d: d.pump("east", "south", 10),
        lambda d: d.pump("north", "east", 10),
        lambda d: d.pump_down("east", "south", 0),
        lambda d: d.pump_down("north", "east", 0),
        lambda d: d.retire_tank("east", "south"),
        lambda d: d.retire_tank("north", "east"),
        lambda d: d.get_level("east"),
        lambda d: d.get_log("east"),
        lambda d: d.get_level(None),
        lambda d: d.get_level(1),
        lambda d: d.fill(None, 10),
        lambda d: d.pump("north", 1, 10),
        lambda d: d.retire_tank("north", None),
    ],
)
def test_ids_that_are_not_tanks_raise_key_error(depot, call):
    depot.fill("north", 50)
    before = state(depot)
    with pytest.raises(KeyError):
        call(depot)
    assert state(depot) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.fill("west", 10),
        lambda d: d.drain("west", 1),
        lambda d: d.pump("west", "south", 1),
        lambda d: d.pump("north", "west", 1),
        lambda d: d.pump_down("west", "south", 0),
        lambda d: d.pump_down("north", "west", 0),
        lambda d: d.retire_tank("west", "south"),
        lambda d: d.retire_tank("north", "west"),
        lambda d: d.get_level("west"),
        lambda d: d.get_log("west"),
    ],
)
def test_a_retired_tank_is_not_in_use(depot, call):
    depot.add_tank("west")
    depot.fill("west", 30)
    depot.retire_tank("west", "south")
    depot.fill("north", 50)
    before = state(depot)
    with pytest.raises(KeyError):
        call(depot)
    assert state(depot) == before


# --- moving fuel ------------------------------------------------------------


def test_fills_and_drains_change_the_level(depot):
    depot.fill("north", 500)
    depot.fill("north", 250)
    depot.drain("north", 100)
    assert depot.get_level("north") == 650
    assert depot.get_level("south") == 0


def test_the_whole_level_can_be_drained(depot):
    depot.fill("north", 300)
    depot.drain("north", 300)
    assert depot.get_level("north") == 0


def test_overdraining_raises_and_changes_nothing(depot):
    depot.fill("north", 300)
    before = state(depot)
    with pytest.raises(NotEnoughFuel):
        depot.drain("north", 301)
    assert state(depot) == before


def test_pump_moves_fuel(depot):
    depot.fill("north", 500)
    depot.pump("north", "south", 200)
    depot.pump("south", "north", 50)
    assert (depot.get_level("north"), depot.get_level("south")) == (350, 150)


def test_the_whole_level_can_be_pumped(depot):
    depot.fill("north", 80)
    depot.pump("north", "south", 80)
    assert (depot.get_level("north"), depot.get_level("south")) == (0, 80)


def test_pumping_more_than_the_level_raises_and_changes_nothing(depot):
    depot.fill("north", 100)
    before = state(depot)
    with pytest.raises(NotEnoughFuel):
        depot.pump("north", "south", 101)
    with pytest.raises(NotEnoughFuel):
        depot.pump("south", "north", 1)
    assert state(depot) == before


def test_pump_down_leaves_keep_litres(depot):
    depot.fill("north", 500)
    depot.fill("south", 20)
    assert depot.pump_down("north", "south", 120) == 380
    assert (depot.get_level("north"), depot.get_level("south")) == (120, 400)


def test_pump_down_with_keep_zero_moves_everything(depot):
    depot.fill("north", 75)
    assert depot.pump_down("north", "south", 0) == 75
    assert (depot.get_level("north"), depot.get_level("south")) == (0, 75)


@pytest.mark.parametrize("keep", [40, 41, 1000])
def test_pump_down_with_nothing_above_keep_changes_nothing(depot, keep):
    depot.fill("north", 40)
    depot.fill("south", 5)
    before = state(depot)
    assert depot.pump_down("north", "south", keep) == 0
    assert state(depot) == before


def test_pump_down_from_an_empty_tank_moves_nothing(depot):
    depot.fill("south", 5)
    before = state(depot)
    assert depot.pump_down("north", "south", 0) == 0
    assert state(depot) == before


def test_retire_tank_moves_the_whole_level(depot):
    depot.fill("north", 90)
    depot.fill("south", 10)
    assert depot.retire_tank("north", "south") == 90
    assert depot.get_level("south") == 100
    assert depot.get_tanks() == ["south"]


def test_retiring_an_empty_tank_moves_nothing(depot):
    depot.fill("south", 10)
    assert depot.retire_tank("north", "south") == 0
    assert depot.get_tanks() == ["south"]
    assert depot.get_level("south") == 10
    assert depot.get_log("south") == [("fill", 10)]


def test_retiring_keeps_the_order_of_the_other_tanks():
    dep = Depot()
    for name in ["a", "b", "c", "d"]:
        dep.add_tank(name)
    dep.fill("b", 5)
    dep.retire_tank("b", "d")
    assert dep.get_tanks() == ["a", "c", "d"]
    dep.retire_tank("a", "c")
    assert dep.get_tanks() == ["c", "d"]
    assert dep.get_level("d") == 5


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.pump("north", "north", 10),
        lambda d: d.pump_down("north", "north", 0),
        lambda d: d.pump_down("north", "north", 10**6),
        lambda d: d.retire_tank("north", "north"),
    ],
    ids=["pump", "pump_down", "pump_down_nothing_to_move", "retire_tank"],
)
def test_the_same_tank_on_both_sides_is_rejected(depot, call):
    depot.fill("north", 100)
    before = state(depot)
    with pytest.raises(ValueError):
        call(depot)
    assert state(depot) == before


def test_retiring_an_empty_tank_into_itself_is_rejected(depot):
    with pytest.raises(ValueError):
        depot.retire_tank("north", "north")
    assert depot.get_tanks() == ["north", "south"]
    assert depot.get_log("north") == []


@pytest.mark.parametrize("litres", BAD_LITRES)
@pytest.mark.parametrize(
    "call",
    [
        lambda d, x: d.fill("north", x),
        lambda d, x: d.drain("north", x),
        lambda d, x: d.pump("north", "south", x),
    ],
    ids=["fill", "drain", "pump"],
)
def test_invalid_litres_are_rejected(depot, call, litres):
    depot.fill("north", 100)
    before = state(depot)
    with pytest.raises(ValueError):
        call(depot, litres)
    assert state(depot) == before


@pytest.mark.parametrize("keep", BAD_KEEPS)
def test_invalid_keeps_are_rejected(depot, keep):
    depot.fill("north", 100)
    before = state(depot)
    with pytest.raises(ValueError):
        depot.pump_down("north", "south", keep)
    assert state(depot) == before


# --- order of errors --------------------------------------------------------
# Which of KeyError and ValueError comes first is unspecified. An amount of
# the right type that is invalid (0 or less) is never more than a level, so
# only the same-tank ValueError can meet NotEnoughFuel.


def test_the_same_tank_is_reported_before_missing_fuel(depot):
    with pytest.raises(ValueError):
        depot.pump("north", "north", 10**6)


# --- log --------------------------------------------------------------------


def test_the_log_lists_every_movement_oldest_first(depot):
    depot.add_tank("east")
    depot.fill("north", 500)
    depot.drain("north", 20)
    depot.pump("north", "south", 80)
    depot.pump("south", "north", 30)
    depot.pump_down("north", "south", 300)
    depot.fill("east", 15)
    depot.retire_tank("east", "north")
    assert depot.get_log("north") == [
        ("fill", 500),
        ("drain", 20),
        ("out", 80),
        ("in", 30),
        ("out", 130),
        ("in", 15),
    ]
    assert depot.get_log("south") == [("in", 80), ("out", 30), ("in", 130)]
    assert (depot.get_level("north"), depot.get_level("south")) == (315, 180)


def test_a_retired_tank_logs_its_last_movement_on_the_receiver(depot):
    depot.fill("south", 1)
    depot.fill("north", 40)
    depot.retire_tank("north", "south")
    assert depot.get_log("south") == [("fill", 1), ("in", 40)]


def test_failed_calls_add_nothing_to_the_log(depot):
    depot.fill("north", 10)
    for call in (
        lambda: depot.drain("north", 11),
        lambda: depot.pump("north", "south", 11),
        lambda: depot.fill("north", 0),
        lambda: depot.pump("north", "north", 5),
        lambda: depot.pump_down("north", "north", 0),
        lambda: depot.pump_down("north", "south", -1),
        lambda: depot.retire_tank("north", "north"),
        lambda: depot.retire_tank("north", "east"),
    ):
        with pytest.raises((ValueError, KeyError, DepotError)):
            call()
    assert depot.get_log("north") == [("fill", 10)]
    assert depot.get_log("south") == []
    assert depot.get_tanks() == ["north", "south"]


def test_not_enough_fuel_is_a_depot_error():
    assert issubclass(NotEnoughFuel, DepotError)


def test_depots_do_not_share_tanks():
    first, second = Depot(), Depot()
    first.add_tank("north")
    first.fill("north", 5)
    first.add_tank("south")
    first.retire_tank("south", "north")
    assert second.get_tanks() == []
    second.add_tank("north")
    second.add_tank("south")
    assert second.get_level("north") == 0
