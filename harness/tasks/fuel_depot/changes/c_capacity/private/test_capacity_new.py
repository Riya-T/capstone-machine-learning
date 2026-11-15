"""Hidden tests for the c_capacity change (tank capacities). Never shown to
the writer or the editor.

c_capacity is the first change of s1 and the second of s2, after c_undo.
The tests at the end check that a call that raises Overflow is not recorded
for undo; they return early, and so pass, when the depot has no undo (s1).
A skipped test would count as failed.

Usage (with depot.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from depot import Depot, DepotError, NotEnoughFuel, Overflow

BAD_CAPACITIES = [-1, 1.5, "10"]


@pytest.fixture
def depot():
    dep = Depot()
    dep.add_tank("north")
    dep.add_tank("south")
    return dep


def state(dep):
    """The tank list, every level, log and capacity, to check that a failed
    call changed nothing."""
    tanks = dep.get_tanks()
    return tanks, {t: (dep.get_level(t), dep.get_log(t), dep.get_capacity(t)) for t in tanks}


# --- setting and reading capacities -----------------------------------------


def test_every_tank_starts_without_a_capacity(depot):
    assert depot.get_capacity("north") is None
    assert depot.get_capacity("south") is None
    depot.fill("north", 10**9)
    assert depot.get_level("north") == 10**9


def test_set_capacity_replaces_the_capacity(depot):
    depot.set_capacity("north", 100)
    assert depot.get_capacity("north") == 100
    depot.set_capacity("north", 0)
    assert depot.get_capacity("north") == 0
    depot.set_capacity("north", None)
    assert depot.get_capacity("north") is None
    depot.fill("north", 500)
    assert depot.get_level("north") == 500


def test_capacities_belong_to_one_tank(depot):
    depot.set_capacity("north", 10)
    assert depot.get_capacity("south") is None
    depot.fill("south", 50)
    assert depot.get_level("south") == 50


@pytest.mark.parametrize("capacity", BAD_CAPACITIES)
def test_invalid_capacities_are_rejected(depot, capacity):
    depot.set_capacity("north", 50)
    before = state(depot)
    with pytest.raises(ValueError):
        depot.set_capacity("north", capacity)
    assert state(depot) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.set_capacity("east", 10),
        lambda d: d.get_capacity("east"),
        lambda d: d.set_capacity("west", 10),
        lambda d: d.get_capacity("west"),
        lambda d: d.set_capacity(None, 10),
        lambda d: d.get_capacity(1),
        lambda d: d.set_capacity("east", -1),
    ],
)
def test_capacity_methods_raise_key_error_for_tanks_not_in_use(depot, call):
    depot.add_tank("west")
    depot.retire_tank("west", "north")
    with pytest.raises(KeyError):
        call(depot)


def test_setting_a_capacity_adds_nothing_to_the_log(depot):
    depot.fill("north", 20)
    depot.set_capacity("north", 5)
    depot.set_capacity("north", None)
    assert depot.get_log("north") == [("fill", 20)]
    assert depot.get_level("north") == 20


def test_overflow_is_a_depot_error_of_its_own():
    assert issubclass(Overflow, DepotError)
    assert not issubclass(Overflow, NotEnoughFuel)
    assert not issubclass(NotEnoughFuel, Overflow)


# --- fill -------------------------------------------------------------------


def test_fill_may_reach_exactly_the_capacity(depot):
    depot.set_capacity("north", 100)
    depot.fill("north", 60)
    depot.fill("north", 40)
    assert depot.get_level("north") == 100


def test_fill_past_the_capacity_raises_and_changes_nothing(depot):
    depot.set_capacity("north", 100)
    depot.fill("north", 60)
    before = state(depot)
    with pytest.raises(Overflow):
        depot.fill("north", 41)
    assert state(depot) == before


def test_a_capacity_of_zero_takes_nothing(depot):
    depot.set_capacity("north", 0)
    with pytest.raises(Overflow):
        depot.fill("north", 1)
    assert depot.get_level("north") == 0
    assert depot.get_log("north") == []


def test_a_capacity_below_the_level(depot):
    depot.fill("north", 50)
    depot.set_capacity("north", 30)
    assert depot.get_level("north") == 50
    with pytest.raises(Overflow):
        depot.fill("north", 1)
    depot.drain("north", 25)
    depot.fill("north", 5)
    assert depot.get_level("north") == 30
    with pytest.raises(Overflow):
        depot.fill("north", 1)
    assert depot.get_log("north") == [("fill", 50), ("drain", 25), ("fill", 5)]


def test_drain_ignores_the_capacity(depot):
    depot.fill("north", 50)
    depot.set_capacity("north", 10)
    depot.drain("north", 5)
    assert depot.get_level("north") == 45


# --- pump -------------------------------------------------------------------


def test_pump_into_the_receiving_tank_up_to_its_capacity(depot):
    depot.fill("north", 100)
    depot.fill("south", 20)
    depot.set_capacity("south", 50)
    depot.pump("north", "south", 30)
    assert (depot.get_level("north"), depot.get_level("south")) == (70, 50)


def test_pump_past_the_receivers_capacity_raises_and_changes_nothing(depot):
    depot.fill("north", 100)
    depot.fill("south", 20)
    depot.set_capacity("south", 50)
    before = state(depot)
    with pytest.raises(Overflow):
        depot.pump("north", "south", 31)
    assert state(depot) == before


def test_pump_into_a_tank_above_its_capacity_raises(depot):
    depot.fill("north", 100)
    depot.fill("south", 40)
    depot.set_capacity("south", 10)
    before = state(depot)
    with pytest.raises(Overflow):
        depot.pump("north", "south", 1)
    assert state(depot) == before


# --- pump_down --------------------------------------------------------------


def test_pump_down_into_the_receiving_tank_up_to_its_capacity(depot):
    depot.fill("north", 100)
    depot.fill("south", 10)
    depot.set_capacity("south", 70)
    assert depot.pump_down("north", "south", 40) == 60
    assert (depot.get_level("north"), depot.get_level("south")) == (40, 70)
    assert depot.get_log("south") == [("fill", 10), ("in", 60)]


def test_pump_down_past_the_receivers_capacity_raises_and_changes_nothing(depot):
    depot.fill("north", 100)
    depot.fill("south", 10)
    depot.set_capacity("south", 70)
    before = state(depot)
    # It never moves less to make room: 61 litres do not fit, so nothing moves.
    with pytest.raises(Overflow):
        depot.pump_down("north", "south", 39)
    with pytest.raises(Overflow):
        depot.pump_down("north", "south", 0)
    assert state(depot) == before


def test_pump_down_moving_nothing_never_overflows(depot):
    depot.fill("north", 30)
    depot.fill("south", 80)
    depot.set_capacity("south", 50)  # south is already above its capacity
    before = state(depot)
    assert depot.pump_down("north", "south", 30) == 0
    assert depot.pump_down("north", "south", 100) == 0
    assert state(depot) == before
    depot.set_capacity("north", 0)  # north is now above its capacity too
    assert depot.pump_down("south", "north", 80) == 0
    assert (depot.get_level("north"), depot.get_level("south")) == (30, 80)
    assert depot.get_log("north") == [("fill", 30)]


# --- retire_tank ------------------------------------------------------------


def test_retire_tank_into_the_receiving_tank_up_to_its_capacity(depot):
    depot.fill("north", 45)
    depot.fill("south", 5)
    depot.set_capacity("south", 50)
    assert depot.retire_tank("north", "south") == 45
    assert depot.get_level("south") == 50
    assert depot.get_tanks() == ["south"]


def test_retire_tank_past_the_receivers_capacity_raises_and_changes_nothing(depot):
    depot.fill("north", 46)
    depot.fill("south", 5)
    depot.set_capacity("south", 50)
    before = state(depot)
    with pytest.raises(Overflow):
        depot.retire_tank("north", "south")
    assert state(depot) == before
    assert depot.get_tanks() == ["north", "south"]
    depot.fill("north", 1)
    assert depot.get_level("north") == 47


def test_retiring_an_empty_tank_never_overflows(depot):
    depot.fill("south", 80)
    depot.set_capacity("south", 50)  # south is already above its capacity
    assert depot.retire_tank("north", "south") == 0
    assert depot.get_tanks() == ["south"]
    assert depot.get_level("south") == 80
    assert depot.get_log("south") == [("fill", 80)]


# --- the sending tank -------------------------------------------------------


def test_the_sending_tanks_capacity_plays_no_part():
    dep = Depot()
    for name in ["a", "b", "c", "d"]:
        dep.add_tank(name)
    dep.fill("a", 100)
    dep.set_capacity("a", 0)  # a is far above its capacity, and can still give fuel
    dep.pump("a", "b", 10)
    assert dep.pump_down("a", "c", 50) == 40
    assert dep.retire_tank("a", "d") == 50
    assert [dep.get_level(t) for t in ["b", "c", "d"]] == [10, 40, 50]


# --- order of errors --------------------------------------------------------


@pytest.mark.parametrize(
    "call, error",
    [
        (lambda d: d.fill("east", 5), KeyError),
        (lambda d: d.fill("south", 0), ValueError),
        (lambda d: d.pump("north", "east", 5), KeyError),
        (lambda d: d.pump("north", "south", -5), ValueError),
        (lambda d: d.pump("south", "south", 5), ValueError),
        (lambda d: d.pump("north", "south", 51), NotEnoughFuel),
        (lambda d: d.pump_down("north", "east", 0), KeyError),
        (lambda d: d.pump_down("north", "south", -1), ValueError),
        (lambda d: d.pump_down("south", "south", 0), ValueError),
        (lambda d: d.retire_tank("north", "east"), KeyError),
        (lambda d: d.retire_tank("south", "south"), ValueError),
    ],
)
def test_other_errors_come_before_overflow(depot, call, error):
    # Every call below would also overflow south, which is full.
    depot.fill("north", 50)
    depot.fill("south", 10)
    depot.set_capacity("south", 10)
    before = state(depot)
    with pytest.raises(error):
        call(depot)
    assert state(depot) == before


def test_failed_calls_add_nothing_to_the_logs(depot):
    depot.fill("north", 30)
    depot.set_capacity("south", 5)
    for call in (
        lambda: depot.pump("north", "south", 6),
        lambda: depot.pump_down("north", "south", 0),
        lambda: depot.retire_tank("north", "south"),
    ):
        with pytest.raises(Overflow):
            call()
    assert depot.get_log("north") == [("fill", 30)]
    assert depot.get_log("south") == []
    assert depot.get_tanks() == ["north", "south"]


# --- with undo (s2 only) ----------------------------------------------------


def undo_depot():
    """north holds 40 and south 5 of its capacity of 10; the last call undo
    can reverse is the fill of south. None if the depot has no undo."""
    dep = Depot()
    if not hasattr(dep, "undo"):
        return None
    dep.add_tank("north")
    dep.add_tank("south")
    dep.fill("north", 40)
    dep.set_capacity("south", 10)
    dep.fill("south", 5)
    return dep


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.fill("south", 6),
        lambda d: d.pump("north", "south", 6),
        lambda d: d.pump_down("north", "south", 0),
        lambda d: d.retire_tank("north", "south"),
    ],
    ids=["fill", "pump", "pump_down", "retire_tank"],
)
def test_a_call_that_overflows_is_not_recorded_for_undo(call):
    dep = undo_depot()
    if dep is None:
        return
    with pytest.raises(Overflow):
        call(dep)
    dep.undo()  # reverses the fill of south, the last call that succeeded
    assert dep.get_tanks() == ["north", "south"]
    assert (dep.get_level("north"), dep.get_level("south")) == (40, 0)
    assert dep.get_log("south") == []
    dep.undo()  # then the fill of north
    assert dep.get_level("north") == 0
    assert dep.get_log("north") == []
