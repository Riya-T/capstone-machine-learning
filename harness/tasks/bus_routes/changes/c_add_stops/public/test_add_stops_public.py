"""Public checks for the c_add_stops change (several stops in one call).
Shown to the editor, never to the writer.

Usage (with network.py importable, e.g. in the sandbox):
    python -m pytest changes/c_add_stops/public/test_add_stops_public.py
"""

import pytest
from network import BusNetwork, RouteError


@pytest.fixture
def net():
    n = BusNetwork()
    n.add_route("red")
    n.add_stop("red", "depot")
    return n


def test_add_stops_adds_them_at_the_end_in_order(net):
    assert net.add_stops("red", ["market", "park", "school"]) == 3
    assert net.get_stops("red") == ["depot", "market", "park", "school"]


def test_a_stop_already_on_the_route_adds_none(net):
    with pytest.raises(RouteError):
        net.add_stops("red", ["market", "depot"])
    assert net.get_stops("red") == ["depot"]
