"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with network.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from network import BusNetwork, RouteError


@pytest.fixture
def net():
    n = BusNetwork()
    n.add_route("red")
    n.add_route("blue")
    return n


def test_undo_takes_back_the_last_stop_added(net):
    net.add_stop("red", "depot")
    net.add_stop("red", "market")
    net.undo()
    assert net.get_stops("red") == ["depot"]
    net.undo()
    assert net.get_stops("red") == []


def test_undo_takes_back_a_removed_stop(net):
    net.add_stop("blue", "harbor")
    net.add_stop("blue", "museum")
    net.remove_stop("blue", "museum")
    net.undo()
    assert net.get_stops("blue") == ["harbor", "museum"]


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(RouteError):
        BusNetwork().undo()
