"""Public checks for the c_capacity change (validation rule). Shown to the
editor, never to the writer.

Usage (with bikes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

import pytest
from bikes import BikeNetwork, StationFull


@pytest.fixture
def net():
    n = BikeNetwork()
    n.add_station("north")
    n.add_station("south")
    return n


def test_a_new_station_has_no_capacity(net):
    assert net.get_capacity("north") is None
    net.set_capacity("north", 2)
    assert net.get_capacity("north") == 2


def test_docking_at_a_full_station_raises(net):
    net.set_capacity("north", 1)
    net.dock("north", "b1")
    with pytest.raises(StationFull):
        net.dock("north", "b2")
    assert net.get_bikes("north") == ["b1"]


def test_rebalance_into_a_station_without_room_raises(net):
    for bike in ["b1", "b2", "b3"]:
        net.dock("north", bike)
    net.set_capacity("south", 2)
    with pytest.raises(StationFull):
        net.rebalance("north", "south", 3)
    assert net.get_bikes("north") == ["b1", "b2", "b3"]
    assert net.get_bikes("south") == []
