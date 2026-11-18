"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with bikes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from bikes import BikeNetwork, DockError


@pytest.fixture
def net():
    n = BikeNetwork()
    n.add_station("north")
    n.add_station("south")
    return n


def test_undo_takes_back_the_last_dock(net):
    net.dock("north", "b1")
    net.dock("north", "b2")
    net.undo()
    assert net.get_bikes("north") == ["b1"]
    net.undo()
    assert net.get_bikes("north") == []


def test_undo_takes_back_a_rebalance(net):
    for bike in ["b1", "b2", "b3"]:
        net.dock("north", bike)
    net.rebalance("north", "south", 2)
    net.undo()
    assert net.get_bikes("north") == ["b1", "b2", "b3"]
    assert net.get_bikes("south") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(DockError):
        BikeNetwork().undo()
