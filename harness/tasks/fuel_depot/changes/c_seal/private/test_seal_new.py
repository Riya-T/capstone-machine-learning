"""Hidden tests for the c_seal change (sealed tanks). Never shown to the
writer or the editor.

c_seal is the second change of s1, after c_capacity, so these tests also use
capacities. That capacities still hold for every method is checked by the
c_capacity tests, which are rerun after this change.

Usage (with depot.py importable, e.g. in the sandbox):
    python -m pytest changes/c_seal/private/test_seal_new.py
"""

import pytest
from depot import Depot, DepotError, NotEnoughFuel, Overflow, Sealed


@pytest.fixture
def depot():
    """north and south hold 50 litres each; north is sealed; east is empty."""
    dep = Depot()
    for name in ["north", "south", "east"]:
        dep.add_tank(name)
    dep.fill("north", 50)
    dep.fill("south", 50)
    dep.seal("north")
    return dep


def state(dep):
    """The tank list, every level, log and capacity, to check that a failed
    call changed nothing."""
    tanks = dep.get_tanks()
    return tanks, {t: (dep.get_level(t), dep.get_log(t), dep.get_capacity(t)) for t in tanks}


# --- sealing and unsealing --------------------------------------------------


def test_new_tanks_are_not_sealed():
    dep = Depot()
    dep.add_tank("north")
    dep.add_tank("south")
    dep.fill("north", 30)
    dep.drain("north", 5)
    dep.pump("north", "south", 5)
    assert dep.pump_down("north", "south", 10) == 10
    assert dep.retire_tank("north", "south") == 10
    assert dep.get_level("south") == 25


@pytest.mark.parametrize("method", ["seal", "unseal"])
@pytest.mark.parametrize("tank_id", ["west", "retired", None, 1])
def test_seal_and_unseal_raise_key_error_for_tanks_not_in_use(depot, method, tank_id):
    depot.add_tank("retired")
    depot.retire_tank("retired", "south")
    with pytest.raises(KeyError):
        getattr(depot, method)(tank_id)


def test_sealing_twice_or_unsealing_twice_is_harmless(depot):
    depot.seal("north")
    with pytest.raises(Sealed):
        depot.fill("north", 1)
    depot.unseal("north")
    depot.unseal("north")
    depot.fill("north", 1)
    depot.unseal("east")  # never sealed: nothing happens
    depot.fill("east", 1)
    assert (depot.get_level("north"), depot.get_level("east")) == (51, 1)


def test_sealed_is_a_depot_error_of_its_own():
    assert issubclass(Sealed, DepotError)
    assert not issubclass(Sealed, NotEnoughFuel)
    assert not issubclass(Sealed, Overflow)


def test_sealing_adds_nothing_to_the_log(depot):
    depot.unseal("north")
    depot.seal("south")
    depot.unseal("south")
    assert depot.get_log("north") == [("fill", 50)]
    assert depot.get_log("south") == [("fill", 50)]


# --- movements --------------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.fill("north", 10),
        lambda d: d.drain("north", 10),
        lambda d: d.pump("north", "south", 10),
        lambda d: d.pump("south", "north", 10),
        lambda d: d.pump_down("north", "south", 0),
        lambda d: d.pump_down("south", "north", 0),
        lambda d: d.retire_tank("north", "south"),
        lambda d: d.retire_tank("south", "north"),
    ],
    ids=[
        "fill",
        "drain",
        "pump_from",
        "pump_to",
        "pump_down_from",
        "pump_down_to",
        "retire_tank_from",
        "retire_tank_to",
    ],
)
def test_every_movement_that_names_a_sealed_tank_is_refused(depot, call):
    before = state(depot)
    with pytest.raises(Sealed):
        call(depot)
    assert state(depot) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.pump_down("north", "south", 50),
        lambda d: d.pump_down("north", "south", 1000),
        lambda d: d.pump_down("east", "north", 0),
        lambda d: d.retire_tank("east", "north"),
        lambda d: d.retire_tank("empty", "south"),
    ],
    ids=[
        "pump_down_from_at_keep",
        "pump_down_from_below_keep",
        "pump_down_to_from_empty",
        "retire_empty_into_sealed",
        "retire_sealed_empty",
    ],
)
def test_a_sealed_tank_is_refused_even_when_nothing_would_move(depot, call):
    depot.add_tank("empty")
    depot.seal("empty")
    before = state(depot)
    with pytest.raises(Sealed):
        call(depot)
    assert state(depot) == before
    assert depot.get_tanks() == ["north", "south", "east", "empty"]


def test_tanks_not_named_in_the_call_are_not_affected(depot):
    depot.pump("south", "east", 10)
    assert depot.pump_down("south", "east", 30) == 10
    depot.fill("east", 5)
    depot.drain("east", 5)
    assert depot.retire_tank("south", "east") == 30
    assert depot.get_level("east") == 50
    assert depot.get_level("north") == 50


def test_an_unsealed_tank_takes_part_in_movements_again(depot):
    depot.unseal("north")
    depot.fill("north", 10)
    depot.drain("north", 20)
    depot.pump("north", "south", 10)
    depot.pump("south", "north", 5)
    assert depot.pump_down("north", "east", 30) == 5
    assert depot.retire_tank("north", "south") == 30
    assert depot.get_level("south") == 85
    assert depot.get_tanks() == ["south", "east"]


def test_calls_that_move_no_fuel_work_on_a_sealed_tank(depot):
    assert depot.get_level("north") == 50
    assert depot.get_log("north") == [("fill", 50)]
    assert depot.get_tanks() == ["north", "south", "east"]
    depot.set_capacity("north", 80)
    assert depot.get_capacity("north") == 80
    depot.add_tank("west")
    depot.seal("west")
    assert depot.get_tanks() == ["north", "south", "east", "west"]
    with pytest.raises(DepotError):
        depot.add_tank("north")


# --- order of errors --------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.pump("north", "west", 5),
        lambda d: d.pump("west", "north", 5),
        lambda d: d.pump_down("north", "west", 0),
        lambda d: d.retire_tank("north", "west"),
        lambda d: d.retire_tank("west", "north"),
    ],
)
def test_a_tank_not_in_use_is_reported_before_a_sealed_one(depot, call):
    before = state(depot)
    with pytest.raises(KeyError):
        call(depot)
    assert state(depot) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.fill("north", 0),
        lambda d: d.drain("north", -1),
        lambda d: d.pump("north", "south", 0),
        lambda d: d.pump("south", "north", -5),
        lambda d: d.pump_down("north", "south", -1),
        lambda d: d.pump_down("south", "north", -3),
        lambda d: d.pump("north", "north", 5),
        lambda d: d.pump_down("north", "north", 0),
        lambda d: d.retire_tank("north", "north"),
    ],
)
def test_value_errors_are_reported_before_a_sealed_tank(depot, call):
    before = state(depot)
    with pytest.raises(ValueError):
        call(depot)
    assert state(depot) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.drain("north", 10**6),
        lambda d: d.pump("north", "south", 10**6),
        lambda d: d.pump("south", "north", 10**6),
    ],
)
def test_a_sealed_tank_is_reported_before_missing_fuel(depot, call):
    before = state(depot)
    with pytest.raises(Sealed):
        call(depot)
    assert state(depot) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.fill("north", 1),
        lambda d: d.pump("south", "north", 1),
        lambda d: d.pump_down("south", "north", 0),
        lambda d: d.retire_tank("south", "north"),
    ],
    ids=["fill", "pump", "pump_down", "retire_tank"],
)
def test_a_sealed_tank_is_reported_before_an_overflow(depot, call):
    depot.set_capacity("north", 50)  # north is full
    before = state(depot)
    with pytest.raises(Sealed):
        call(depot)
    assert state(depot) == before


def test_an_unsealed_tank_still_respects_its_capacity(depot):
    depot.set_capacity("north", 60)
    depot.unseal("north")
    with pytest.raises(Overflow):
        depot.fill("north", 11)
    with pytest.raises(Overflow):
        depot.pump("south", "north", 11)
    depot.fill("north", 10)
    assert depot.get_level("north") == 60
