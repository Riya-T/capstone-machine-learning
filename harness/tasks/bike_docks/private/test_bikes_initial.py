"""Hidden tests for the initial bike_docks spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with bikes.py importable, e.g. in the sandbox):
    python -m pytest private/test_bikes_initial.py
"""

import pytest
from bikes import BikeNetwork, DockError


@pytest.fixture
def net():
    n = BikeNetwork()
    for name in ["north", "south", "east"]:
        n.add_station(name)
    for bike in ["b1", "b2", "b3", "b4"]:
        n.dock("north", bike)
    n.dock("south", "b5")
    return n


def state(n):
    """Every station in order with its bikes, to check that a failed call
    changed nothing."""
    return [(s, n.get_bikes(s)) for s in n.get_stations()]


# --- stations ---------------------------------------------------------------


def test_a_new_station_has_no_bikes():
    n = BikeNetwork()
    n.add_station("north")
    assert n.get_bikes("north") == []
    assert n.get_stations() == ["north"]


def test_stations_are_listed_in_the_order_added():
    n = BikeNetwork()
    for name in ["west", "north", "east"]:
        n.add_station(name)
    assert n.get_stations() == ["west", "north", "east"]


def test_adding_a_name_in_use_is_rejected(net):
    before = state(net)
    with pytest.raises(DockError):
        net.add_station("north")
    assert state(net) == before


STATION_CALLS = [
    lambda n, s: n.dock(s, "b9"),
    lambda n, s: n.rebalance(s, "south", 1),
    lambda n, s: n.rebalance("north", s, 1),
    lambda n, s: n.close_station(s, "south"),
    lambda n, s: n.close_station("north", s),
    lambda n, s: n.get_bikes(s),
]


@pytest.mark.parametrize("call", STATION_CALLS)
def test_stations_that_were_never_added_raise_key_error(net, call):
    before = state(net)
    with pytest.raises(KeyError):
        call(net, "west")
    assert state(net) == before


@pytest.mark.parametrize("call", STATION_CALLS)
def test_a_closed_station_is_not_in_use(net, call):
    net.dock("east", "b8")
    net.close_station("east", "south")
    before = state(net)
    with pytest.raises(KeyError):
        call(net, "east")
    assert state(net) == before


# --- docking and undocking --------------------------------------------------


def test_dock_adds_the_bike_at_the_end(net):
    net.dock("north", "b6")
    net.dock("east", "b7")
    assert net.get_bikes("north") == ["b1", "b2", "b3", "b4", "b6"]
    assert net.get_bikes("east") == ["b7"]
    assert net.get_station_of("b6") == "north"
    assert net.get_station_of("b7") == "east"


def test_a_docked_bike_cannot_be_docked_again(net):
    before = state(net)
    with pytest.raises(DockError):
        net.dock("north", "b1")
    with pytest.raises(DockError):
        net.dock("east", "b5")
    assert state(net) == before


def test_undock_removes_only_that_bike(net):
    net.undock("b1")
    net.undock("b3")
    assert net.get_bikes("north") == ["b2", "b4"]
    assert net.get_bikes("south") == ["b5"]
    assert net.get_station_of("b4") == "north"


def test_an_undocked_bike_can_be_docked_again(net):
    net.undock("b2")
    net.dock("east", "b2")
    assert net.get_station_of("b2") == "east"
    net.undock("b2")
    net.dock("north", "b2")
    assert net.get_bikes("north") == ["b1", "b3", "b4", "b2"]


def test_bikes_that_are_not_docked_raise_key_error(net):
    net.undock("b5")
    before = state(net)
    for bike in ["b5", "b9"]:
        with pytest.raises(KeyError):
            net.undock(bike)
        with pytest.raises(KeyError):
            net.get_station_of(bike)
    assert state(net) == before


# --- rebalancing ------------------------------------------------------------


def test_rebalance_moves_the_first_bikes_in_their_order(net):
    net.rebalance("north", "south", 3)
    assert net.get_bikes("north") == ["b4"]
    assert net.get_bikes("south") == ["b5", "b1", "b2", "b3"]
    assert net.get_station_of("b2") == "south"
    assert net.get_station_of("b4") == "north"


def test_rebalance_of_every_bike_leaves_the_station_in_use(net):
    net.rebalance("north", "east", 4)
    assert net.get_bikes("north") == []
    assert net.get_bikes("east") == ["b1", "b2", "b3", "b4"]
    assert net.get_stations() == ["north", "south", "east"]
    net.dock("north", "b6")
    assert net.get_bikes("north") == ["b6"]


def test_rebalanced_bikes_go_after_the_bikes_already_there(net):
    net.rebalance("north", "south", 1)
    net.rebalance("south", "east", 1)
    net.rebalance("north", "east", 2)
    assert net.get_bikes("east") == ["b5", "b2", "b3"]
    assert net.get_bikes("south") == ["b1"]


def test_rebalancing_more_bikes_than_there_are_changes_nothing(net):
    before = state(net)
    with pytest.raises(DockError):
        net.rebalance("north", "south", 5)
    with pytest.raises(DockError):
        net.rebalance("east", "south", 1)
    assert state(net) == before


@pytest.mark.parametrize("count", [0, -2])
def test_rebalance_counts_of_0_or_less_are_rejected(net, count):
    before = state(net)
    with pytest.raises(ValueError):
        net.rebalance("north", "south", count)
    assert state(net) == before


# --- closing ----------------------------------------------------------------


def test_close_station_moves_every_bike_and_closes_it(net):
    net.dock("east", "b6")
    assert net.close_station("north", "east") == 4
    assert net.get_stations() == ["south", "east"]
    assert net.get_bikes("east") == ["b6", "b1", "b2", "b3", "b4"]
    assert net.get_station_of("b1") == "east"
    assert net.get_station_of("b4") == "east"


def test_closing_an_empty_station_moves_nothing(net):
    assert net.close_station("east", "north") == 0
    assert net.get_stations() == ["north", "south"]
    assert net.get_bikes("north") == ["b1", "b2", "b3", "b4"]


def test_the_other_stations_keep_their_order_after_a_close(net):
    net.add_station("west")
    net.close_station("south", "west")
    assert net.get_stations() == ["north", "east", "west"]
    assert net.get_bikes("west") == ["b5"]
    assert net.get_station_of("b5") == "west"


@pytest.mark.parametrize(
    "call",
    [
        lambda n: n.rebalance("north", "north", 1),
        lambda n: n.close_station("north", "north"),
        lambda n: n.close_station("east", "east"),
    ],
    ids=["rebalance", "close_station", "close_empty_station"],
)
def test_the_same_station_on_both_sides_is_rejected(net, call):
    before = state(net)
    with pytest.raises(ValueError):
        call(net)
    assert state(net) == before


# --- general ----------------------------------------------------------------


def test_networks_do_not_share_stations():
    first, second = BikeNetwork(), BikeNetwork()
    first.add_station("north")
    first.dock("north", "b1")
    assert second.get_stations() == []
    second.add_station("north")
    second.dock("north", "b1")
    assert second.get_bikes("north") == ["b1"]
    assert first.get_bikes("north") == ["b1"]
