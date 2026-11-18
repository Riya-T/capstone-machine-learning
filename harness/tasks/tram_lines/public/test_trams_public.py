"""Public checks for trams.py.

Usage (with trams.py importable, e.g. in the sandbox):
    python -m pytest public/test_trams_public.py
"""

import pytest
from trams import TramError, TramNetwork


@pytest.fixture
def network():
    n = TramNetwork()
    n.add_line("1")
    n.add_line("2")
    return n


def test_stops_and_lines_are_listed_in_the_order_added(network):
    network.add_stop("1", "Central")
    network.add_stop("1", "Park")
    network.add_stop("1", "Harbour")
    assert network.get_stops("1") == ["Central", "Park", "Harbour"]
    assert network.get_stops("2") == []
    assert network.get_lines() == ["1", "2"]


def test_a_line_has_each_stop_at_most_once(network):
    network.add_stop("1", "Central")
    with pytest.raises(TramError):
        network.add_stop("1", "Central")
    network.add_stop("2", "Central")
    assert network.get_stops("1") == ["Central"]
    assert network.get_lines_through("Central") == ["1", "2"]


def test_removing_a_stop_keeps_the_order_of_the_others(network):
    for stop in ["Central", "Park", "Harbour"]:
        network.add_stop("1", stop)
    network.remove_stop("1", "Park")
    assert network.get_stops("1") == ["Central", "Harbour"]


def test_close_stop_takes_the_stop_off_every_line(network):
    network.add_stop("1", "Central")
    network.add_stop("1", "Park")
    network.add_stop("2", "Park")
    assert network.close_stop("Park") == 2
    assert network.get_stops("1") == ["Central"]
    assert network.get_stops("2") == []
    assert network.get_lines() == ["1", "2"]


def test_merge_lines_adds_the_new_stops_and_removes_the_second_line(network):
    for stop in ["Central", "Park"]:
        network.add_stop("1", stop)
    for stop in ["Zoo", "Park", "Harbour"]:
        network.add_stop("2", stop)
    network.merge_lines("1", "2")
    assert network.get_stops("1") == ["Central", "Park", "Zoo", "Harbour"]
    assert network.get_lines() == ["1"]
    with pytest.raises(KeyError):
        network.get_stops("2")
