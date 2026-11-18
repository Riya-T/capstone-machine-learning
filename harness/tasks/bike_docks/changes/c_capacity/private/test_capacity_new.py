"""Hidden tests for the c_capacity change (validation rule). Never shown to
the writer or the editor.

Usage (with bikes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from bikes import BikeNetwork, DockError, StationFull


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
    return [(s, n.get_bikes(s), n.get_capacity(s)) for s in n.get_stations()]


# --- setting a capacity -----------------------------------------------------


def test_station_full_is_a_dock_error():
    assert issubclass(StationFull, DockError)


def test_every_new_station_has_no_capacity(net):
    assert [net.get_capacity(s) for s in net.get_stations()] == [None, None, None]


def test_each_call_replaces_the_capacity(net):
    net.set_capacity("east", 3)
    net.set_capacity("east", 1)
    assert net.get_capacity("east") == 1
    net.set_capacity("east", None)
    assert net.get_capacity("east") is None
    net.dock("east", "b6")
    net.dock("east", "b7")
    assert net.get_bikes("east") == ["b6", "b7"]


def test_capacities_belong_to_one_station(net):
    net.set_capacity("south", 2)
    assert net.get_capacity("north") is None
    assert net.get_capacity("east") is None


@pytest.mark.parametrize("capacity", [0, -1])
def test_capacities_of_0_or_less_are_rejected(net, capacity):
    net.set_capacity("east", 2)
    with pytest.raises(ValueError):
        net.set_capacity("east", capacity)
    assert net.get_capacity("east") == 2


def test_stations_not_in_use_raise_key_error(net):
    net.close_station("east", "south")
    for name in ["east", "west"]:
        with pytest.raises(KeyError):
            net.set_capacity(name, 2)
        with pytest.raises(KeyError):
            net.get_capacity(name)


def test_set_capacity_changes_no_bikes(net):
    before = [(s, net.get_bikes(s)) for s in net.get_stations()]
    net.set_capacity("north", 1)
    assert [(s, net.get_bikes(s)) for s in net.get_stations()] == before


# --- dock -------------------------------------------------------------------


def test_a_station_can_be_filled_up_to_its_capacity(net):
    net.set_capacity("east", 2)
    net.dock("east", "b6")
    net.dock("east", "b7")
    assert net.get_bikes("east") == ["b6", "b7"]
    before = state(net)
    with pytest.raises(StationFull):
        net.dock("east", "b8")
    assert state(net) == before
    with pytest.raises(KeyError):
        net.get_station_of("b8")


def test_a_full_station_takes_bikes_again_once_one_leaves(net):
    net.set_capacity("south", 1)
    with pytest.raises(StationFull):
        net.dock("south", "b6")
    net.undock("b5")
    net.dock("south", "b6")
    assert net.get_bikes("south") == ["b6"]


# --- rebalance and close_station --------------------------------------------


def test_rebalance_may_fill_the_station_exactly(net):
    net.set_capacity("south", 3)
    net.rebalance("north", "south", 2)
    assert net.get_bikes("south") == ["b5", "b1", "b2"]
    before = state(net)
    with pytest.raises(StationFull):
        net.rebalance("north", "south", 1)
    assert state(net) == before


def test_a_rebalance_that_does_not_fit_moves_nothing(net):
    net.set_capacity("east", 3)
    before = state(net)
    with pytest.raises(StationFull):
        net.rebalance("north", "east", 4)
    assert state(net) == before
    assert net.get_station_of("b1") == "north"


def test_close_station_into_a_station_without_room_closes_nothing(net):
    net.set_capacity("south", 4)
    before = state(net)
    with pytest.raises(StationFull):
        net.close_station("north", "south")
    assert state(net) == before
    assert net.get_stations() == ["north", "south", "east"]
    assert net.get_station_of("b4") == "north"


def test_close_station_that_fits_still_works(net):
    net.set_capacity("south", 5)
    assert net.close_station("north", "south") == 4
    assert net.get_bikes("south") == ["b5", "b1", "b2", "b3", "b4"]
    assert net.get_stations() == ["south", "east"]


# --- bikes already there and the station bikes leave ------------------------


def test_a_capacity_below_the_bikes_there_keeps_them(net):
    net.set_capacity("north", 2)
    assert net.get_bikes("north") == ["b1", "b2", "b3", "b4"]
    with pytest.raises(StationFull):
        net.dock("north", "b6")
    net.rebalance("north", "east", 1)
    net.undock("b4")
    assert net.get_bikes("north") == ["b2", "b3"]
    with pytest.raises(StationFull):
        net.rebalance("east", "north", 1)


def test_the_capacity_of_the_station_bikes_leave_is_not_checked(net):
    net.set_capacity("north", 1)
    net.rebalance("north", "south", 2)
    assert net.close_station("north", "east") == 2
    assert net.get_bikes("east") == ["b3", "b4"]
