"""Hidden tests for the initial tram_lines spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with trams.py importable, e.g. in the sandbox):
    python -m pytest private/test_trams_initial.py
"""

import pytest
from trams import TramError, TramNetwork


@pytest.fixture
def network():
    n = TramNetwork()
    for name in ["4", "1", "7"]:
        n.add_line(name)
    for stop in ["Central", "Park", "Museum", "Harbour"]:
        n.add_stop("4", stop)
    for stop in ["Station", "Park", "Central"]:
        n.add_stop("1", stop)
    return n


def state(n):
    """Every line in order with its stops, to check that a failed call
    changed nothing."""
    return [(line, n.get_stops(line)) for line in n.get_lines()]


# --- lines --------------------------------------------------------------------


def test_a_new_line_has_no_stops():
    n = TramNetwork()
    n.add_line("1")
    assert n.get_stops("1") == []
    assert n.get_lines() == ["1"]


def test_lines_are_listed_in_the_order_added(network):
    assert network.get_lines() == ["4", "1", "7"]


def test_adding_a_line_name_in_use_is_rejected(network):
    before = state(network)
    with pytest.raises(TramError):
        network.add_line("1")
    assert state(network) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda n: n.add_stop("9", "Zoo"),
        lambda n: n.remove_stop("9", "Park"),
        lambda n: n.merge_lines("9", "4"),
        lambda n: n.merge_lines("4", "9"),
        lambda n: n.get_stops("9"),
    ],
)
def test_lines_that_were_never_added_raise_key_error(network, call):
    before = state(network)
    with pytest.raises(KeyError):
        call(network)
    assert state(network) == before


def test_networks_do_not_share_lines():
    first, second = TramNetwork(), TramNetwork()
    first.add_line("1")
    first.add_stop("1", "Central")
    assert second.get_lines() == []
    second.add_line("1")
    assert second.get_stops("1") == []


# --- stops --------------------------------------------------------------------


def test_stops_are_kept_in_the_order_added(network):
    assert network.get_stops("4") == ["Central", "Park", "Museum", "Harbour"]
    assert network.get_stops("1") == ["Station", "Park", "Central"]
    assert network.get_stops("7") == []


def test_a_stop_the_line_already_has_is_rejected(network):
    before = state(network)
    with pytest.raises(TramError):
        network.add_stop("4", "Museum")
    assert state(network) == before


def test_the_same_stop_can_be_on_several_lines(network):
    network.add_stop("7", "Park")
    assert network.get_lines_through("Park") == ["4", "1", "7"]


@pytest.mark.parametrize(
    "stop, left",
    [
        ("Central", ["Park", "Museum", "Harbour"]),
        ("Museum", ["Central", "Park", "Harbour"]),
        ("Harbour", ["Central", "Park", "Museum"]),
    ],
)
def test_remove_stop_keeps_the_order_of_the_others(network, stop, left):
    network.remove_stop("4", stop)
    assert network.get_stops("4") == left
    assert network.get_stops("1") == ["Station", "Park", "Central"]


def test_removing_a_stop_the_line_does_not_have_is_rejected(network):
    before = state(network)
    with pytest.raises(TramError):
        network.remove_stop("4", "Station")
    with pytest.raises(TramError):
        network.remove_stop("7", "Park")
    assert state(network) == before


def test_a_removed_stop_can_be_added_again_at_the_end(network):
    network.remove_stop("4", "Park")
    network.add_stop("4", "Park")
    assert network.get_stops("4") == ["Central", "Museum", "Harbour", "Park"]


# --- closing a stop -------------------------------------------------------------


def test_close_stop_takes_it_off_every_line_that_has_it(network):
    assert network.close_stop("Park") == 2
    assert network.get_stops("4") == ["Central", "Museum", "Harbour"]
    assert network.get_stops("1") == ["Station", "Central"]
    assert network.get_lines_through("Park") == []


def test_close_stop_of_a_stop_on_one_line(network):
    assert network.close_stop("Museum") == 1
    assert network.get_stops("4") == ["Central", "Park", "Harbour"]
    assert network.get_stops("1") == ["Station", "Park", "Central"]


def test_a_line_left_without_stops_stays_in_use(network):
    network.add_stop("7", "Zoo")
    assert network.close_stop("Zoo") == 1
    assert network.get_lines() == ["4", "1", "7"]
    assert network.get_stops("7") == []


def test_closing_a_stop_no_line_has_is_rejected(network):
    before = state(network)
    with pytest.raises(TramError):
        network.close_stop("Zoo")
    assert state(network) == before


# --- lines through a stop -------------------------------------------------------


def test_lines_through_a_stop_follow_the_order_of_the_lines(network):
    network.add_stop("7", "Central")
    assert network.get_lines_through("Central") == ["4", "1", "7"]
    assert network.get_lines_through("Station") == ["1"]
    assert network.get_lines_through("Zoo") == []


# --- merging lines --------------------------------------------------------------


def test_merge_lines_skips_the_stops_the_first_line_has(network):
    network.merge_lines("4", "1")
    assert network.get_stops("4") == ["Central", "Park", "Museum", "Harbour", "Station"]
    assert network.get_lines() == ["4", "7"]


def test_merge_lines_keeps_the_second_lines_order(network):
    for stop in ["Zoo", "Airport", "Beach"]:
        network.add_stop("7", stop)
    network.merge_lines("1", "7")
    assert network.get_stops("1") == ["Station", "Park", "Central", "Zoo", "Airport", "Beach"]
    assert network.get_lines() == ["4", "1"]
    assert network.get_stops("4") == ["Central", "Park", "Museum", "Harbour"]


def test_merging_into_a_line_without_stops(network):
    network.merge_lines("7", "1")
    assert network.get_stops("7") == ["Station", "Park", "Central"]
    assert network.get_lines() == ["4", "7"]
    assert network.get_lines_through("Station") == ["7"]


@pytest.mark.parametrize(
    "call",
    [
        lambda n: n.add_stop("1", "Zoo"),
        lambda n: n.remove_stop("1", "Park"),
        lambda n: n.merge_lines("1", "7"),
        lambda n: n.merge_lines("7", "1"),
        lambda n: n.get_stops("1"),
    ],
)
def test_a_merged_line_is_not_in_use(network, call):
    network.merge_lines("4", "1")
    before = state(network)
    with pytest.raises(KeyError):
        call(network)
    assert state(network) == before


def test_merging_a_line_into_itself_is_rejected(network):
    before = state(network)
    with pytest.raises(ValueError):
        network.merge_lines("4", "4")
    assert state(network) == before
