"""Hidden tests for the c_connections change (where to change trams).
Never shown to the writer or the editor.

Usage (with trams.py importable, e.g. in the sandbox):
    python -m pytest changes/c_connections/private/test_connections_new.py
"""

import pytest
from trams import TramNetwork


@pytest.fixture
def network():
    # Lines are added in an order that is not alphabetical.
    n = TramNetwork()
    for name in ["4", "1", "7", "2"]:
        n.add_line(name)
    for stop in ["Central", "Park", "Museum", "Harbour"]:
        n.add_stop("4", stop)
    for stop in ["Station", "Park", "Central"]:
        n.add_stop("1", stop)
    for stop in ["Zoo", "Beach"]:
        n.add_stop("7", stop)
    for stop in ["Beach", "Harbour"]:
        n.add_stop("2", stop)
    return n


def state(n):
    return [(line, n.get_stops(line)) for line in n.get_lines()]


# --- get_connections ----------------------------------------------------------


def test_connections_follow_the_order_of_the_lines(network):
    assert network.get_connections("4") == ["1", "2"]
    assert network.get_connections("1") == ["4"]
    assert network.get_connections("7") == ["2"]
    assert network.get_connections("2") == ["4", "7"]


def test_a_line_sharing_several_stops_is_listed_once(network):
    assert network.get_connections("1") == ["4"]
    network.add_stop("1", "Museum")
    assert network.get_connections("1") == ["4"]


def test_a_line_is_never_its_own_connection(network):
    for line in network.get_lines():
        assert line not in network.get_connections(line)


def test_a_line_without_shared_stops_has_no_connections(network):
    network.add_line("9")
    assert network.get_connections("9") == []
    network.add_stop("9", "Airport")
    assert network.get_connections("9") == []


def test_a_removed_stop_no_longer_connects(network):
    network.remove_stop("2", "Harbour")
    assert network.get_connections("4") == ["1"]
    assert network.get_connections("2") == ["7"]


def test_a_closed_stop_no_longer_connects(network):
    network.close_stop("Park")
    assert network.get_connections("1") == ["4"]  # still Central
    network.close_stop("Central")
    assert network.get_connections("1") == []
    assert network.get_connections("4") == ["2"]


def test_connections_after_a_merge(network):
    network.merge_lines("1", "7")
    assert network.get_lines() == ["4", "1", "2"]
    assert network.get_connections("1") == ["4", "2"]
    assert network.get_connections("2") == ["4", "1"]


# --- get_shared_stops -----------------------------------------------------------


def test_shared_stops_are_in_the_order_of_the_first_line(network):
    assert network.get_shared_stops("4", "1") == ["Central", "Park"]
    assert network.get_shared_stops("1", "4") == ["Park", "Central"]


def test_lines_that_share_no_stop_have_no_shared_stops(network):
    assert network.get_shared_stops("1", "7") == []
    network.add_line("9")
    assert network.get_shared_stops("9", "4") == []
    assert network.get_shared_stops("4", "9") == []


def test_shared_stops_follow_later_changes(network):
    network.add_stop("1", "Harbour")
    assert network.get_shared_stops("4", "1") == ["Central", "Park", "Harbour"]
    network.remove_stop("4", "Park")
    assert network.get_shared_stops("4", "1") == ["Central", "Harbour"]


def test_the_same_line_twice_is_rejected(network):
    with pytest.raises(ValueError):
        network.get_shared_stops("4", "4")


# --- errors and side effects ----------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda n: n.get_connections("9"),
        lambda n: n.get_shared_stops("9", "4"),
        lambda n: n.get_shared_stops("4", "9"),
    ],
)
def test_lines_not_in_use_raise_key_error(network, call):
    with pytest.raises(KeyError):
        call(network)


def test_a_merged_line_is_not_in_use_for_the_queries(network):
    network.merge_lines("4", "1")
    with pytest.raises(KeyError):
        network.get_connections("1")
    with pytest.raises(KeyError):
        network.get_shared_stops("4", "1")


def test_the_queries_change_nothing(network):
    before = state(network)
    network.get_connections("4")
    network.get_shared_stops("4", "1")
    network.get_shared_stops("7", "2")
    assert state(network) == before
    assert network.get_lines_through("Park") == ["4", "1"]
