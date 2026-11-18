"""Hidden tests for the c_add_stops change (several stops in one call).
Never shown to the writer or the editor.

Usage (with network.py importable, e.g. in the sandbox):
    python -m pytest changes/c_add_stops/private/test_add_stops_new.py
"""

import pytest
from network import BusNetwork, RouteError


@pytest.fixture
def net():
    n = BusNetwork()
    for name in ["red", "blue", "green"]:
        n.add_route(name)
    for stop in ["depot", "market"]:
        n.add_stop("red", stop)
    n.add_stop("blue", "harbor")
    return n


def state(n):
    return [(r, list(n.get_stops(r))) for r in list(n.get_routes())]


def test_add_stops_appends_in_the_order_given(net):
    assert net.add_stops("red", ["school", "park", "zoo"]) == 3
    assert net.get_stops("red") == ["depot", "market", "school", "park", "zoo"]


def test_add_stops_to_an_empty_route(net):
    assert net.add_stops("green", ["mill"]) == 1
    assert net.get_stops("green") == ["mill"]


def test_add_stops_only_changes_its_route(net):
    net.add_stops("blue", ["market", "museum"])
    assert net.get_stops("blue") == ["harbor", "market", "museum"]
    assert net.get_stops("red") == ["depot", "market"]
    assert net.get_routes() == ["red", "blue", "green"]


def test_stops_on_other_routes_may_be_added(net):
    assert net.add_stops("green", ["depot", "harbor"]) == 2
    assert net.get_stops("green") == ["depot", "harbor"]


@pytest.mark.parametrize(
    "stops",
    [
        ["depot"],
        ["park", "depot"],
        ["park", "zoo", "market"],
    ],
)
def test_a_stop_already_on_the_route_adds_none(net, stops):
    before = state(net)
    with pytest.raises(RouteError):
        net.add_stops("red", stops)
    assert state(net) == before


@pytest.mark.parametrize(
    "stops",
    [
        ["park", "park"],
        ["park", "zoo", "park"],
        ["zoo", "mill", "mill"],
    ],
)
def test_a_stop_listed_twice_adds_none(net, stops):
    before = state(net)
    with pytest.raises(RouteError):
        net.add_stops("red", stops)
    assert state(net) == before


def test_a_refused_call_can_be_retried_without_the_problem(net):
    with pytest.raises(RouteError):
        net.add_stops("red", ["park", "depot"])
    assert net.add_stops("red", ["park"]) == 1
    assert net.get_stops("red") == ["depot", "market", "park"]


@pytest.mark.parametrize("route", ["yellow", "green"])
def test_a_route_not_in_use_raises_key_error(net, route):
    net.remove_route("green")
    before = state(net)
    with pytest.raises(KeyError):
        net.add_stops(route, ["zoo"])
    assert state(net) == before


def test_added_stops_are_ordinary_stops(net):
    net.add_stops("red", ["park", "school"])
    net.add_stops("green", ["park"])
    with pytest.raises(RouteError):
        net.add_stop("red", "park")
    net.remove_stop("red", "market")
    assert net.retire_stop("park") == 2
    assert net.split_route("red", "school", "orange") == 1
    assert net.get_stops("red") == ["depot"]
    assert net.get_stops("orange") == ["school"]
    assert net.get_stops("green") == []


def test_a_route_made_by_split_can_be_extended(net):
    net.add_stops("red", ["park", "school"])
    net.split_route("red", "park", "orange")
    assert net.add_stops("orange", ["zoo", "depot"]) == 2
    assert net.get_stops("orange") == ["park", "school", "zoo", "depot"]
