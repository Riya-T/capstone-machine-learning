"""Hidden tests for the initial bus_routes spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with network.py importable, e.g. in the sandbox):
    python -m pytest private/test_network_initial.py
"""

import pytest
from network import BusNetwork, RouteError


@pytest.fixture
def net():
    n = BusNetwork()
    for name in ["red", "blue", "green"]:
        n.add_route(name)
    for stop in ["depot", "market", "park", "school"]:
        n.add_stop("red", stop)
    for stop in ["harbor", "market", "museum"]:
        n.add_stop("blue", stop)
    return n


def state(n):
    """Every route in order with a copy of its stops, to check that a failed
    call changed nothing."""
    return [(r, list(n.get_stops(r))) for r in list(n.get_routes())]


# --- routes -----------------------------------------------------------------


def test_a_new_route_has_no_stops():
    n = BusNetwork()
    n.add_route("red")
    assert n.get_stops("red") == []
    assert n.get_routes() == ["red"]


def test_routes_are_listed_in_the_order_added():
    n = BusNetwork()
    for name in ["west", "north", "east"]:
        n.add_route(name)
    assert n.get_routes() == ["west", "north", "east"]


def test_adding_a_route_name_in_use_is_rejected(net):
    before = state(net)
    with pytest.raises(RouteError):
        net.add_route("blue")
    assert state(net) == before


def test_remove_route_removes_it_with_its_stops(net):
    net.remove_route("blue")
    assert net.get_routes() == ["red", "green"]
    assert net.get_stops("red") == ["depot", "market", "park", "school"]
    with pytest.raises(KeyError):
        net.get_stops("blue")


def test_a_removed_name_can_be_added_again_as_a_new_route_at_the_end(net):
    net.remove_route("red")
    net.add_route("red")
    assert net.get_routes() == ["blue", "green", "red"]
    assert net.get_stops("red") == []
    net.add_stop("red", "school")
    assert net.get_stops("red") == ["school"]


@pytest.mark.parametrize(
    "call",
    [
        lambda n: n.remove_route("yellow"),
        lambda n: n.add_stop("yellow", "depot"),
        lambda n: n.remove_stop("yellow", "depot"),
        lambda n: n.split_route("yellow", "depot", "orange"),
        lambda n: n.get_stops("yellow"),
    ],
    ids=["remove_route", "add_stop", "remove_stop", "split_route", "get_stops"],
)
def test_routes_never_added_raise_key_error(net, call):
    before = state(net)
    with pytest.raises(KeyError):
        call(net)
    assert state(net) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda n: n.remove_route("green"),
        lambda n: n.add_stop("green", "depot"),
        lambda n: n.remove_stop("green", "depot"),
        lambda n: n.split_route("green", "depot", "orange"),
        lambda n: n.get_stops("green"),
    ],
    ids=["remove_route", "add_stop", "remove_stop", "split_route", "get_stops"],
)
def test_a_removed_route_is_not_in_use(net, call):
    net.add_stop("green", "depot")
    net.remove_route("green")
    before = state(net)
    with pytest.raises(KeyError):
        call(net)
    assert state(net) == before


# --- adding and removing stops ----------------------------------------------


def test_stops_are_listed_in_the_order_added(net):
    for stop in ["zoo", "airport", "mill"]:
        net.add_stop("green", stop)
    assert net.get_stops("green") == ["zoo", "airport", "mill"]


def test_a_stop_can_be_on_several_routes(net):
    net.add_stop("green", "market")
    assert net.get_stops("green") == ["market"]
    assert "market" in net.get_stops("red")
    assert "market" in net.get_stops("blue")


def test_adding_a_stop_the_route_already_has_is_rejected(net):
    before = state(net)
    with pytest.raises(RouteError):
        net.add_stop("red", "depot")
    with pytest.raises(RouteError):
        net.add_stop("blue", "museum")
    assert state(net) == before


def test_remove_stop_keeps_the_order_of_the_others(net):
    net.remove_stop("red", "market")
    assert net.get_stops("red") == ["depot", "park", "school"]
    assert net.get_stops("blue") == ["harbor", "market", "museum"]


def test_removing_a_stop_not_on_the_route_is_rejected(net):
    before = state(net)
    with pytest.raises(RouteError):
        net.remove_stop("red", "harbor")  # on another route
    with pytest.raises(RouteError):
        net.remove_stop("red", "zoo")  # on no route
    with pytest.raises(RouteError):
        net.remove_stop("green", "depot")
    assert state(net) == before


def test_a_removed_stop_can_be_added_again_at_the_end(net):
    net.remove_stop("red", "depot")
    net.add_stop("red", "depot")
    assert net.get_stops("red") == ["market", "park", "school", "depot"]


# --- retire_stop ----------------------------------------------------------------


def test_retire_stop_removes_it_from_every_route_that_has_it(net):
    net.add_stop("green", "zoo")
    net.add_stop("green", "market")
    assert net.retire_stop("market") == 3
    assert net.get_stops("red") == ["depot", "park", "school"]
    assert net.get_stops("blue") == ["harbor", "museum"]
    assert net.get_stops("green") == ["zoo"]


def test_retire_stop_on_one_route(net):
    assert net.retire_stop("school") == 1
    assert net.get_stops("red") == ["depot", "market", "park"]
    assert net.get_stops("blue") == ["harbor", "market", "museum"]


def test_retiring_a_stop_on_no_route_changes_nothing(net):
    before = state(net)
    assert net.retire_stop("zoo") == 0
    assert state(net) == before
    net.retire_stop("museum")
    assert net.retire_stop("museum") == 0
    assert net.get_stops("blue") == ["harbor", "market"]


# --- split_route ----------------------------------------------------------------


def test_split_route_moves_the_stop_and_every_stop_after_it(net):
    assert net.split_route("red", "market", "orange") == 3
    assert net.get_routes() == ["red", "blue", "green", "orange"]
    assert net.get_stops("red") == ["depot"]
    assert net.get_stops("orange") == ["market", "park", "school"]
    assert net.get_stops("blue") == ["harbor", "market", "museum"]


def test_split_at_the_last_stop_moves_one_stop(net):
    assert net.split_route("blue", "museum", "orange") == 1
    assert net.get_stops("blue") == ["harbor", "market"]
    assert net.get_stops("orange") == ["museum"]


def test_split_at_the_first_stop_moves_every_stop(net):
    assert net.split_route("red", "depot", "orange") == 4
    assert net.get_stops("red") == []
    assert net.get_stops("orange") == ["depot", "market", "park", "school"]
    assert net.get_routes() == ["red", "blue", "green", "orange"]


def test_the_new_route_works_like_any_other(net):
    net.split_route("red", "park", "orange")
    net.add_stop("orange", "zoo")
    net.remove_stop("orange", "school")
    assert net.get_stops("orange") == ["park", "zoo"]
    assert net.get_stops("red") == ["depot", "market"]
    net.remove_route("orange")
    assert net.get_routes() == ["red", "blue", "green"]


def test_splitting_at_a_stop_not_on_the_route_is_rejected(net):
    before = state(net)
    with pytest.raises(RouteError):
        net.split_route("red", "harbor", "orange")
    with pytest.raises(RouteError):
        net.split_route("green", "depot", "orange")
    assert state(net) == before


def test_splitting_into_a_name_in_use_is_rejected(net):
    before = state(net)
    with pytest.raises(RouteError):
        net.split_route("red", "park", "blue")
    with pytest.raises(RouteError):
        net.split_route("red", "park", "red")
    assert state(net) == before


def test_splitting_into_a_removed_name_works(net):
    net.remove_route("green")
    assert net.split_route("blue", "market", "green") == 2
    assert net.get_routes() == ["red", "blue", "green"]
    assert net.get_stops("green") == ["market", "museum"]


# --- general ----------------------------------------------------------------


def test_networks_do_not_share_routes():
    first, second = BusNetwork(), BusNetwork()
    first.add_route("red")
    first.add_stop("red", "depot")
    assert second.get_routes() == []
    second.add_route("red")
    assert second.get_stops("red") == []
