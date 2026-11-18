"""Hidden tests for the c_lock change (locked routes). Never shown to the
writer or the editor.

Usage (with network.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/private/test_lock_new.py
"""

import pytest
from network import BusNetwork, RouteError, RouteLocked


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
    return [(r, list(n.get_stops(r))) for r in list(n.get_routes())]


# --- the flag ---------------------------------------------------------------


def test_routes_start_unlocked(net):
    assert [net.is_locked(r) for r in net.get_routes()] == [False, False, False]


def test_lock_and_unlock(net):
    net.lock_route("blue")
    assert net.is_locked("blue") is True
    assert net.is_locked("red") is False
    net.unlock_route("blue")
    assert net.is_locked("blue") is False


def test_locking_twice_or_unlocking_an_unlocked_route_does_nothing(net):
    net.lock_route("red")
    net.lock_route("red")
    assert net.is_locked("red") is True
    net.unlock_route("red")
    assert net.is_locked("red") is False
    net.unlock_route("green")
    assert net.is_locked("green") is False


def test_locking_changes_no_stops(net):
    before = state(net)
    net.lock_route("red")
    net.lock_route("blue")
    assert state(net) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda n: n.lock_route("yellow"),
        lambda n: n.unlock_route("yellow"),
        lambda n: n.is_locked("yellow"),
        lambda n: n.lock_route("green"),
        lambda n: n.unlock_route("green"),
        lambda n: n.is_locked("green"),
    ],
)
def test_routes_not_in_use_raise_key_error(net, call):
    net.remove_route("green")
    with pytest.raises(KeyError):
        call(net)


def test_the_route_made_by_a_split_is_not_locked(net):
    net.lock_route("blue")
    net.split_route("red", "park", "orange")
    assert net.is_locked("orange") is False
    net.add_stop("orange", "zoo")
    assert net.get_stops("orange") == ["park", "school", "zoo"]


def test_a_route_added_again_under_a_removed_name_is_not_locked(net):
    net.lock_route("green")
    net.unlock_route("green")
    net.remove_route("green")
    net.add_route("green")
    assert net.is_locked("green") is False


# --- what a locked route refuses --------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda n: n.add_stop("red", "zoo"),
        lambda n: n.remove_stop("red", "park"),
        lambda n: n.remove_route("red"),
        lambda n: n.split_route("red", "market", "orange"),
        lambda n: n.retire_stop("school"),
    ],
    ids=["add_stop", "remove_stop", "remove_route", "split_route", "retire_stop"],
)
def test_a_locked_route_refuses_every_change(net, call):
    net.lock_route("red")
    before = state(net)
    with pytest.raises(RouteLocked):
        call(net)
    assert state(net) == before
    assert net.get_routes() == ["red", "blue", "green"]


def test_a_refused_split_adds_no_route(net):
    net.lock_route("red")
    with pytest.raises(RouteLocked):
        net.split_route("red", "park", "orange")
    with pytest.raises(KeyError):
        net.get_stops("orange")
    net.add_route("orange")
    assert net.get_routes() == ["red", "blue", "green", "orange"]


def test_retire_stop_with_one_locked_route_removes_it_from_none(net):
    net.add_stop("green", "market")
    net.lock_route("blue")
    before = state(net)
    with pytest.raises(RouteLocked):
        net.retire_stop("market")
    assert state(net) == before
    assert net.get_stops("red") == ["depot", "market", "park", "school"]
    assert net.get_stops("green") == ["market"]


def test_retire_stop_works_when_no_locked_route_has_the_stop(net):
    net.add_stop("green", "park")
    net.lock_route("blue")
    assert net.retire_stop("park") == 2
    assert net.get_stops("red") == ["depot", "market", "school"]
    assert net.get_stops("green") == []
    assert net.get_stops("blue") == ["harbor", "market", "museum"]


def test_a_lock_only_applies_to_its_own_route(net):
    net.lock_route("red")
    net.add_stop("blue", "zoo")
    net.remove_stop("blue", "harbor")
    assert net.split_route("blue", "zoo", "orange") == 1
    net.remove_route("green")
    assert net.get_routes() == ["red", "blue", "orange"]
    assert net.get_stops("blue") == ["market", "museum"]


def test_getters_work_on_a_locked_route(net):
    net.lock_route("red")
    assert net.get_stops("red") == ["depot", "market", "park", "school"]
    assert net.get_routes() == ["red", "blue", "green"]


def test_a_refused_call_can_be_retried_once_unlocked(net):
    net.lock_route("blue")
    with pytest.raises(RouteLocked):
        net.retire_stop("market")
    net.unlock_route("blue")
    assert net.retire_stop("market") == 2
    net.lock_route("red")
    with pytest.raises(RouteLocked):
        net.remove_route("red")
    net.unlock_route("red")
    net.remove_route("red")
    assert net.get_routes() == ["blue", "green"]


def test_route_locked_is_a_route_error():
    assert issubclass(RouteLocked, RouteError)
