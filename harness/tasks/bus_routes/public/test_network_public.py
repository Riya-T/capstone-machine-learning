"""Public checks for network.py.

Usage (with network.py importable, e.g. in the sandbox):
    python -m pytest public/test_network_public.py
"""

import pytest
from network import BusNetwork, RouteError


@pytest.fixture
def net():
    n = BusNetwork()
    n.add_route("red")
    n.add_route("blue")
    for stop in ["depot", "market", "park", "school"]:
        n.add_stop("red", stop)
    for stop in ["harbor", "market"]:
        n.add_stop("blue", stop)
    return n


def test_routes_and_stops_are_listed_in_the_order_added(net):
    assert net.get_routes() == ["red", "blue"]
    assert net.get_stops("red") == ["depot", "market", "park", "school"]
    assert net.get_stops("blue") == ["harbor", "market"]


def test_a_route_has_each_stop_once(net):
    with pytest.raises(RouteError):
        net.add_stop("red", "park")
    assert net.get_stops("red") == ["depot", "market", "park", "school"]


def test_retire_stop_removes_it_from_every_route(net):
    assert net.retire_stop("market") == 2
    assert net.get_stops("red") == ["depot", "park", "school"]
    assert net.get_stops("blue") == ["harbor"]
    assert net.retire_stop("market") == 0  # on no route any more


def test_split_route_moves_the_stop_and_those_after_it(net):
    assert net.split_route("red", "park", "red-east") == 2
    assert net.get_routes() == ["red", "blue", "red-east"]
    assert net.get_stops("red") == ["depot", "market"]
    assert net.get_stops("red-east") == ["park", "school"]


def test_split_at_the_first_stop_leaves_the_route_empty(net):
    assert net.split_route("blue", "harbor", "green") == 2
    assert net.get_stops("blue") == []
    assert net.get_stops("green") == ["harbor", "market"]


def test_a_removed_route_is_gone_and_its_name_is_free(net):
    net.remove_route("red")
    assert net.get_routes() == ["blue"]
    with pytest.raises(KeyError):
        net.get_stops("red")
    net.add_route("red")
    assert net.get_routes() == ["blue", "red"]
    assert net.get_stops("red") == []
