"""Public checks for the c_rebalance_many change (atomic operation). Shown to
the editor, never to the writer.

Usage (with bikes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_rebalance_many/public/test_rebalance_many_public.py
"""

import pytest
from bikes import BikeNetwork, DockError


@pytest.fixture
def net():
    n = BikeNetwork()
    for name in ["north", "south", "east"]:
        n.add_station(name)
    for bike in ["b1", "b2", "b3"]:
        n.dock("north", bike)
    return n


def test_moves_are_carried_out_in_order(net):
    assert net.rebalance_many([("north", "south", 2), ("north", "east", 1)]) == 3
    assert net.get_bikes("north") == []
    assert net.get_bikes("south") == ["b1", "b2"]
    assert net.get_bikes("east") == ["b3"]


def test_a_failing_move_cancels_the_moves_before_it(net):
    with pytest.raises(DockError):
        net.rebalance_many([("north", "south", 2), ("north", "east", 2)])
    assert net.get_bikes("north") == ["b1", "b2", "b3"]
    assert net.get_bikes("south") == []
    assert net.get_bikes("east") == []
