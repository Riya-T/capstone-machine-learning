"""Public checks for the c_connections change (where to change trams).
Shown to the editor, never to the writer.

Usage (with trams.py importable, e.g. in the sandbox):
    python -m pytest changes/c_connections/public/test_connections_public.py
"""

import pytest
from trams import TramNetwork


@pytest.fixture
def network():
    n = TramNetwork()
    for name in ["1", "2", "3"]:
        n.add_line(name)
    for stop in ["Central", "Park", "Harbour"]:
        n.add_stop("1", stop)
    for stop in ["Station", "Park"]:
        n.add_stop("2", stop)
    n.add_stop("3", "Zoo")
    return n


def test_connections_are_the_other_lines_sharing_a_stop(network):
    assert network.get_connections("1") == ["2"]
    assert network.get_connections("2") == ["1"]
    assert network.get_connections("3") == []


def test_shared_stops_follow_the_first_line(network):
    network.add_stop("2", "Central")
    assert network.get_shared_stops("1", "2") == ["Central", "Park"]
    assert network.get_shared_stops("2", "1") == ["Park", "Central"]
    assert network.get_shared_stops("1", "3") == []
