"""Public checks for bikes.py.

Usage (with bikes.py importable, e.g. in the sandbox):
    python -m pytest public/test_bikes_public.py
"""

import pytest
from bikes import BikeNetwork, DockError


@pytest.fixture
def net():
    n = BikeNetwork()
    n.add_station("north")
    n.add_station("south")
    return n


def test_bikes_are_listed_in_the_order_they_were_docked(net):
    net.dock("north", "b1")
    net.dock("north", "b2")
    net.dock("south", "b3")
    assert net.get_bikes("north") == ["b1", "b2"]
    assert net.get_station_of("b3") == "south"
    assert net.get_stations() == ["north", "south"]


def test_docking_a_bike_twice_raises(net):
    net.dock("north", "b1")
    with pytest.raises(DockError):
        net.dock("south", "b1")
    assert net.get_bikes("south") == []


def test_undock_keeps_the_order_of_the_other_bikes(net):
    for bike in ["b1", "b2", "b3"]:
        net.dock("north", bike)
    net.undock("b2")
    assert net.get_bikes("north") == ["b1", "b3"]
    with pytest.raises(KeyError):
        net.get_station_of("b2")


def test_rebalance_moves_the_first_bikes_to_the_end(net):
    for bike in ["b1", "b2", "b3"]:
        net.dock("north", bike)
    net.dock("south", "b4")
    net.rebalance("north", "south", 2)
    assert net.get_bikes("north") == ["b3"]
    assert net.get_bikes("south") == ["b4", "b1", "b2"]


def test_rebalancing_more_bikes_than_there_are_raises(net):
    net.dock("north", "b1")
    with pytest.raises(DockError):
        net.rebalance("north", "south", 2)
    assert net.get_bikes("north") == ["b1"]
    assert net.get_bikes("south") == []


def test_a_closed_station_is_gone(net):
    net.dock("north", "b1")
    net.dock("south", "b2")
    assert net.close_station("north", "south") == 1
    assert net.get_stations() == ["south"]
    assert net.get_bikes("south") == ["b2", "b1"]
    with pytest.raises(KeyError):
        net.get_bikes("north")
