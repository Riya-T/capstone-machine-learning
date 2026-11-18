"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with network.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
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
    return n  # 10 recorded calls


def state(n):
    return [(r, list(n.get_stops(r))) for r in list(n.get_routes())]


# --- each call can be undone ------------------------------------------------


def test_undo_of_add_stop(net):
    before = state(net)
    net.add_stop("green", "zoo")
    net.undo()
    assert state(net) == before
    assert net.get_stops("green") == []


def test_undo_of_removing_the_first_stop_puts_it_back_first(net):
    before = state(net)
    net.remove_stop("red", "depot")
    net.undo()
    assert net.get_stops("red") == ["depot", "market", "park", "school"]
    assert state(net) == before


def test_undo_of_removing_a_middle_stop_puts_it_back_in_place(net):
    net.remove_stop("blue", "market")
    net.undo()
    assert net.get_stops("blue") == ["harbor", "market", "museum"]


def test_undo_of_remove_route_brings_it_back_with_its_stops(net):
    before = state(net)
    net.remove_route("red")
    net.undo()
    assert net.get_routes() == ["red", "blue", "green"]
    assert net.get_stops("red") == ["depot", "market", "park", "school"]
    assert state(net) == before


def test_undo_of_remove_route_keeps_its_place_in_the_list(net):
    net.remove_route("blue")
    net.add_stop("green", "zoo")
    net.undo()  # the zoo
    net.undo()  # the removal of blue
    assert net.get_routes() == ["red", "blue", "green"]
    assert net.get_stops("blue") == ["harbor", "market", "museum"]
    assert net.get_stops("green") == []


def test_a_route_brought_back_is_in_use_again(net):
    net.remove_route("blue")
    net.undo()
    with pytest.raises(RouteError):
        net.add_route("blue")
    net.add_stop("blue", "zoo")
    assert net.get_stops("blue") == ["harbor", "market", "museum", "zoo"]


def test_undo_of_add_route_removes_it_and_frees_the_name(net):
    net.add_route("orange")
    net.undo()
    assert net.get_routes() == ["red", "blue", "green"]
    with pytest.raises(KeyError):
        net.get_stops("orange")
    net.add_route("orange")
    assert net.get_routes() == ["red", "blue", "green", "orange"]


# --- calls that change several routes at once -------------------------------


def test_one_undo_takes_back_a_whole_retire_stop(net):
    net.add_stop("green", "market")
    net.add_stop("green", "zoo")
    before = state(net)
    assert net.retire_stop("market") == 3
    net.undo()
    assert state(net) == before
    assert net.get_stops("red") == ["depot", "market", "park", "school"]
    assert net.get_stops("blue") == ["harbor", "market", "museum"]
    assert net.get_stops("green") == ["market", "zoo"]


def test_undo_of_retire_stop_does_not_undo_the_call_before(net):
    net.add_stop("green", "zoo")
    net.retire_stop("market")
    net.undo()
    assert net.get_stops("green") == ["zoo"]
    assert "market" in net.get_stops("red")


def test_one_undo_takes_back_a_whole_split(net):
    before = state(net)
    assert net.split_route("red", "market", "orange") == 3
    net.undo()
    assert state(net) == before
    assert net.get_routes() == ["red", "blue", "green"]
    with pytest.raises(KeyError):
        net.get_stops("orange")


def test_undo_of_a_split_frees_the_new_name(net):
    net.split_route("blue", "harbor", "orange")
    net.undo()
    net.add_route("orange")
    assert net.get_stops("orange") == []
    assert net.get_stops("blue") == ["harbor", "market", "museum"]


def test_undo_through_a_name_that_was_removed_and_added_again(net):
    net.add_route("orange")
    net.add_stop("orange", "zoo")
    net.remove_route("orange")
    net.add_route("orange")  # a new, empty orange
    net.add_stop("orange", "mill")
    net.undo()  # the mill
    net.undo()  # the new orange
    assert net.get_routes() == ["red", "blue", "green"]
    net.undo()  # the removal: the old orange comes back with its zoo
    assert net.get_routes() == ["red", "blue", "green", "orange"]
    assert net.get_stops("orange") == ["zoo"]
    net.undo()  # the zoo
    net.undo()  # the first orange
    assert net.get_routes() == ["red", "blue", "green"]


def test_a_retire_stop_of_nothing_is_still_a_call(net):
    net.add_stop("green", "zoo")
    assert net.retire_stop("airport") == 0
    net.undo()  # the retire_stop, which changed nothing
    assert net.get_stops("green") == ["zoo"]
    net.undo()  # the zoo
    assert net.get_stops("green") == []


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    n = BusNetwork()
    calls = [
        lambda: n.add_route("red"),
        lambda: n.add_route("blue"),
        lambda: n.add_stop("red", "depot"),
        lambda: n.add_stop("red", "market"),
        lambda: n.add_stop("blue", "market"),
        lambda: n.add_stop("red", "park"),
        lambda: n.add_stop("blue", "harbor"),
        lambda: n.add_route("green"),
        lambda: n.add_stop("green", "park"),
        lambda: n.retire_stop("park"),
        lambda: n.split_route("red", "market", "orange"),
        lambda: n.remove_stop("blue", "market"),
        lambda: n.remove_route("red"),
        lambda: n.add_stop("orange", "zoo"),
        lambda: n.split_route("orange", "zoo", "red"),
    ]
    states = [state(n)]
    for call in calls:
        call()
        states.append(state(n))
    assert n.get_routes() == ["blue", "green", "orange", "red"]
    assert n.get_stops("orange") == ["market"]
    for expected in reversed(states[:-1]):
        n.undo()
        assert state(n) == expected
    with pytest.raises(RouteError):
        n.undo()
    assert n.get_routes() == []


def test_failed_calls_are_not_recorded(net):
    net.add_stop("green", "zoo")
    for call in (
        lambda: net.add_route("red"),
        lambda: net.remove_route("yellow"),
        lambda: net.add_stop("red", "park"),
        lambda: net.remove_stop("red", "harbor"),
        lambda: net.split_route("red", "harbor", "orange"),
        lambda: net.split_route("red", "park", "blue"),
    ):
        with pytest.raises((KeyError, RouteError)):
            call()
    net.undo()  # the zoo
    assert net.get_stops("green") == []
    assert net.get_stops("blue") == ["harbor", "market", "museum"]


def test_get_calls_are_not_recorded(net):
    net.add_stop("green", "zoo")
    net.get_stops("green")
    net.get_routes()
    net.undo()
    assert net.get_stops("green") == []
    assert net.get_stops("blue") == ["harbor", "market", "museum"]


def test_there_is_no_redo():
    n = BusNetwork()
    n.add_route("red")
    n.add_stop("red", "depot")
    n.undo()
    n.undo()
    assert n.get_routes() == []
    with pytest.raises(RouteError):
        n.undo()


def test_new_calls_after_an_undo_are_undone_first(net):
    net.add_stop("green", "zoo")
    net.undo()
    net.add_stop("green", "mill")
    net.undo()
    assert net.get_stops("green") == []
    net.undo()  # the museum from the fixture
    assert net.get_stops("blue") == ["harbor", "market"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    n = BusNetwork()
    with pytest.raises(RouteError):
        n.undo()
    n.add_route("red")
    n.undo()
    with pytest.raises(RouteError):
        n.undo()
    assert n.get_routes() == []
    n.add_route("red")
    n.add_stop("red", "depot")
    assert n.get_stops("red") == ["depot"]


def test_the_whole_fixture_can_be_undone(net):
    for _ in range(10):
        net.undo()
    assert net.get_routes() == []
    with pytest.raises(RouteError):
        net.undo()


def test_undo_restores_stops_that_a_later_call_checks(net):
    net.retire_stop("market")
    net.undo()
    with pytest.raises(RouteError):
        net.add_stop("blue", "market")
    assert net.split_route("blue", "market", "orange") == 2
