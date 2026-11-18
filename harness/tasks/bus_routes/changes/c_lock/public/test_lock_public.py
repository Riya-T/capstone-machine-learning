"""Public checks for the c_lock change (locked routes). Shown to the editor,
never to the writer.

Usage (with network.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/public/test_lock_public.py
"""

import pytest
from network import BusNetwork, RouteLocked


@pytest.fixture
def net():
    n = BusNetwork()
    n.add_route("red")
    n.add_route("blue")
    n.add_stop("red", "depot")
    n.add_stop("red", "market")
    return n


def test_a_locked_route_refuses_new_stops(net):
    assert net.is_locked("red") is False
    net.lock_route("red")
    assert net.is_locked("red") is True
    with pytest.raises(RouteLocked):
        net.add_stop("red", "park")
    assert net.get_stops("red") == ["depot", "market"]
    net.add_stop("blue", "park")
    assert net.get_stops("blue") == ["park"]


def test_an_unlocked_route_can_change_again(net):
    net.lock_route("red")
    net.unlock_route("red")
    assert net.is_locked("red") is False
    net.remove_stop("red", "depot")
    assert net.get_stops("red") == ["market"]
